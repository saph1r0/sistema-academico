"""
Mixins y decoradores para autenticación y permisos del panel administrativo
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from functools import wraps
import logging

logger = logging.getLogger('admin_panel')


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para verificar permisos de administrador
    Requiere que el usuario esté autenticado y tenga rol 'admin'
    """
    
    def test_func(self):
        """
        Verifica si el usuario tiene permisos de administrador
        """
        user = self.request.user
        
        # Verificar autenticación
        if not user.is_authenticated:
            return False
        
        # Verificar rol de administrador usando el método del modelo
        if hasattr(user, 'is_admin') and callable(user.is_admin):
            return user.is_admin()
        
        # Fallback para compatibilidad con otros sistemas
        return (
            hasattr(user, 'rol') and 
            user.rol == 'admin' and 
            getattr(user, 'activo', True) and
            user.is_active
        )
    
    def handle_no_permission(self):
        """
        Maneja el caso cuando el usuario no tiene permisos
        """
        user = self.request.user
        
        if not user.is_authenticated:
            messages.warning(
                self.request, 
                'Debe iniciar sesión para acceder al panel administrativo.'
            )
            return redirect('login')
        
        # Log del intento de acceso no autorizado
        logger.warning(
            f"Acceso denegado al panel admin para usuario {user.email} "
            f"con rol {getattr(user, 'rol', 'desconocido')}"
        )
        
        messages.error(
            self.request, 
            'No tienes permisos para acceder al panel administrativo. '
            'Contacta al administrador del sistema si crees que esto es un error.'
        )
        
        # Redirigir según el rol del usuario
        if hasattr(user, 'rol'):
            if user.rol == 'secretaria':
                return redirect('secretaria:dashboard')
            elif user.rol == 'docente':
                return redirect('docente:dashboard')
            elif user.rol == 'estudiante':
                return redirect('estudiante:dashboard')
        
        return redirect('login')
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch para logging adicional
        """
        if self.test_func():
            logger.info(
                f"Acceso autorizado al panel admin para usuario {request.user.email}"
            )
        
        return super().dispatch(request, *args, **kwargs)


class SecretariaOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para verificar permisos de secretaria o administrador
    """
    
    def test_func(self):
        """
        Verifica si el usuario es secretaria o administrador
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        # Usar métodos del modelo si están disponibles
        if hasattr(user, 'is_admin') and hasattr(user, 'is_secretaria'):
            return user.is_admin() or user.is_secretaria()
        
        # Fallback
        return (
            hasattr(user, 'rol') and 
            user.rol in ['admin', 'secretaria'] and 
            getattr(user, 'activo', True) and
            user.is_active
        )
    
    def handle_no_permission(self):
        """
        Maneja el caso cuando el usuario no tiene permisos
        """
        if not self.request.user.is_authenticated:
            return redirect('login')
        
        messages.error(
            self.request, 
            'Necesitas permisos de secretaria o administrador para acceder a esta función.'
        )
        return redirect('login')


def admin_required(view_func=None, *, redirect_url='login'):
    """
    Decorador para vistas basadas en funciones que requieren permisos de admin
    
    Usage:
        @admin_required
        def my_view(request):
            ...
        
        @admin_required(redirect_url='custom_login')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debe iniciar sesión para continuar.')
                return redirect(redirect_url)
            
            # Verificar permisos de admin
            if hasattr(request.user, 'is_admin') and callable(request.user.is_admin):
                if not request.user.is_admin():
                    logger.warning(
                        f"Acceso denegado a vista admin para usuario {request.user.email}"
                    )
                    messages.error(
                        request, 
                        'No tienes permisos de administrador para acceder a esta función.'
                    )
                    return redirect(redirect_url)
            else:
                # Fallback
                if not (hasattr(request.user, 'rol') and 
                       request.user.rol == 'admin' and 
                       getattr(request.user, 'activo', True)):
                    messages.error(
                        request, 
                        'No tienes permisos de administrador para acceder a esta función.'
                    )
                    return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def secretaria_or_admin_required(view_func=None, *, redirect_url='login'):
    """
    Decorador para vistas que requieren permisos de secretaria o admin
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(redirect_url)
            
            user = request.user
            has_permission = False
            
            if hasattr(user, 'is_admin') and hasattr(user, 'is_secretaria'):
                has_permission = user.is_admin() or user.is_secretaria()
            else:
                # Fallback
                has_permission = (
                    hasattr(user, 'rol') and 
                    user.rol in ['admin', 'secretaria'] and 
                    getattr(user, 'activo', True)
                )
            
            if not has_permission:
                messages.error(
                    request, 
                    'Necesitas permisos de secretaria o administrador.'
                )
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def ajax_admin_required(view_func):
    """
    Decorador para vistas AJAX que requieren permisos de admin
    Retorna JSON en lugar de redireccionar
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'No autenticado',
                'message': 'Debe iniciar sesión para continuar.'
            }, status=401)
        
        # Verificar permisos de admin
        if hasattr(request.user, 'is_admin') and callable(request.user.is_admin):
            if not request.user.is_admin():
                return JsonResponse({
                    'success': False,
                    'error': 'Permisos insuficientes',
                    'message': 'No tienes permisos de administrador.'
                }, status=403)
        else:
            # Fallback
            if not (hasattr(request.user, 'rol') and 
                   request.user.rol == 'admin' and 
                   getattr(request.user, 'activo', True)):
                return JsonResponse({
                    'success': False,
                    'error': 'Permisos insuficientes',
                    'message': 'No tienes permisos de administrador.'
                }, status=403)
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class PermissionDeniedError(Exception):
    """Excepción personalizada para permisos denegados"""
    pass


def check_admin_permission(user):
    """
    Función utilitaria para verificar permisos de admin
    Lanza PermissionDeniedError si no tiene permisos
    """
    if not user.is_authenticated:
        raise PermissionDeniedError("Usuario no autenticado")
    
    if hasattr(user, 'is_admin') and callable(user.is_admin):
        if not user.is_admin():
            raise PermissionDeniedError("Usuario no tiene permisos de administrador")
    else:
        # Fallback
        if not (hasattr(user, 'rol') and 
               user.rol == 'admin' and 
               getattr(user, 'activo', True)):
            raise PermissionDeniedError("Usuario no tiene permisos de administrador")
    
    return True


def check_secretaria_or_admin_permission(user):
    """
    Función utilitaria para verificar permisos de secretaria o admin
    """
    if not user.is_authenticated:
        raise PermissionDeniedError("Usuario no autenticado")
    
    if hasattr(user, 'is_admin') and hasattr(user, 'is_secretaria'):
        if not (user.is_admin() or user.is_secretaria()):
            raise PermissionDeniedError("Usuario no tiene permisos suficientes")
    else:
        # Fallback
        if not (hasattr(user, 'rol') and 
               user.rol in ['admin', 'secretaria'] and 
               getattr(user, 'activo', True)):
            raise PermissionDeniedError("Usuario no tiene permisos suficientes")
    
    return True