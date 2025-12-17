"""
Vistas para el módulo de estudiantes
"""

import random
import datetime
from datetime import datetime, time
from django.db.models import Prefetch
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import time
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import EstudianteRequiredMixin
from servicios.servicioMatriculaLaboratorio import ServicioMatriculaLaboratorio, servicio_matricula_laboratorio
from servicios.servicioAsistencia import ServicioAsistencia
from servicios.servicioAvance import ServicioAvance
from servicios.servicioReservas import servicio_reservas
from servicios.servicioNotas import ServicioNotas, servicio_notas
from servicios.servicioHorario import ServicioHorario
from servicios.servicioEstudianteData import ServicioEstudianteData
from servicios.servicioMatriculaLaboratorio import servicio_matricula_laboratorio


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from repositorio.postgres_repository.models import Enrollment
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from repositorio.postgres_repository.models import Enrollment
from repositorio.postgres_repository.models import (
    User, 
    Student, 
    AcademicPeriod, 
    Enrollment, 
    Horario,
    LaboratoryEnrollment
)

logger = logging.getLogger(__name__)

def parse_time(value):
    """Convierte '14:00:00' o datetime en objeto time correctamente"""
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    try:
        # caso '14:00:00'
        return datetime.strptime(value, "%H:%M:%S").time()
    except Exception:
        try:
            # caso '14:00'
            return datetime.strptime(value, "%H:%M").time()
        except Exception:
            return time(0, 0)


def parse_hora(h):
    if isinstance(h, time):
        return h
    try:
        return datetime.strptime(h, "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.strptime(h, "%H:%M").time()
        except ValueError:
            return time(0, 0)


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
        horario_actual = []

        try:
            servicio_horario = ServicioHorario()
            data_horario = servicio_horario.obtener_horario_estudiante(estudiante_id)

            eventos = data_horario.get("events", [])

            # Obtener día actual en formato que usa tu BD
            hoy = datetime.now().strftime("%A").lower()   # monday / tuesday / ...

            # Filtrar clases del día
            horario_actual = [
                e for e in eventos
                if e.get("dia") == hoy
            ]

        except Exception as e:
            logger.error(f"Error obteniendo horario del dashboard: {e}")
            horario_actual = []
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

        # 1) Obtener estudiante logueado
        try:
            student = self.request.user.student
        except AttributeError:
            # Si algo raro pasa
            student = None

        if not student:
            context.update({
                "plazo_matricula_activo": False,
                "laboratorios_disponibles": [],
                "matriculas_actuales": [],
            })
            return context

        # 2) Usar el servicio NUEVO de laboratorios
        data = servicio_matricula_laboratorio.obtener_laboratorios_disponibles(student.id)

        laboratorios_disponibles = data.get("laboratorios", [])
        en_periodo = data.get("en_periodo_matricula", False)

        # 3) Mis laboratorios actuales (matrículas reales en la BD)
        matriculas_qs = LaboratoryEnrollment.objects.filter(
            student=student,
            status='active'
        ).select_related(
            'laboratory__course_group__course',
            'laboratory__teacher__user'
        )

        mis_labs = []
        for m in matriculas_qs:
            lab = m.laboratory
            cg = lab.course_group
            mis_labs.append({
                "curso_nombre": cg.course.name,
                "curso_codigo": cg.course.code,
                "grupo": cg.group_code,
                "laboratorio_codigo": lab.lab_code,
                "laboratorio_id": str(lab.id),
                "aula": lab.lab_room or "Por asignar",
                "profesor_nombre": lab.teacher.user.get_full_name() if lab.teacher else "Por asignar",
                "fecha_matricula": m.enrollment_date,
            })

        # 4) Enviar todo al template
        context.update({
            "plazo_matricula_activo": en_periodo,
            "laboratorios_disponibles": laboratorios_disponibles,
            "matriculas_actuales": mis_labs,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Matricular o desmatricular en laboratorio"""

        accion = request.POST.get('accion')
        laboratorio_id = request.POST.get('laboratorio_id')

        try:
            estudiante = request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante_id = request.user.id

        servicio = servicio_matricula_laboratorio

        # Laboratorio_id viene como "<enrollment_id>-A" o "<enrollment_id>-B"
        try:
            enrollment_id, lab_key = laboratorio_id.split('-')
        except ValueError:
            enrollment_id = None
            lab_key = None

        if accion == 'matricular' and enrollment_id and lab_key:
            ok, msg = servicio.matricular_laboratorio(request, estudiante_id, enrollment_id, lab_key)
            messages.success(request, msg) if ok else messages.error(request, msg)
            if ok:
                # Guardar el laboratorio matriculado en la sesión
                matriculas_labs = request.session.get('matriculas_labs', {})
                matriculas_labs[str(enrollment_id)] = {
                    'lab_key': lab_key,
                    'lab_codigo': f"LAB-{lab_key}",
                    'fecha_matricula': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'enrollment_id': enrollment_id
                }
                request.session['matriculas_labs'] = matriculas_labs
                request.session.modified = True

        elif accion == 'desmatricular':
            ok, msg = servicio.desmatricular_laboratorio(request, estudiante_id, enrollment_id)
            messages.success(request, msg) if ok else messages.error(request, msg)

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

@login_required
def cursos(request):
    student = request.user.student

    enrollments = Enrollment.objects.filter(student=student).select_related(
        "course_group__course",
        "course_group",
        "course_group__teacher__user",
        "academic_period",
    )

    # Recuperamos laboratorios matriculados desde la sesión
    matriculas_labs = request.session.get("matriculas_labs", {})

    courses_info = []

    for e in enrollments:
        course = e.course_group.course
        group = e.course_group

        # Datos del profesor
        teacher = getattr(group, "teacher", None)

        # Datos de laboratorio
        lab_data = matriculas_labs.get(str(e.id))
        tiene_lab = lab_data is not None
        laboratorio_asignado = lab_data["lab_key"] if lab_data else None

        # Cálculo de progreso del curso (ejemplo simple)
        progress_info = {
            "progress_percentage": group.progress_percentage if hasattr(group, "progress_percentage") else 0,
            "current_week": group.current_week if hasattr(group, "current_week") else 1,
            "total_weeks": group.total_weeks if hasattr(group, "total_weeks") else 16,
        }

        courses_info.append({
            "course": {
                "name": course.name,
                "code": course.code,
                "credits": course.credits,
                "theory_hours": course.theory_hours,
                "practice_hours": course.practice_hours,
            },
            "course_group": {
                "group_code": group.group_code,
                "id": group.id,
            },
            "teacher": teacher,
            "has_syllabus": getattr(group, "has_syllabus", False),
            "progress_info": progress_info,
        })

    context = {
        "courses_info": courses_info,
        "error": None,
    }

    return render(request, "estudiante/cursos.html", context)


@login_required
def matricular_lab(request):
    """
    POST: espera enrollment_id y opcion_lab ('A' o 'B') y acción 'matricular' o 'desmatricular'
    """
    if request.method != 'POST':
        return redirect('estudiante:cursos')

    accion = request.POST.get('accion')
    enrollment_id = request.POST.get('enrollment_id')
    opcion_lab = request.POST.get('opcion_lab', '').upper()

    # obtener student id
    try:
        student = request.user.student
        estudiante_id = student.id
    except AttributeError:
        estudiante_id = request.user.id

    servicio = servicio_matricula_laboratorio

    if accion == 'matricular':
        ok, msg = servicio.matricular_laboratorio(request, estudiante_id, enrollment_id, opcion_lab)
        if ok:
            # Guardamos el grupo elegido en la sesión para reflejarlo luego
            matriculas_labs = request.session.get('matriculas_labs', {})
            matriculas_labs[str(enrollment_id)] = {
                'lab_key': opcion_lab,
                'lab_codigo': f"LAB-{opcion_lab}",
                'fecha_matricula': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'enrollment_id': enrollment_id
            }
            request.session['matriculas_labs'] = matriculas_labs
            request.session.modified = True
            messages.success(request, f"✅ Te matriculaste en Laboratorio {opcion_lab}")
        else:
            messages.error(request, msg)

    elif accion == 'desmatricular':
        ok, msg = servicio.desmatricular_laboratorio(request, estudiante_id, enrollment_id)
        if ok:
            # Eliminamos la matrícula del diccionario de sesión
            matriculas_labs = request.session.get('matriculas_labs', {})
            matriculas_labs.pop(str(enrollment_id), None)
            request.session['matriculas_labs'] = matriculas_labs
            request.session.modified = True
            messages.success(request, msg)
        else:
            messages.error(request, msg)

    return redirect('estudiante:cursos')


class EstudianteHorarioView(EstudianteRequiredMixin, TemplateView):
    """Vista del horario del estudiante"""
    template_name = 'estudiante/horarios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from servicios.servicioHorario import ServicioHorario
        from repositorio.postgres_repository.models import Enrollment, Horario
        from datetime import time
        # Crea una instancia del servicio
        servicio_horario = ServicioHorario()
        
        # Obtener el estudiante
        student = self.request.user.student
        
        # Obtener período activo
        period = AcademicPeriod.objects.filter(is_active=True).first()
        
        if not period:
            context['cursos_matriculados'] = []
            context['horario_semanal'] = []
            context['total_horas_semanales'] = 0
            context['total_laboratorios'] = 0
            context['total_aulas'] = 0
            return context
        
        # Obtener matrículas del estudiante
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_period=period,
            status='active'
        ).select_related('course_group__course', 'course_group__teacher__user')
        
        # Construir lista de cursos matriculados
        cursos_matriculados = []
        total_horas = 0
        aulas_set = set()
        
        for enrollment in enrollments:
            cg = enrollment.course_group
            course = cg.course
            
            # Obtener horarios del curso
            horarios = Horario.objects.filter(course_group=cg).select_related('aula')
            
            horarios_lista = []
            for h in horarios:
                horarios_lista.append({
                    'dia': h.dia_semana.capitalize(),
                    'hora_inicio': h.hora_inicio.strftime('%H:%M'),
                    'hora_fin': h.hora_fin.strftime('%H:%M'),
                    'aula': h.aula.codigo if h.aula else 'Por asignar',
                    'es_laboratorio': False  # Por ahora
                })
                
                # Calcular horas
                delta = (h.hora_fin.hour * 60 + h.hora_fin.minute) - (h.hora_inicio.hour * 60 + h.hora_inicio.minute)
                total_horas += delta / 60
                
                if h.aula:
                    aulas_set.add(h.aula.codigo)
            
            cursos_matriculados.append({
                'nombre': course.name,
                'codigo': course.code,
                'grupo': cg.group_code,
                'profesor_nombre': cg.teacher.user.get_full_name() if cg.teacher else 'Sin asignar',
                'creditos': course.credits,
                'horas_semanales': course.theory_hours + course.practice_hours,
                'tiene_laboratorio': False,  # Por ahora
                'horarios': horarios_lista
            })
        
        # Construir horario semanal (tabla)
        dias_orden = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
        
        # Obtener todos los horarios del estudiante
        todos_horarios = []
        for enrollment in enrollments:
            horarios = Horario.objects.filter(
                course_group=enrollment.course_group
            ).select_related('aula', 'course_group__course', 'course_group__teacher__user')
            todos_horarios.extend(horarios)
        
        # Agrupar por franjas horarias
        franjas_dict = {}
        for h in todos_horarios:
            key = (h.hora_inicio, h.hora_fin)
            if key not in franjas_dict:
                franjas_dict[key] = {dia: None for dia in dias_orden}
            
            franjas_dict[key][h.dia_semana] = {
                'curso': h.course_group.course.name,
                'profesor': h.course_group.teacher.user.get_full_name() if h.course_group.teacher else 'Sin asignar',
                'aula': h.aula.codigo if h.aula else 'Por asignar',
                'es_laboratorio': False
            }
        
        # Ordenar franjas por hora
        franjas_ordenadas = sorted(franjas_dict.items(), key=lambda x: x[0][0])
        
        # Construir estructura para el template
        horario_semanal = []
        for (hora_inicio, hora_fin), dias_data in franjas_ordenadas:
            franja = {
                'hora_inicio': hora_inicio.strftime('%H:%M'),
                'hora_fin': hora_fin.strftime('%H:%M'),
                'dias': []
            }
            
            for dia in dias_orden:
                franja['dias'].append({
                    'clase': dias_data[dia]
                })
            
            horario_semanal.append(franja)

        context.update({
            'cursos_matriculados': cursos_matriculados,
            'horario_semanal': horario_semanal,
            'total_horas_semanales': int(total_horas),
            'total_laboratorios': 0,  # Por implementar
            'total_aulas': len(aulas_set)
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

