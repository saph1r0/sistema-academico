# presentacion/permisos.py

from rest_framework import permissions

SECRETARIA_ROL_NAME = 'secretaria'
ADMIN_ROL_NAME = 'admin' 


class IsSecretariaOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios con rol 
    'secretaria' o 'admin'.
    """
    message = 'Debe ser un usuario con rol Secretaria o Administrador para acceder a esta función.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_groups = request.user.groups.values_list('name', flat=True)
        
        is_secretaria = SECRETARIA_ROL_NAME in user_groups
        is_admin = ADMIN_ROL_NAME in user_groups
        
        return is_secretaria or is_admin
    