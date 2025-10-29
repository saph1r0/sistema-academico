"""
Middleware para gestión de sesiones por roles
"""
import time
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.utils import timezone
from presentacion.permisos import get_user_role


class RoleBasedSessionMiddleware:
    """Middleware para gestión de sesiones basada en roles"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar antes de la vista
        if request.user.is_authenticated:
            self._check_session_timeout(request)
            self._update_session_activity(request)
        
        response = self.get_response(request)
        
        # Procesar después de la vista
        return response

    def _check_session_timeout(self, request):
        """Verifica si la sesión ha expirado según el rol del usuario"""
        user_role = get_user_role(request.user)
        
        if not user_role:
            return
        
        # Obtener timeout específico del rol
        role_timeouts = getattr(settings, 'ROLE_SESSION_TIMEOUTS', {})
        timeout = role_timeouts.get(user_role, settings.SESSION_COOKIE_AGE)
        
        # Verificar última actividad
        last_activity = request.session.get('last_activity')
        if last_activity:
            time_since_activity = time.time() - last_activity
            
            if time_since_activity > timeout:
                # Sesión expirada
                logout(request)
                messages.warning(
                    request, 
                    f'Tu sesión ha expirado por inactividad ({timeout // 60} minutos). '
                    'Por favor, inicia sesión nuevamente.'
                )
                return redirect('login:login')

    def _update_session_activity(self, request):
        """Actualiza la marca de tiempo de última actividad"""
        request.session['last_activity'] = time.time()
        
        # Guardar información del rol para referencia rápida
        user_role = get_user_role(request.user)
        if user_role:
            request.session['user_role'] = user_role


class SecurityHeadersMiddleware:
    """Middleware para agregar headers de seguridad"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy básico
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            )
        
        return response


class AuditMiddleware:
    """Middleware para auditoría de acciones de usuarios"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Registrar información de la request
        if request.user.is_authenticated:
            self._log_user_activity(request)
        
        response = self.get_response(request)
        
        # Registrar información de la response si es necesario
        if request.user.is_authenticated and response.status_code >= 400:
            self._log_error_activity(request, response)
        
        return response

    def _log_user_activity(self, request):
        """Registra la actividad del usuario"""
        import logging
        logger = logging.getLogger('admin_panel')
        
        user_role = get_user_role(request.user)
        
        # Solo registrar acciones importantes (POST, PUT, DELETE)
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            logger.info(
                f"User Activity - User: {request.user.email}, "
                f"Role: {user_role}, Method: {request.method}, "
                f"Path: {request.path}, IP: {self._get_client_ip(request)}"
            )

    def _log_error_activity(self, request, response):
        """Registra errores de acceso"""
        import logging
        logger = logging.getLogger('admin_panel')
        
        user_role = get_user_role(request.user)
        
        logger.warning(
            f"Access Error - User: {request.user.email}, "
            f"Role: {user_role}, Status: {response.status_code}, "
            f"Path: {request.path}, IP: {self._get_client_ip(request)}"
        )

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RoleAccessControlMiddleware:
    """Middleware para control de acceso por roles"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Definir rutas protegidas por rol
        self.role_patterns = {
            'admin': ['/admin/'],
            'teacher': ['/profesor/'],
            'student': ['/estudiante/'],
            'secretary': ['/secretario/'],
        }

    def __call__(self, request):
        # Verificar acceso antes de procesar la vista
        if request.user.is_authenticated:
            access_denied = self._check_role_access(request)
            if access_denied:
                return access_denied
        
        response = self.get_response(request)
        return response

    def _check_role_access(self, request):
        """Verifica si el usuario tiene acceso a la ruta según su rol"""
        user_role = get_user_role(request.user)
        
        if not user_role:
            return None
        
        path = request.path
        
        # Verificar si está intentando acceder a una ruta de otro rol
        for role, patterns in self.role_patterns.items():
            if role != user_role:
                for pattern in patterns:
                    if path.startswith(pattern):
                        messages.error(
                            request,
                            f'No tienes permisos para acceder a esta sección. '
                            f'Tu rol actual es: {user_role}'
                        )
                        # Redirigir al dashboard apropiado
                        from presentacion.permisos import get_user_dashboard_url
                        dashboard_url = get_user_dashboard_url(request.user)
                        return redirect(dashboard_url)
        
        return None