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

    cursos = []
    for e in enrollments:
        # Tomamos el curso real
        curso_nombre = e.course_group.course.name
        curso_codigo = e.course_group.course.code
        curso_grupo = e.course_group.group_code

        # Asignamos solo visualmente un laboratorio (sin borrar datos)
        tiene_lab = random.choice([True, False])
        laboratorio_asignado = random.choice(["A", "B"]) if tiene_lab else None

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
    opcion = request.POST.get('opcion_lab', '').upper()

    # obtener student id
    try:
        student = request.user.student
        estudiante_id = student.id
    except AttributeError:
        estudiante_id = request.user.id

    servicio = ServicioMatricula(repo=None)

    if accion == 'matricular':
        ok, msg = servicio.matricular_laboratorio(request, estudiante_id, enrollment_id, opcion)
        if ok:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    elif accion == 'desmatricular':
        ok, msg = servicio.desmatricular_laboratorio(request, estudiante_id, enrollment_id)
        if ok:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('estudiante:cursos')

class EstudianteHorarioView(EstudianteRequiredMixin, TemplateView):
    """Vista del horario del estudiante"""
    template_name = 'estudiante/horarios/index.html'

    def get_context_data(self, **kwargs):
        from repositorio.postgres_repository.models import Enrollment, LaboratoryEnrollment
        context = super().get_context_data(**kwargs)

        estudiante = getattr(self.request.user, "student", None)
        if not estudiante:
            context.update({"horario_semanal": [], "cursos_matriculados": []})
            return context

        # 🟦 Cursos y laboratorios matriculados
        enrollments = Enrollment.objects.filter(
            student=estudiante, status="active"
        ).select_related("course_group__course", "course_group__teacher")

        lab_enrollments = LaboratoryEnrollment.objects.filter(
            student=estudiante, status="active"
        ).select_related("laboratory__course_group__course")

        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horario = {dia: [] for dia in dias_semana}

        # ⏰ Horas realistas para simular horarios (bloques de 1h30)
        horas_ficticias = [
            ("07:00", "08:30"),
            ("08:30", "10:00"),
            ("10:00", "11:30"),
            ("11:30", "13:00"),
            ("14:00", "15:30"),
            ("15:30", "17:00"),
            ("17:00", "18:30"),
        ]
        bloque_ocupado = set()  # (dia, inicio, fin)

        # 🔹 PRIMERO: asignar cursos teóricos (simulados si no tienen horario)
        for idx, e in enumerate(enrollments):
            schedule = e.course_group.schedule_info or []

            # Si no tiene horario real → crear uno simulado libre
            if not schedule:
                for h_inicio, h_fin in horas_ficticias:
                    dia = dias_semana[idx % len(dias_semana)]
                    if (dia, h_inicio, h_fin) not in bloque_ocupado:
                        schedule = [{
                            "dia": dia,
                            "start": h_inicio,
                            "end": h_fin,
                            "aula": f"A-{idx+1}"
                        }]
                        bloque_ocupado.add((dia, h_inicio, h_fin))
                        break

            if isinstance(schedule, dict):
                schedule = [schedule]

            # Añadir a horario
            for bloque in schedule:
                dia = bloque.get("dia", "").capitalize()
                if dia in horario:
                    bloque_ocupado.add((dia, bloque.get("start"), bloque.get("end")))
                    horario[dia].append({
                        "inicio": bloque.get("start"),
                        "fin": bloque.get("end"),
                        "curso": e.course_group.course.name,
                        "aula": bloque.get("aula", e.course_group.classroom or "-"),
                        "profesor": "",  # vacío
                        "es_laboratorio": False,
                    })

        # 🔸 DESPUÉS: agregar laboratorios sin superponer
        for le in lab_enrollments:
            lab = le.laboratory
            schedule = lab.schedule_info or []

            if not schedule:
                for h_inicio, h_fin in horas_ficticias:
                    dia = dias_semana[(len(bloque_ocupado) + 1) % len(dias_semana)]
                    if (dia, h_inicio, h_fin) not in bloque_ocupado:
                        schedule = [{
                            "dia": dia,
                            "start": h_inicio,
                            "end": h_fin,
                            "aula": f"LAB-{dia[:3].upper()}"
                        }]
                        bloque_ocupado.add((dia, h_inicio, h_fin))
                        break

            if isinstance(schedule, dict):
                schedule = [schedule]

            for bloque in schedule:
                dia = bloque.get("dia", "").capitalize()
                if dia in horario:
                    horario[dia].append({
                        "inicio": bloque.get("start"),
                        "fin": bloque.get("end"),
                        "curso": lab.course_group.course.name,
                        "aula": bloque.get("aula", lab.lab_room or "-"),
                        "profesor": "",
                        "es_laboratorio": True,
                    })

        # 🧮 Calcular todas las horas usadas
        horas_unicas = sorted({
            b["inicio"] for clases in horario.values() for b in clases
        }.union({
            b["fin"] for clases in horario.values() for b in clases
        }))

        # 🧱 Construcción de cuadrícula para el template
        horario_semanal = []
        for i in range(len(horas_unicas) - 1):
            franja = {
                "hora_inicio": horas_unicas[i],
                "hora_fin": horas_unicas[i + 1],
                "dias": [],
            }
            for dia in dias_semana:
                clase = next(
                    (c for c in horario[dia] if c["inicio"] == horas_unicas[i]),
                    None,
                )
                franja["dias"].append({"dia": dia, "clase": clase})
            horario_semanal.append(franja)

        # 📘 Cursos matriculados (para la tabla inferior)
        cursos_matriculados = []
        for idx, e in enumerate(enrollments):
            schedule = e.course_group.schedule_info or []
            if not schedule:
                dia = dias_semana[idx % len(dias_semana)]
                h_inicio, h_fin = horas_ficticias[idx % len(horas_ficticias)]
                schedule = [{"dia": dia, "hora_inicio": h_inicio, "hora_fin": h_fin, "aula": f"A-{idx+1}"}]

            cursos_matriculados.append({
                "nombre": e.course_group.course.name,
                "codigo": e.course_group.course.code,
                "grupo": e.course_group.group_code,
                "profesor_nombre": "",
                "creditos": e.course_group.course.credits,
                "horas_semanales": e.course_group.course.theory_hours + e.course_group.course.practice_hours,
                "tiene_laboratorio": LaboratoryEnrollment.objects.filter(
                    student=estudiante,
                    laboratory__course_group=e.course_group,
                    status="active",
                ).exists(),
                "horarios": schedule,
            })

        context.update({
            "horario_semanal": horario_semanal,
            "cursos_matriculados": cursos_matriculados,
            "total_horas_semanales": len(horas_unicas) - 1,
            "total_laboratorios": len(lab_enrollments),
            "total_aulas": len(set([e.course_group.classroom for e in enrollments if e.course_group.classroom])),
        })
        return context
