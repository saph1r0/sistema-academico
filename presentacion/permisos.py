# presentacion/permisos.py

from rest_framework import permissions

SECRETARIA_ROL_NAME = 'secretaria'
ADMIN_ROL_NAME = 'admin' 


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
    