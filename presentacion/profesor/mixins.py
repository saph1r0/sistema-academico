"""
Mixins para control de acceso de profesores
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from presentacion.permisos import TeacherRequiredMixin as BaseTeacherRequiredMixin


class ProfesorRequiredMixin(BaseTeacherRequiredMixin):
    """Mixin que requiere que el usuario sea un profesor"""
    pass  # Hereda toda la funcionalidad del mixin centralizado