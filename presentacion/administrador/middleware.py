"""
Middleware para el panel administrativo
Proporciona funcionalidades adicionales de autenticación, logging y seguridad
"""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import logging
import re

logger = logging.getLogger('admin_panel')


class AdminPanelMiddleware(MiddlewareMixin):
    """
    Middleware específico para el panel administrativo
    
    Funcionalidades:
    - Actualiza último acceso para usuarios admin
    - Valida sesiones de admin
    - Logging de acciones administrativas
    - Protección adicional para rutas admin
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Patrones de URLs del panel admin
        self.admin_url_patterns = [
            re.compile(r'^/admin/'),
            re.compile(r'^/administrador/'),
        ]
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Procesa la request antes de que llegue a la vista
        """
        # Verificar si es una URL del panel admin
        if self._is_admin_url(request.path):
            return self._handle_admin_request(request)
        
        return None
    
    def process_response(self, request, response):
        """
        Procesa la response después de la vista
        """
        # Actualizar último acceso para usuarios admin
        if (self._is_admin_url(request.path) and 
            request.user.is_authenticated and 
            hasattr(request.user, 'is_admin') and 
            request.user.is_admin()):
            
            try:
                request.user.actualizar_ultimo_acceso()
            except Exception as e:
                logger.error(f"Error actualizando último acceso: {e}")
        
        return response
    
    def _is_admin_url(self, path):
        """
        Verifica si la URL pertenece al panel administrativo
        """
        return any(pattern.match(path) for pattern in self.admin_url_patterns)
    
    def _handle_admin_request(self, request):
        """
        Maneja requests al panel administrativo
        """
        # Log de acceso
        logger.info(
            f"Acceso a panel admin: {request.path} "
            f"desde IP {self._get_client_ip(request)} "
            f"por usuario {getattr(request.user, 'email', 'anónimo')}"
        )
        
        # Verificar autenticación
        if not request.user.is_authenticated:
            messages.warning(
                request, 
                'Debe iniciar sesión para acceder al panel administrativo.'
            )
            return redirect('login')
        
        # Verificar permisos de admin
        if not self._has_admin_permission(request.user):
            logger.warning(
                f"Intento de acceso no autorizado al panel admin por "
                f"usuario {request.user.email} con rol {getattr(request.user, 'rol', 'desconocido')}"
            )
            
            messages.error(
                request, 
                'No tienes permisos para acceder al panel administrativo.'
            )
            return redirect('login')
        
        # Verificar si el usuario está activo
        if not getattr(request.user, 'activo', True) or not request.user.is_active:
            logger.warning(
                f"Usuario inactivo intentó acceder al panel admin: {request.user.email}"
            )
            
            messages.error(
                request, 
                'Tu cuenta está desactivada. Contacta al administrador del sistema.'
            )
            return redirect('login')
        
        return None
    
    def _has_admin_permission(self, user):
        """
        Verifica si el usuario tiene permisos de administrador
        """
        if hasattr(user, 'is_admin') and callable(user.is_admin):
            return user.is_admin()
        
        # Fallback
        return (
            hasattr(user, 'rol') and 
            user.rol == 'admin' and 
            getattr(user, 'activo', True)
        )
    
    def _get_client_ip(self, request):
        """
        Obtiene la IP del cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminSessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad adicional para sesiones de admin
    
    Funcionalidades:
    - Timeout de sesión más corto para admins
    - Validación de IP para sesiones admin
    - Logging de cambios de sesión
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Timeout de sesión para admins (en segundos)
        self.admin_session_timeout = getattr(settings, 'ADMIN_SESSION_TIMEOUT', 3600)  # 1 hora
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Procesa la request para validar sesión de admin
        """
        if (request.user.is_authenticated and 
            hasattr(request.user, 'is_admin') and 
            request.user.is_admin()):
            
            return self._validate_admin_session(request)
        
        return None
    
    def _validate_admin_session(self, request):
        """
        Valida la sesión de un usuario administrador
        """
        session = request.session
        current_time = timezone.now().timestamp()
        
        # Verificar timeout de sesión
        last_activity = session.get('admin_last_activity')
        if last_activity:
            if current_time - last_activity > self.admin_session_timeout:
                logger.info(
                    f"Sesión de admin expirada para usuario {request.user.email}"
                )
                
                # Limpiar sesión
                session.flush()
                messages.warning(
                    request, 
                    'Tu sesión ha expirado por seguridad. Por favor, inicia sesión nuevamente.'
                )
                return redirect('login')
        
        # Actualizar última actividad
        session['admin_last_activity'] = current_time
        
        # Validar IP (opcional, para mayor seguridad)
        if getattr(settings, 'ADMIN_VALIDATE_IP', False):
            return self._validate_admin_ip(request)
        
        return None
    
    def _validate_admin_ip(self, request):
        """
        Valida que la IP del admin no haya cambiado durante la sesión
        """
        session = request.session
        current_ip = self._get_client_ip(request)
        session_ip = session.get('admin_ip')
        
        if session_ip is None:
            # Primera vez, guardar IP
            session['admin_ip'] = current_ip
        elif session_ip != current_ip:
            # IP cambió, invalidar sesión por seguridad
            logger.warning(
                f"Cambio de IP detectado para admin {request.user.email}: "
                f"{session_ip} -> {current_ip}"
            )
            
            session.flush()
            messages.error(
                request, 
                'Se detectó un cambio en tu dirección IP. '
                'Por seguridad, debes iniciar sesión nuevamente.'
            )
            return redirect('login')
        
        return None
    
    def _get_client_ip(self, request):
        """
        Obtiene la IP del cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminAuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoría de acciones administrativas
    
    Registra todas las acciones POST/PUT/DELETE realizadas por administradores
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Métodos HTTP que se auditan
        self.audit_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Registra acciones administrativas
        """
        if (request.method in self.audit_methods and 
            request.user.is_authenticated and 
            hasattr(request.user, 'is_admin') and 
            request.user.is_admin()):
            
            self._log_admin_action(request)
        
        return None
    
    def _log_admin_action(self, request):
        """
        Registra una acción administrativa en el log
        """
        try:
            # Información básica de la acción
            action_data = {
                'user': request.user.email,
                'method': request.method,
                'path': request.path,
                'ip': self._get_client_ip(request),
                'timestamp': timezone.now().isoformat(),
            }
            
            # Agregar datos del POST si existen (sin contraseñas)
            if request.POST:
                post_data = dict(request.POST)
                # Filtrar campos sensibles
                sensitive_fields = ['password', 'contrasena', 'token', 'csrf']
                filtered_data = {
                    k: v for k, v in post_data.items() 
                    if not any(field in k.lower() for field in sensitive_fields)
                }
                action_data['post_data'] = filtered_data
            
            logger.info(f"Acción administrativa: {action_data}")
            
        except Exception as e:
            logger.error(f"Error registrando acción administrativa: {e}")
    
    def _get_client_ip(self, request):
        """
        Obtiene la IP del cliente
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip