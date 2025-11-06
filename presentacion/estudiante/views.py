"""
Vistas para el módulo de estudiantes
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse

from .mixins import EstudianteRequiredMixin
from servicios.servicioMatricula import ServicioMatricula, servicio_matricula
from servicios.servicioAsistencia import ServicioAsistencia
from servicios.servicioAvance import ServicioAvance
from servicios.servicioReservas import ServicioReservas
from servicios.servicioNotas import ServicioNotas, servicio_notas
from servicios.servicioEstudianteData import ServicioEstudianteData


class EstudianteDashboardView(EstudianteRequiredMixin, TemplateView):
    """Dashboard principal del estudiante"""
    template_name = 'estudiante/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Inicializar servicio de datos del estudiante
        servicio_estudiante = ServicioEstudianteData()
        
        # Obtener el estudiante asociado al usuario
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            # Si no hay relación student, buscar por usuario
            estudiante = servicio_estudiante.obtener_estudiante_por_usuario(self.request.user.id)
            if estudiante:
                estudiante_id = estudiante.id
            else:
                # Si no existe estudiante, mostrar mensaje de error
                messages.error(self.request, 'No se encontró perfil de estudiante asociado a tu usuario.')
                estudiante_id = None
        
        # Obtener datos reales del estudiante
        if estudiante_id:
            try:
                cursos_matriculados = servicio_estudiante.obtener_cursos_estudiante(estudiante_id)
                estadisticas = servicio_estudiante.obtener_estadisticas_estudiante(estudiante_id)
            except Exception as e:
                # En caso de error, usar datos por defecto y mostrar mensaje
                messages.warning(self.request, 'Hubo un problema al cargar algunos datos. Intenta recargar la página.')
                cursos_matriculados = []
                estadisticas = {
                    'total_cursos': 0,
                    'asistencia_promedio': 0.0,
                    'progreso_promedio': 0.0,
                    'total_laboratorios': 0
                }
        else:
            cursos_matriculados = []
            estadisticas = {
                'total_cursos': 0,
                'asistencia_promedio': 0.0,
                'progreso_promedio': 0.0,
                'total_laboratorios': 0
            }
        
        context.update({
            'horario_actual': [],  # Por implementar después
            'porcentaje_avance': estadisticas.get('progreso_promedio', 0.0),
            'porcentaje_asistencia': estadisticas.get('asistencia_promedio', 0.0),
            'cursos_matriculados': cursos_matriculados,
            'total_cursos': estadisticas.get('total_cursos', 0),
            'total_laboratorios': estadisticas.get('total_laboratorios', 0)
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
            estudiante_id = str(estudiante.id)
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de estudiante.')
            estudiante_id = None
        
        if estudiante_id:
            # Obtener laboratorios disponibles
            laboratorios_data = servicio_matricula.obtener_laboratorios_disponibles(estudiante_id)
            
            # Obtener matrículas actuales
            matriculas_data = servicio_matricula.obtener_matriculas_estudiante(estudiante_id)
            
            context.update({
                'laboratorios_disponibles': laboratorios_data.get('laboratorios_por_curso', {}),
                'matriculas_actuales': matriculas_data.get('matriculas_activas', []),
                'plazo_matricula_activo': True,  # TODO: Implementar verificación de fechas
                'total_cursos_con_lab': laboratorios_data.get('total_cursos_con_lab', 0)
            })
        else:
            context.update({
                'laboratorios_disponibles': {},
                'matriculas_actuales': [],
                'plazo_matricula_activo': False,
                'total_cursos_con_lab': 0
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Matricular o desmatricular en laboratorio"""
        accion = request.POST.get('accion')
        laboratorio_id = request.POST.get('laboratorio_id')
        
        try:
            # Obtener el estudiante asociado al usuario
            estudiante = request.user.student
            estudiante_id = str(estudiante.id)
            
            if accion == 'matricular':
                resultado = servicio_matricula.matricular_laboratorio(estudiante_id, laboratorio_id)
                if resultado['success']:
                    messages.success(request, resultado['message'])
                else:
                    messages.error(request, resultado['error'])
                    
            elif accion == 'desmatricular':
                resultado = servicio_matricula.desmatricular_laboratorio(estudiante_id, laboratorio_id)
                if resultado['success']:
                    messages.success(request, resultado['message'])
                else:
                    messages.error(request, resultado['error'])
                    
        except AttributeError:
            messages.error(request, 'No se encontró perfil de estudiante.')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')
        
        return redirect('estudiante:laboratorios')


class EstudianteNotasView(EstudianteRequiredMixin, TemplateView):
    """Vista de notas del estudiante por fases usando PhaseGrade model"""
    template_name = 'estudiante/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Importar la vista actualizada desde views_notas
        from .views_notas import StudentGradesView
        
        # Usar la nueva implementación
        grades_view = StudentGradesView()
        grades_view.request = self.request
        grades_context = grades_view.get_context_data(**kwargs)
        
        # Mapear los nombres de variables para compatibilidad
        context.update({
            'notas_por_curso': grades_context.get('courses_data', []),
            'promedio_general': grades_context.get('general_average', 0.0),
            'total_cursos': grades_context.get('total_courses', 0),
            'student_name': grades_context.get('student', {}).user.get_full_name() if grades_context.get('student') else '',
            'student_code': grades_context.get('student', {}).student_code if grades_context.get('student') else '',
            # Nuevas variables para la plantilla actualizada
            'courses_data': grades_context.get('courses_data', []),
            'general_average': grades_context.get('general_average', 0.0),
            'total_courses': grades_context.get('total_courses', 0),
            'courses_with_grades': grades_context.get('courses_with_grades', 0),
            'active_period': grades_context.get('active_period'),
            'passed_courses': grades_context.get('passed_courses', 0),
            'failed_courses': grades_context.get('failed_courses', 0),
            'pending_courses': grades_context.get('pending_courses', 0)
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


class EstudianteCursoDetalleView(EstudianteRequiredMixin, TemplateView):
    """Vista de detalle de un curso específico"""
    template_name = 'estudiante/curso_detalle.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el ID del curso desde la URL
        course_id = kwargs.get('course_id')
        
        # Inicializar servicio de datos del estudiante
        servicio_estudiante = ServicioEstudianteData()
        
        # Obtener el estudiante asociado al usuario
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante = servicio_estudiante.obtener_estudiante_por_usuario(self.request.user.id)
            if estudiante:
                estudiante_id = estudiante.id
            else:
                messages.error(self.request, 'No se encontró perfil de estudiante asociado a tu usuario.')
                estudiante_id = None
        
        # Obtener detalle del curso
        if estudiante_id and course_id:
            detalle_curso = servicio_estudiante.obtener_detalle_curso(course_id, estudiante_id)
            if not detalle_curso:
                messages.error(self.request, 'No tienes acceso a este curso o el curso no existe.')
        else:
            detalle_curso = {}
        
        context.update({
            'curso': detalle_curso,
            'course_id': course_id
        })
        return context