"""
Mixins para control de acceso de secretarios
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from presentacion.permisos import SecretaryRequiredMixin as BaseSecretaryRequiredMixin


class SecretarioRequiredMixin(BaseSecretaryRequiredMixin):
    """Mixin que requiere que el usuario sea un secretario"""
    pass  # Hereda toda la funcionalidad del mixin centralizado