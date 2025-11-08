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
from django.views.generic import TemplateView
from django.utils.timezone import now
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import time
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import EstudianteRequiredMixin
from servicios.servicioMatricula import ServicioMatricula
from servicios.servicioAsistencia import ServicioAsistencia
from servicios.servicioAvance import ServicioAvance
from servicios.servicioReservas import ServicioReservas
from servicios.servicioNotas import ServicioNotas
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from repositorio.postgres_repository.models import Enrollment
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from repositorio.postgres_repository.models import Enrollment
from servicios.servicioMatricula import ServicioMatricula
from repositorio.postgres_repository.models import (
    User, 
    Student, 
    AcademicPeriod, 
    Enrollment, 
    Horario
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
    template_name = 'estudiante/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante_id = self.request.user.id

        context.update({
            'horario_actual': [],
            'porcentaje_avance': 0.0,
            'porcentaje_asistencia': 0.0,
            'cursos_matriculados': []
        })
        return context


class EstudianteLaboratoriosView(EstudianteRequiredMixin, TemplateView):
    """Gestión de matrícula en laboratorios"""
    template_name = 'estudiante/laboratorios/index.html'

    def get_context_data(self, **kwargs):
        from repositorio.postgres_repository.models import Enrollment
        from servicios.servicioMatricula import ServicioMatricula

        context = super().get_context_data(**kwargs)

        # Obtener estudiante logueado
        try:
            estudiante = self.request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante = None
            estudiante_id = self.request.user.id

        # Obtener cursos matriculados
        enrollments = Enrollment.objects.filter(student=estudiante).select_related(
            "course_group__course", "academic_period"
        )

        servicio = ServicioMatricula(repo=None)
        cursos_context = servicio.preparar_contexto_enrollments(self.request, enrollments)

        # Laboratorios disponibles (todos los labs A y B de cada curso)
        laboratorios_disponibles = []
        for c in cursos_context:
            curso_id = c['enrollment_id']
            for key, lab in c['labs'].items():
                # Verificar si ya matriculado en este lab
                asignado = c['asignado']
                ya_matriculado = asignado and asignado.get('lab_codigo') == lab['codigo']

                # Verificar cupos usados
                matriculas = self.request.session.get('matriculas_labs', {})
                inscritos = sum(1 for m in matriculas.values() if m.get('lab_codigo') == lab['codigo'])
                porcentaje_ocupacion = int((inscritos / lab['capacidad']) * 100)

    
                # luego en tu código:
                curso_start = parse_hora(c['horario_curso']['start'])
                curso_end = parse_hora(c['horario_curso']['end'])
                from datetime import datetime, time


                # y cuando se usa:
                lab_start = parse_time(lab['horario']['start'])
                lab_end = parse_time(lab['horario']['end'])

                
                conflicto = (lab_start < curso_end) and (curso_start < lab_end)

                laboratorios_disponibles.append({
                    'id': f"{curso_id}-{key}",
                    'curso_id': curso_id,
                    'curso_nombre': c['curso_nombre'],
                    'laboratorio_codigo': lab['codigo'],
                    'profesor_nombre': "Asignar",
                    'aula': "Lab " + key,
                    'horario': f"{lab_start.strftime('%H:%M')} - {lab_end.strftime('%H:%M')}",
                    'capacidad': lab['capacidad'],
                    'estudiantes_matriculados': inscritos,
                    'porcentaje_ocupacion': porcentaje_ocupacion,
                    'ya_matriculado': ya_matriculado,
                    'tiene_cupos': inscritos < lab['capacidad'],
                    'conflicto_horario': conflicto,
                    'conflicto_con': c['curso_nombre'] if conflicto else None,
                    'duracion_horas': 2,
                    'equipos_disponibles': None,
                    'requisitos': None,
                })

        # Mis laboratorios actuales
        matriculas = self.request.session.get('matriculas_labs', {})
        mis_labs = []
        for m in matriculas.values():
            for c in cursos_context:
                if str(c['enrollment_id']) == str(m['enrollment_id']) or m.get('lab_codigo') in [l['codigo'] for l in c['labs'].values()]:
                    mis_labs.append({
                        'curso_nombre': c['curso_nombre'],
                        'laboratorio_codigo': m['lab_codigo'],
                        'profesor_nombre': "Asignar",
                        'aula': "Lab " + m['lab_key'],
                        'horario': f"{c['labs'][m['lab_key']]['horario']['start'][:5]} - {c['labs'][m['lab_key']]['horario']['end'][:5]}",
                        'estudiantes_matriculados': 1,
                        'capacidad': 20,
                        'fecha_matricula': datetime.parse_time(m['fecha_matricula']),
                        'laboratorio_id': m['lab_codigo'],
                    })

        context.update({
            'plazo_matricula_activo': True,
            'laboratorios_disponibles': laboratorios_disponibles,
            'matriculas_actuales': mis_labs,
            'cursos_con_laboratorio': [{'id': c['enrollment_id'], 'nombre': c['curso_nombre']} for c in cursos_context],
        })
        return context

    def post(self, request, *args, **kwargs):
        """Matricular o desmatricular en laboratorio"""
        from servicios.servicioMatricula import ServicioMatricula

        accion = request.POST.get('accion')
        laboratorio_id = request.POST.get('laboratorio_id')

        try:
            estudiante = request.user.student
            estudiante_id = estudiante.id
        except AttributeError:
            estudiante_id = request.user.id

        servicio = ServicioMatricula(repo=None)

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


@login_required
def cursos(request):
    student = request.user.student
    enrollments = Enrollment.objects.filter(student=student).select_related(
        "course_group__course", "academic_period"
    )

    # Recuperamos laboratorios matriculados desde la sesión
    matriculas_labs = request.session.get('matriculas_labs', {})

    cursos = []
    for e in enrollments:
        curso_nombre = e.course_group.course.name
        curso_codigo = e.course_group.course.code
        curso_grupo = e.course_group.group_code

        # Revisar si el curso tiene laboratorio matriculado
        lab_data = matriculas_labs.get(str(e.id))
        tiene_lab = lab_data is not None
        laboratorio_asignado = lab_data['lab_key'] if lab_data else None

        cursos.append({
            "nombre": curso_nombre,
            "codigo": curso_codigo,
            "grupo": curso_grupo,
            "tiene_lab": tiene_lab,
            "laboratorio_asignado": laboratorio_asignado,
        })

    return render(request, "estudiante/cursos.html", {"cursos": cursos})

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

    servicio = ServicioMatricula(repo=None)

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
        
        from repositorio.postgres_repository.models import Enrollment, Horario
        from datetime import time
        
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

