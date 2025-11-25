from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import User

class InstitutionalEmailBackend(BaseBackend):
    """
    Autenticación usando email institucional en lugar de username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('institutional_email')
        
        if username is None or password is None:
            return None
        
        try:
            # Buscar usuario por email institucional
            user = User.objects.get(institutional_email=username)
        except User.DoesNotExist:
            return None
        
        # Verificar contraseña
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def user_can_authenticate(self, user):
        """
        Rechazar usuarios con is_active=False. Los backends personalizados pueden
        anular este método si tienen sus propias reglas de activación de usuarios.
        """
        return getattr(user, 'is_active', None)
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None