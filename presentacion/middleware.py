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
from servicios.servicioAsistenciaDocente import ServicioAsistenciaDocente


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


class TeacherAttendanceMiddleware:
    """Middleware para registro automático de asistencia docente"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.servicio_asistencia = ServicioAsistenciaDocente()
        # Importar el calculador de progreso
        from servicios.servicioCalculadorProgreso import ProgressCalculator
        self.progress_calculator = ProgressCalculator()

    def __call__(self, request):
        # Procesar antes de la vista
        if request.user.is_authenticated and hasattr(request.user, 'teacher'):
            self._handle_teacher_login(request)
        
        response = self.get_response(request)
        
        # Procesar después de la vista si es logout
        if self._is_logout_request(request) and request.user.is_authenticated and hasattr(request.user, 'teacher'):
            self._handle_teacher_logout(request)
        
        return response

    def _handle_teacher_login(self, request):
        """Maneja el login automático del docente"""
        try:
            teacher = request.user.teacher
            
            # Verificar si ya se registró el login hoy
            login_registered_today = request.session.get('teacher_login_registered_today')
            current_date = timezone.now().date().isoformat()
            
            if login_registered_today != current_date:
                # Obtener información de la request
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                # Registrar login automático
                attendance = self.servicio_asistencia.registrar_login_automatico(
                    teacher_id=str(teacher.id),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                if attendance:
                    # Marcar que ya se registró hoy
                    request.session['teacher_login_registered_today'] = current_date
                    request.session['teacher_attendance_id'] = str(attendance.id)
                    
                    # Actualizar progreso de cursos inmediatamente después del login
                    self._update_course_progress_on_login(teacher)
                    
        except Exception as e:
            import logging
            logger = logging.getLogger('admin_panel')
            logger.error(f"Error en registro automático de login docente: {str(e)}")

    def _handle_teacher_logout(self, request):
        """Maneja el logout automático del docente"""
        try:
            teacher = request.user.teacher
            
            # Registrar logout automático
            logout_success = self.servicio_asistencia.registrar_logout_automatico(str(teacher.id))
            
            # Si el logout fue exitoso y se registró una sesión válida, actualizar progreso
            if logout_success:
                self._update_course_progress_on_logout(teacher)
            
            # Limpiar variables de sesión
            request.session.pop('teacher_login_registered_today', None)
            request.session.pop('teacher_attendance_id', None)
            
        except Exception as e:
            import logging
            logger = logging.getLogger('admin_panel')
            logger.error(f"Error en registro automático de logout docente: {str(e)}")

    def _update_course_progress_on_login(self, teacher):
        """Actualiza el progreso de los cursos cuando el docente hace login"""
        try:
            # Obtener todos los cursos del docente
            from repositorio.postgres_repository.models import CourseGroup
            course_groups = CourseGroup.objects.filter(teacher=teacher)
            
            for course_group in course_groups:
                # Calcular progreso para cada curso
                result = self.progress_calculator.calculate_course_progress(str(course_group.id))
                
                if result.get('success'):
                    import logging
                    logger = logging.getLogger('admin_panel')
                    logger.info(
                        f"Progreso actualizado por login - {course_group.course.name}: "
                        f"{result.get('progress_percentage', 0):.1f}%"
                    )
                    
        except Exception as e:
            import logging
            logger = logging.getLogger('admin_panel')
            logger.error(f"Error actualizando progreso en login: {str(e)}")

    def _update_course_progress_on_logout(self, teacher):
        """Actualiza el progreso de los cursos cuando el docente hace logout"""
        try:
            # Recalcular progreso usando el método específico del calculador
            results = self.progress_calculator.recalculate_progress_for_teacher_attendance(
                str(teacher.id), 
                timezone.now()
            )
            
            if results:
                import logging
                logger = logging.getLogger('admin_panel')
                successful_updates = sum(1 for r in results if r.get('success', False))
                logger.info(
                    f"Progreso recalculado por logout - {teacher.user.get_full_name()}: "
                    f"{successful_updates}/{len(results)} cursos actualizados"
                )
                
        except Exception as e:
            import logging
            logger = logging.getLogger('admin_panel')
            logger.error(f"Error actualizando progreso en logout: {str(e)}")

    def _is_logout_request(self, request):
        """Verifica si la request es de logout"""
        return (
            request.path.endswith('/logout/') or 
            request.path.endswith('/login/logout/') or
            'logout' in request.path
        )

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip