"""
Mixins para control de acceso de estudiantes
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from presentacion.permisos import StudentRequiredMixin as BaseStudentRequiredMixin


class EstudianteRequiredMixin(BaseStudentRequiredMixin):
    """Mixin que requiere que el usuario sea un estudiante"""
    pass  # Hereda toda la funcionalidad del mixin centralizado