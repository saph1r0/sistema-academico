"""
Vistas para el módulo de estudiantes
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils import timezone

from .mixins import EstudianteRequiredMixin
from servicios.servicioMatricula import ServicioMatricula
from servicios.servicioAsistencia import ServicioAsistencia
from servicios.servicioAvance import ServicioAvance
from servicios.servicioReservas import ServicioReservas
from servicios.servicioNotas import ServicioNotas


class EstudianteDashboardView(EstudianteRequiredMixin, TemplateView):
    """Dashboard principal del estudiante"""
    template_name = 'estudiante/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el estudiante asociado al usuario
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            # Si no hay relación student, usar el ID del usuario
            estudiante_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora hasta que los servicios estén implementados
        context.update({
            'horario_actual': [],  # ServicioMatricula.obtener_horario_estudiante(estudiante_id),
            'porcentaje_avance': 0.0,  # ServicioAvance.calcular_avance_estudiante(estudiante_id),
            'porcentaje_asistencia': 0.0,  # ServicioAsistencia.calcular_asistencia_estudiante(estudiante_id),
            'cursos_matriculados': []  # ServicioMatricula.obtener_cursos_estudiante(estudiante_id)
        })
        return context


class EstudianteLaboratoriosView(EstudianteRequiredMixin, TemplateView):
    """Gestión de matrícula en laboratorios"""
    template_name = 'estudiante/laboratorios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el estudiante asociado al usuario
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora
        context.update({
            'laboratorios_disponibles': [],  # ServicioReservas.obtener_laboratorios_disponibles(estudiante_id),
            'matriculas_actuales': [],  # ServicioMatricula.obtener_matriculas_laboratorio(estudiante_id),
            'plazo_matricula_activo': True  # ServicioMatricula.verificar_plazo_matricula()
        })
        return context

    def post(self, request, *args, **kwargs):
        """Matricular o desmatricular en laboratorio"""
        accion = request.POST.get('accion')
        laboratorio_id = request.POST.get('laboratorio_id')
        
        try:
            # Obtener el estudiante asociado al usuario
            try:
                estudiante = request.user.student
                estudiante_id = estudiante.id
            except AttributeError:
                estudiante_id = request.user.id
            
            if accion == 'matricular':
                # ServicioMatricula.matricular_laboratorio(estudiante_id, laboratorio_id)
                messages.success(request, 'Te has matriculado exitosamente en el laboratorio.')
            elif accion == 'desmatricular':
                # ServicioMatricula.desmatricular_laboratorio(estudiante_id, laboratorio_id)
                messages.success(request, 'Te has desmatriculado exitosamente del laboratorio.')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')
        
        return redirect('estudiante:laboratorios')


class EstudianteNotasView(EstudianteRequiredMixin, TemplateView):
    """Vista de notas del estudiante"""
    template_name = 'estudiante/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el estudiante asociado al usuario
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora
        context.update({
            'notas_por_curso': [],  # ServicioNotas.obtener_notas_estudiante(estudiante_id),
            'promedio_general': 0.0  # ServicioNotas.calcular_promedio_estudiante(estudiante_id)
        })
        return context


class EstudianteHorarioView(EstudianteRequiredMixin, TemplateView):
    """Vista del horario del estudiante"""
    template_name = 'estudiante/horarios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el estudiante asociado al usuario
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora
        context.update({
            'horario_semanal': [],  # ServicioMatricula.obtener_horario_semanal_estudiante(estudiante_id),
            'cursos_matriculados': []  # ServicioMatricula.obtener_cursos_estudiante(estudiante_id)
        })
        return context