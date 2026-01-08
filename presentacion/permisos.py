# presentacion/permisos.py

from rest_framework import permissions
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# Nombres de roles del sistema
ADMIN_ROL_NAME = 'admin'
SECRETARIA_ROL_NAME = 'secretary'
DOCENTE_ROL_NAME = 'teacher'
ESTUDIANTE_ROL_NAME = 'student'

# Mapeo de roles para compatibilidad
ROLE_MAPPING = {
    'admin': ADMIN_ROL_NAME,
    'secretaria': SECRETARIA_ROL_NAME,
    'docente': DOCENTE_ROL_NAME,
    'teacher': DOCENTE_ROL_NAME,
    'profesor': DOCENTE_ROL_NAME,
    'estudiante': ESTUDIANTE_ROL_NAME,
    'student': ESTUDIANTE_ROL_NAME,
    'secretary': SECRETARIA_ROL_NAME,
} 


class IsSecretariaOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios con rol 
    'secretaria' o 'admin'.
    Actualizado para usar el nuevo sistema de autenticación.
    """
    message = 'Debe ser un usuario con rol Secretaria o Administrador para acceder a esta función.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Usar los nuevos métodos del modelo de usuario si están disponibles
        if hasattr(request.user, 'is_admin') and hasattr(request.user, 'is_secretaria'):
            return request.user.is_admin() or request.user.is_secretaria()
        
        # Fallback para compatibilidad con el sistema anterior
        if hasattr(request.user, 'rol'):
            return request.user.rol in [ADMIN_ROL_NAME, SECRETARIA_ROL_NAME]
        
        # Fallback para sistema de grupos de Django
        user_groups = request.user.groups.values_list('name', flat=True)
        is_secretaria = SECRETARIA_ROL_NAME in user_groups
        is_admin = ADMIN_ROL_NAME in user_groups
        
        return is_secretaria or is_admin


class IsAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios con rol 'admin'.
    """
    message = 'Debe ser un usuario con rol Administrador para acceder a esta función.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Usar el nuevo método del modelo de usuario si está disponible
        if hasattr(request.user, 'is_admin'):
            return request.user.is_admin()
        
        # Fallback para compatibilidad
        if hasattr(request.user, 'rol'):
            return request.user.rol == ADMIN_ROL_NAME and getattr(request.user, 'activo', True)
        
        # Fallback para sistema de grupos de Django
        user_groups = request.user.groups.values_list('name', flat=True)
        return ADMIN_ROL_NAME in user_groups


