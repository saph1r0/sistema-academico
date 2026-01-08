#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vistas para la Gestión de Laboratorios y Carga de Horarios (Módulo Secretaría)
"""

# 1. Importaciones estándar
import re
import unicodedata
from datetime import datetime
from collections import defaultdict

# 2. Terceros
import pandas as pd
import difflib


# 3. Django
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db import transaction

# 4. Modelos
from repositorio.postgres_repository.models import (
    Course, CourseGroup, AcademicPeriod, Aula, Horario,
    Classroom, Laboratory, Teacher
)

from .mixins import SecretarioRequiredMixin
from servicios.servicioMatriculaLaboratorio import servicio_matricula_laboratorio


# ==========================================================
# Utils
# ==========================================================

def _intervals_conflict(start1, end1, start2, end2) -> bool:
    return (start1 < end2) and (start2 < end1)


def _limpiar_texto_local(txt: str) -> str:
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = txt.encode("ASCII", "ignore").decode("utf-8", errors="ignore")
    txt = re.sub(r"[^A-Z0-9\s,.\-]", " ", txt.upper())
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


# ==========================================================
# Vista principal 
# ==========================================================

class SecretarioLaboratoriosView(SecretarioRequiredMixin, TemplateView):
    template_name = 'secretario/laboratorios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        periodo_activo = AcademicPeriod.objects.filter(is_active=True).first()
        docentes = Teacher.objects.select_related('user').all()

        laboratorios_fisicos = Aula.objects.filter(
            tipo='laboratorio',
            horarios__laboratory__isnull=False
        ).distinct().order_by('codigo')

        teacher_busy = defaultdict(lambda: defaultdict(list))

        qs_busy = Horario.objects.filter(laboratory__teacher_id__isnull=False)
        if periodo_activo:
            qs_busy = qs_busy.filter(laboratory__course_group__academic_period=periodo_activo)

        qs_busy = qs_busy.values(
            'laboratory__teacher_id', 'dia_semana',
            'hora_inicio', 'hora_fin', 'laboratory_id'
        )

        for r in qs_busy:
            teacher_busy[r['laboratory__teacher_id']][r['dia_semana']].append(
                (r['hora_inicio'], r['hora_fin'], r['laboratory_id'])
            )

        grupos = {}

        for lab_fisico in laboratorios_fisicos:
            horarios = Horario.objects.filter(
                aula=lab_fisico
            ).select_related(
                'laboratory__course_group__course',
                'laboratory__teacher__user'
            )

            for h in horarios:
                lab = h.laboratory
                course = lab.course_group.course
                teacher = lab.teacher

                key = f"{lab_fisico.codigo}_{lab.lab_code}_{course.id}"

                if key not in grupos:
                    grupos[key] = {
                        'laboratory_id': lab.id,
                        'teacher_id': lab.teacher_id,
                        'codigo_aula_fisica': lab_fisico.codigo,
                        'curso_nombre': course.name,
                        'curso_codigo': course.code,
                        'lab_code': lab.lab_code,
                        'profesor': teacher.user.get_full_name() if teacher else 'Pendiente',
                        'matriculados': lab.enrolled_students,
                        'capacidad_grupo': lab.capacity,
                        'horarios_list': [],
                        'horarios_raw': []
                    }

                grupos[key]['horarios_list'].append(
                    f"{h.dia_semana[:3].upper()} {h.hora_inicio.strftime('%H:%M')}-{h.hora_fin.strftime('%H:%M')}"
                )
                grupos[key]['horarios_raw'].append(
                    (h.dia_semana, h.hora_inicio, h.hora_fin)
                )

        resultado = []
        for g in grupos.values():
            g['horarios'] = '<br>'.join(g['horarios_list'])

            if g.get('curso_codigo'):
                g['codigo'] = f"{g['curso_codigo']}-{g['lab_code']}"
            else:
                g['codigo'] = g['lab_code']

            resultado.append(g)

        # ===== CALCULAR DOCENTES DISPONIBLES (SIN CRUCE REAL) =====
        for g in resultado:
            lab_actual_id = g['laboratory_id']
            lab_slots = g.get('horarios_raw', [])

            disponibles = []

            for t in docentes:
                conflicto = False

                horarios_docente = teacher_busy.get(t.id, {})

                for dia, ini, fin in lab_slots:
                    for b_ini, b_fin, b_lab_id in horarios_docente.get(dia, []):

                        # ignorar el mismo laboratorio
                        if b_lab_id == lab_actual_id:
                            continue

                        # cruce real
                        if _intervals_conflict(ini, fin, b_ini, b_fin):
                            conflicto = True
                            break

                    if conflicto:
                        break

                if not conflicto:
                    disponibles.append({
                        'id': t.id,
                        'nombre': t.user.get_full_name()
                    })

            g['docentes_disponibles'] = disponibles

            # marcar si el docente actual tiene cruce
            g['teacher_conflicto'] = False
            if g.get('teacher_id'):
                g['teacher_conflicto'] = not any(
                    d['id'] == g['teacher_id'] for d in disponibles
                )
        # =========================
        # ESTADÍSTICAS RÁPIDAS (LABS)
        # =========================

        ambientes_fisicos = set()
        capacidad_total = 0
        ocupacion_total = 0

        for g in resultado:
            # aulas físicas únicas
            if g.get('codigo_aula_fisica'):
                ambientes_fisicos.add(g['codigo_aula_fisica'])

            # capacidad y ocupación
            if g.get('capacidad_grupo'):
                capacidad_total += g['capacidad_grupo']

            if g.get('matriculados'):
                ocupacion_total += g['matriculados']

        total_ambientes_fisicos = len(ambientes_fisicos)

        ocupacion_promedio = 0
        if capacidad_total > 0:
            ocupacion_promedio = round((ocupacion_total / capacidad_total) * 100)
        context.update({
            'total_ambientes_fisicos': total_ambientes_fisicos,
            'ocupacion_promedio': ocupacion_promedio,
        })

        context['grupos_lab_resumidos'] = resultado
        context['periodo_activo'] = periodo_activo
        context['cursos_disponibles'] = servicio_matricula_laboratorio.obtener_cursos_con_laboratorio()
        return context
    
@login_required
@require_POST
def cargar_horarios_laboratorios(request):
    if not request.user.is_secretary():
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:laboratorios')

    excel_file = request.FILES.get('excel_file')
    if not excel_file or not excel_file.name.lower().endswith('.xlsx'):
        messages.error(request, 'Debe subir un archivo Excel (.xlsx).')
        return redirect('secretario:laboratorios')

    periodo = AcademicPeriod.objects.filter(is_active=True).first()
    if not periodo:
        messages.error(request, 'No hay período académico activo.')
        return redirect('secretario:laboratorios')

    laboratorios_creados = 0
    horarios_creados = 0

    # 🔴 MAPA: lab_id → nombre_docente (para asignar al final)
    docente_por_lab = {}

    try:
        df = pd.read_excel(excel_file)

        required_cols = [
            'ASIGNATURA',
            'GRUPO LAB',
            'DOCENTE',
            'AULA FÍSICA',
            'HORARIOS'
        ]
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f'Falta columna {col} en el Excel')

        # Mapeo de cursos (igual que PDF)
        course_map = {
            _limpiar_texto_local(c.name): c
            for c in Course.objects.all()
        }
        nombres_db_limpios = list(course_map.keys())

        with transaction.atomic():
            for _, row in df.iterrows():
                nombre_curso = str(row['ASIGNATURA']).strip()
                lab_code_academico = str(row['GRUPO LAB']).strip().upper()
                aula_codigo = str(row['AULA FÍSICA']).strip()
                docente_nombre = str(row['DOCENTE']).strip()
                bloque_horarios = str(row['HORARIOS'])

                # ---------- AULA ----------
                aula, _ = Aula.objects.get_or_create(
                    codigo=aula_codigo,
                    defaults={
                        'nombre': aula_codigo,
                        'capacidad': 30,
                        'tipo': 'laboratorio'
                    }
                )

                # ---------- CURSO (búsqueda difusa) ----------
                nombre_curso_limpio = _limpiar_texto_local(nombre_curso)
                coincidencias = difflib.get_close_matches(
                    nombre_curso_limpio,
                    nombres_db_limpios,
                    n=1,
                    cutoff=0.7
                )
                if not coincidencias:
                    continue

                course = course_map.get(coincidencias[0])
                if not course:
                    continue

                # ---------- COURSE GROUP ----------
                cg, _ = CourseGroup.objects.get_or_create(
                    course=course,
                    academic_period=periodo,
                    group_code='L',
                    defaults={'capacity': 0}
                )

                # ---------- LABORATORY ----------
                laboratory, lab_created = Laboratory.objects.get_or_create(
                    course_group=cg,
                    lab_code=lab_code_academico,
                    defaults={
                        'capacity': None,
                        'lab_room': aula.codigo,
                        'is_active': True
                    }
                )
                if lab_created:
                    laboratorios_creados += 1

                # ---------- GUARDAR DOCENTE (NO ASIGNAR AÚN) ----------
                if (
                    laboratory.id not in docente_por_lab
                    and docente_nombre
                    and docente_nombre.lower() != 'nan'
                ):
                    docente_por_lab[laboratory.id] = docente_nombre

                # ---------- HORARIOS ----------
                lineas_horario = bloque_horarios.split('\n')
                for linea in lineas_horario:
                    linea = linea.strip()
                    if not linea:
                        continue

                    match = re.match(
                        r'(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO)\s+(\d{2}:\d{2})-(\d{2}:\d{2})',
                        linea.upper()
                    )
                    if not match:
                        continue

                    dia, hora_ini, hora_fin = match.groups()
                    dia = dia.lower()

                    hora_inicio = datetime.strptime(hora_ini, "%H:%M").time()
                    hora_fin = datetime.strptime(hora_fin, "%H:%M").time()

                    _, creado = Horario.objects.get_or_create(
                        course_group=cg,
                        aula=aula,
                        dia_semana=dia,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        laboratory=laboratory
                    )
                    if creado:
                        horarios_creados += 1

        # ---------- ASIGNAR DOCENTE FINAL (COMO BOTÓN GUARDAR) ----------
        for lab_id, docente_nombre in docente_por_lab.items():
            lab = Laboratory.objects.get(id=lab_id)

            if lab.teacher:
                continue

            docente_limpio = _limpiar_texto_local(docente_nombre)

            for t in Teacher.objects.select_related('user'):
                nombre_db = _limpiar_texto_local(
                    f"{t.user.first_name} {t.user.last_name}"
                )

                if docente_limpio == nombre_db:
                    lab.teacher = t
                    lab.save(update_fields=['teacher'])
                    break

        messages.success(
            request,
            f"{laboratorios_creados} laboratorios y "
            f"{horarios_creados} horarios cargados correctamente."
        )

    except Exception as e:
        messages.error(request, f"Error procesando Excel: {e}")

    return redirect('secretario:laboratorios')


@login_required
@require_POST
def configurar_cupo_global_laboratorio(request):
    if not request.user.is_secretary():
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:laboratorios')

    try:
        cupo = int(request.POST.get('cupo_global'))
        if cupo < 0:
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, 'Ingrese un número válido.')
        return redirect('secretario:laboratorios')

    actualizados = Laboratory.objects.update(capacity=cupo)

    messages.success(
        request,
        f'Cupo global actualizado correctamente ({actualizados} laboratorios).'
    )

    return redirect('secretario:laboratorios')

@login_required
@require_POST
def configurar_periodo_matricula_laboratorio(request):
    if not request.user.is_secretary():
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:laboratorios')

    periodo_id = request.POST.get('periodo_id')
    inicio = request.POST.get('laboratory_enrollment_start')
    fin = request.POST.get('laboratory_enrollment_end')

    if not periodo_id or not inicio or not fin:
        messages.error(request, 'Datos incompletos.')
        return redirect('secretario:laboratorios')

    try:
        inicio_date = datetime.strptime(inicio, "%Y-%m-%d").date()
        fin_date = datetime.strptime(fin, "%Y-%m-%d").date()

        if inicio_date > fin_date:
            messages.error(request, 'La fecha de inicio no puede ser mayor que la fecha fin.')
            return redirect('secretario:laboratorios')

        period = AcademicPeriod.objects.get(id=periodo_id)
        period.laboratory_enrollment_start = inicio_date
        period.laboratory_enrollment_end = fin_date
        period.save(update_fields=["laboratory_enrollment_start", "laboratory_enrollment_end"])

        messages.success(request, '✅ Período de matrícula de laboratorio actualizado.')
    except AcademicPeriod.DoesNotExist:
        messages.error(request, 'Período académico no encontrado.')
    except ValueError:
        messages.error(request, 'Formato de fecha inválido.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    return redirect('secretario:laboratorios')

@login_required
@require_POST
def asignar_docente_laboratorio(request):
    if not request.user.is_secretary():
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:laboratorios')

    lab_id = request.POST.get('laboratory_id')
    teacher_id = request.POST.get('teacher_id') or None

    try:
        lab = Laboratory.objects.select_related('course_group__academic_period').get(id=lab_id)

        # si quieren quitar docente
        if teacher_id is None:
            lab.teacher = None
            lab.save(update_fields=['teacher'])
            messages.success(request, '✅ Docente retirado del laboratorio.')
            return redirect('secretario:laboratorios')

        teacher = Teacher.objects.select_related('user').get(id=teacher_id)

        # ✅ revalidar cruce en backend
        lab_horarios = Horario.objects.filter(laboratory=lab).values('dia_semana', 'hora_inicio', 'hora_fin')

        busy = Horario.objects.filter(laboratory__teacher=teacher).exclude(laboratory=lab)

        # filtra por periodo activo si quieres (recomendado)
        periodo_activo = AcademicPeriod.objects.filter(is_active=True).first()
        if periodo_activo:
            busy = busy.filter(laboratory__course_group__academic_period=periodo_activo)

        busy = busy.values('dia_semana', 'hora_inicio', 'hora_fin')

        for lh in lab_horarios:
            dia = (lh['dia_semana'] or '').lower()
            ini, fin = lh['hora_inicio'], lh['hora_fin']

            for bh in busy:
                if (bh['dia_semana'] or '').lower() != dia:
                    continue
                if _intervals_conflict(ini, fin, bh['hora_inicio'], bh['hora_fin']):
                    messages.error(request, f'❌ Cruce de horario: {teacher.user.get_full_name()} no está disponible.')
                    return redirect('secretario:laboratorios')

        lab.teacher = teacher
        lab.save(update_fields=['teacher'])
        messages.success(request, f'✅ Docente asignado: {teacher.user.get_full_name()}')
        return redirect('secretario:laboratorios')

    except Laboratory.DoesNotExist:
        messages.error(request, 'Laboratorio no encontrado.')
    except Teacher.DoesNotExist:
        messages.error(request, 'Docente no encontrado.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    return redirect('secretario:laboratorios')