class IsSecretaria(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios con rol 'secretaria'.
    """
    message = 'Debe ser un usuario con rol Secretaria para acceder a esta función.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Usar el nuevo método del modelo de usuario si está disponible
        if hasattr(request.user, 'is_secretaria'):
            return request.user.is_secretaria()
        
        # Fallback para compatibilidad
        if hasattr(request.user, 'rol'):
            return request.user.rol == SECRETARIA_ROL_NAME and getattr(request.user, 'activo', True)
        
        # Fallback para sistema de grupos de Django
        user_groups = request.user.groups.values_list('name', flat=True)
        return SECRETARIA_ROL_NAME in user_groups


class IsDocente(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios con rol 'docente'.
    """
    message = 'Debe ser un usuario con rol Docente para acceder a esta función.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Usar el nuevo método del modelo de usuario si está disponible
        if hasattr(request.user, 'is_docente'):
            return request.user.is_docente()
        
        # Fallback para compatibilidad
        if hasattr(request.user, 'rol'):
            return request.user.rol == 'docente' and getattr(request.user, 'activo', True)
        
        # Fallback para sistema de grupos de Django
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'docente' in user_groups


class IsEstudiante(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios con rol 'estudiante'.
    """
    message = 'Debe ser un usuario con rol Estudiante para acceder a esta función.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Usar el nuevo método del modelo de usuario si está disponible
        if hasattr(request.user, 'is_estudiante'):
            return request.user.is_estudiante()
        
        # Fallback para compatibilidad
        if hasattr(request.user, 'rol'):
            return request.user.rol == 'estudiante' and getattr(request.user, 'activo', True)
        
        # Fallback para sistema de grupos de Django
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'estudiante' in user_groups


# Funciones auxiliares para verificación de roles
def get_user_role(user):
    """Obtiene el rol del usuario de forma consistente"""
    if not user or not user.is_authenticated:
        return None
    
    # Verificar si el usuario tiene el atributo role (nuevo modelo User)
    if hasattr(user, 'role'):
        return ROLE_MAPPING.get(user.role, user.role)
    
    # Verificar si el usuario tiene el atributo rol (UsuarioModel legacy)
    if hasattr(user, 'rol'):
        return ROLE_MAPPING.get(user.rol, user.rol)
    
    # Verificar grupos de Django como fallback
    user_groups = user.groups.values_list('name', flat=True)
    for group in user_groups:
        mapped_role = ROLE_MAPPING.get(group)
        if mapped_role:
            return mapped_role
    
    return None


def is_admin(user):
    """Verifica si el usuario es administrador"""
    return get_user_role(user) == ADMIN_ROL_NAME


def is_teacher(user):
    """Verifica si el usuario es profesor"""
    return get_user_role(user) == DOCENTE_ROL_NAME


def is_student(user):
    """Verifica si el usuario es estudiante"""
    return get_user_role(user) == ESTUDIANTE_ROL_NAME


def is_secretary(user):
    """Verifica si el usuario es secretario"""
    return get_user_role(user) == SECRETARIA_ROL_NAME


def user_has_role(user, required_role):
    """Verifica si el usuario tiene un rol específico"""
    user_role = get_user_role(user)
    return user_role == required_role


def user_has_any_role(user, required_roles):
    """Verifica si el usuario tiene alguno de los roles especificados"""
    user_role = get_user_role(user)
    return user_role in required_roles


# Decoradores para vistas basadas en funciones
def role_required(required_role):
    """Decorador que requiere un rol específico"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not user_has_role(request.user, required_role):
                messages.error(
                    request, 
                    f'No tienes permisos para acceder a esta sección. Se requiere rol: {required_role}'
                )
                return redirect('login')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorador que requiere rol de administrador"""
    return role_required(ADMIN_ROL_NAME)(view_func)


def teacher_required(view_func):
    """Decorador que requiere rol de profesor"""
    return role_required(DOCENTE_ROL_NAME)(view_func)


def student_required(view_func):
    """Decorador que requiere rol de estudiante"""
    return role_required(ESTUDIANTE_ROL_NAME)(view_func)


def secretary_required(view_func):
    """Decorador que requiere rol de secretario"""
    return role_required(SECRETARIA_ROL_NAME)(view_func)


# Mixins para vistas basadas en clases (actualizados)
class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin base para verificación de roles"""
    required_role = None
    
    def test_func(self):
        if not self.required_role:
            return False
        return user_has_role(self.request.user, self.required_role)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        
        messages.error(
            self.request, 
            f'No tienes permisos para acceder a esta sección. Se requiere rol: {self.required_role}'
        )
        return redirect('login')


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de administrador"""
    required_role = ADMIN_ROL_NAME


class TeacherRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de profesor"""
    required_role = DOCENTE_ROL_NAME


class StudentRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de estudiante"""
    required_role = ESTUDIANTE_ROL_NAME


class SecretaryRequiredMixin(RoleRequiredMixin):
    """Mixin que requiere rol de secretario"""
    required_role = SECRETARIA_ROL_NAME


# Funciones para filtrado de datos por rol
def filter_data_by_role(user, queryset, model_type=None):
    """Filtra datos según el rol del usuario"""
    user_role = get_user_role(user)
    
    if user_role == ADMIN_ROL_NAME:
        # Los administradores ven todo
        return queryset
    
    elif user_role == DOCENTE_ROL_NAME:
        # Los profesores solo ven sus datos
        if hasattr(user, 'profesor') or hasattr(user, 'teacher'):
            teacher_id = getattr(user, 'profesor', getattr(user, 'teacher', None))
            if teacher_id:
                return queryset.filter(teacher_id=teacher_id.id)
        return queryset.none()
    
    elif user_role == ESTUDIANTE_ROL_NAME:
        # Los estudiantes solo ven sus datos
        if hasattr(user, 'estudiante') or hasattr(user, 'student'):
            student_id = getattr(user, 'estudiante', getattr(user, 'student', None))
            if student_id:
                return queryset.filter(student_id=student_id.id)
        return queryset.none()
    
    elif user_role == SECRETARIA_ROL_NAME:
        # Los secretarios ven datos académicos generales
        return queryset
    
    # Por defecto, no mostrar nada
    return queryset.none()


def get_user_dashboard_url(user):
    """Obtiene la URL del dashboard según el rol del usuario"""
    user_role = get_user_role(user)
    
    dashboard_urls = {
        ADMIN_ROL_NAME: 'administrador:usuarios',
        DOCENTE_ROL_NAME: 'profesor:dashboard',
        ESTUDIANTE_ROL_NAME: 'estudiante:dashboard',
        SECRETARIA_ROL_NAME: 'secretario:dashboard',
    }
    
    return dashboard_urls.get(user_role, 'login')


def get_user_permissions(user):
    """Obtiene los permisos del usuario según su rol"""
    user_role = get_user_role(user)
    
    permissions = {
        ADMIN_ROL_NAME: [
            'view_all_users', 'manage_users', 'view_all_reports', 
            'manage_system_config', 'view_system_metrics'
        ],
        DOCENTE_ROL_NAME: [
            'view_own_courses', 'manage_grades', 'manage_attendance',
            'create_reservations', 'manage_syllabus'
        ],
        ESTUDIANTE_ROL_NAME: [
            'view_own_grades', 'view_own_schedule', 'manage_lab_enrollment',
            'view_own_attendance'
        ],
        SECRETARIA_ROL_NAME: [
            'manage_lab_enrollments', 'generate_academic_reports',
            'view_academic_statistics'
        ]
    }
    
    return permissions.get(user_role, [])


def obtener_dashboard_por_rol(role):
    """Función de compatibilidad para obtener URL del dashboard por rol"""
    dashboard_urls = {
        'admin': '/administrador/',
        'teacher': '/profesor/',
        'student': '/estudiante/',
        'secretary': '/secretario/',
    }
    
    return dashboard_urls.get(role, '/')
    