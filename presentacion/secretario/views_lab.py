#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vistas para la Gestión de Laboratorios y Carga de Horarios (Módulo Secretaría)
"""
# 1. Importaciones Estándar de Python
import re
import unicodedata
from datetime import datetime, time

# 2. Importaciones de Bibliotecas de Terceros
import pdfplumber
import difflib

# 3. Importaciones de Django
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db import transaction

# 4. Importaciones de la Aplicación (Modelos y Servicios)
from repositorio.postgres_repository.models import (
    Course, CourseGroup, AcademicPeriod, Aula, Horario, Classroom, Laboratory, User, Teacher
)
from .mixins import SecretarioRequiredMixin
from servicios.servicioMatriculaLaboratorio import servicio_matricula_laboratorio 
from servicios.servicioReservas import servicio_reservas 


# --- Funciones de Utilidad (Limpieza de texto) ---

def _limpiar_texto_local(txt: str) -> str:
    """Limpia caracteres dañados, tildes y convierte a mayúsculas uniformes"""
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = txt.encode("ASCII", "ignore").decode("utf-8", errors="ignore")
    txt = re.sub(r"[^A-Z0-9\s,.\-]", " ", txt.upper())
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


# --- VISTAS BASADAS EN CLASES (TemplateView) ---

class SecretarioLaboratoriosView(SecretarioRequiredMixin, TemplateView):
    """Gestión y visualización de laboratorios (Vista principal)"""
    template_name = 'secretario/laboratorios/index.html'
    DEFAULT_PERIOD_NAME = "2025-II"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Obtener la lista de ambientes físicos (LAB 01, LAB 02, ...) que tienen horarios cargados
        laboratorios_fisicos = Aula.objects.filter(
            tipo='laboratorio',
            horarios__laboratory__isnull=False
        ).distinct().order_by('codigo')

        # Diccionario para almacenar la información resumida por GRUPO DE LABORATORIO
        # Clave: (Codigo_Aula_Fisica, lab_code) -> Valor: Info Resumida
        grupos_lab_resumidos = {}
        
        for lab_fisico in laboratorios_fisicos:
            # Obtener todos los horarios asociados a este ambiente físico
            # Ordenar por día y hora para construir el string de horarios correctamente
            horarios = Horario.objects.filter(
                aula=lab_fisico
            ).select_related(
                'laboratory__course_group__course', 
                'laboratory__teacher__user'
            ).order_by('dia_semana', 'hora_inicio')

            # Agrupar los horarios por el GRUPO DE LABORATORIO (LAB A, LAB B, etc.)
            for h in horarios:
                lab_group = h.laboratory 
                course = lab_group.course_group.course
                teacher = lab_group.teacher
                
                # Usar una clave única para el grupo de laboratorio (lab_code)
                clave_grupo = f"{lab_fisico.codigo}_{lab_group.lab_code}_{course.id}"
                
                if clave_grupo not in grupos_lab_resumidos:
                    # Inicializar la entrada del grupo de laboratorio
                    grupos_lab_resumidos[clave_grupo] = {
                        'codigo_aula_fisica': lab_fisico.codigo,
                        'capacidad_aula': lab_fisico.capacidad,
                        'curso_nombre': course.name,
                        'curso_codigo': course.code, # Asumiendo que Course tiene un 'code'
                        'lab_code': lab_group.lab_code,
                        'profesor': teacher.user.get_full_name() if teacher and teacher.user else 'Pendiente',
                        'matriculados': lab_group.enrolled_students, 
                        'capacidad_grupo': lab_group.capacity,
                        'horarios_list': [] # Lista para almacenar los bloques de horario
                    }
                
                # Agregar el bloque de horario a la lista
                dia = h.dia_semana.capitalize()[:3] # LUN, MAR, MIE, etc.
                horario_str = f"{h.hora_inicio.strftime('%H:%M')}-{h.hora_fin.strftime('%H:%M')}"
                grupos_lab_resumidos[clave_grupo]['horarios_list'].append(f"{dia} {horario_str}")


        # Convertir la lista de bloques de horario en un solo string por grupo
        horarios_finales = []
        for clave, data in grupos_lab_resumidos.items():
            # Crear un string separado por saltos de línea (<br>) o comas
            data['horarios'] = '<br>'.join(data['horarios_list'])
            # Simplificamos el código de curso si es necesario, aquí usamos el lab_code como identificador principal
            data['codigo'] = f"{data['curso_codigo']}-{data['lab_code']}" if hasattr(course, 'code') else data['lab_code']
            horarios_finales.append(data)
            
        # Ordenar por código de aula física y luego por lab_code
        horarios_finales.sort(key=lambda x: (x['codigo_aula_fisica'], x['lab_code']))

        context.update({
            # Cambiamos el nombre de la variable para reflejar que es una lista plana
            'grupos_lab_resumidos': horarios_finales, 
            # Los demás servicios se mantienen
            'cursos_disponibles': servicio_matricula_laboratorio.obtener_cursos_con_laboratorio(),
             })
        return context  

# --- FUNCIONES BASADAS EN VISTAS (Procesamiento de Archivos) ---

@login_required
@require_POST
def cargar_horarios_laboratorios(request):
    """
    Procesa el PDF de horarios de Laboratorio, creando Laboratory y Horario,
    y asociando el aula física (LAB 01, LAB 02, etc.).
    """
    if not request.user.is_secretary():        
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:laboratorios')

    pdf_file = request.FILES.get('pdf_file')
    if not pdf_file or not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Debe seleccionar un archivo PDF válido.')
        return redirect('secretario:laboratorios')

    laboratorios_creados = 0
    horarios_creados = 0
    DEFAULT_PERIOD_NAME = "2025-II"
    redirect_url = redirect('secretario:laboratorios')


    try:
        with transaction.atomic():
            period = AcademicPeriod.objects.get(name=DEFAULT_PERIOD_NAME)
            
            # 1. Mapeo de cursos existentes (para búsqueda difusa rápida)
            course_map = {
                _limpiar_texto_local(c.name): c
                for c in Course.objects.all()
            }
            nombres_db_limpios = list(course_map.keys())
            
            with pdfplumber.open(pdf_file) as pdf:
                ambiente_fisico_actual = None 
                
                for page in pdf.pages:
                    texto = page.extract_text() or ""
                    lineas = texto.split('\n')

                    for linea in lineas:
                        linea = linea.strip()
                        if not linea: continue

                        # 1️⃣ Detectar AMBIENTE FÍSICO (Creación de LAB 01, LAB 02, etc. en Aula y Classroom)
                        if linea.upper().startswith('LABORATORIO:'):
                            codigo_lab_fisico = linea.split(':', 1)[-1].strip()[:100]
                            ambiente_fisico_actual, creada = Aula.objects.get_or_create(
                                codigo=codigo_lab_fisico,
                                defaults={"nombre": codigo_lab_fisico, "capacidad": 30, "tipo": "laboratorio"}
                            )
                            if creada:
                                Classroom.objects.get_or_create(
                                    code=codigo_lab_fisico[:20],
                                    defaults={
                                        "name": codigo_lab_fisico,
                                        "room_type": "laboratory",
                                        "capacity": 30,
                                        "is_active": True,
                                    }
                                )
                            continue

                        # 2️⃣ Detectar línea de horario de Laboratorio
                        if re.match(r'^(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO)', linea.upper()):
                            if not ambiente_fisico_actual: continue
                            try:
                                # Extracción de Día, Horas y Curso/Grupo LAB
                                partes = re.split(r'\s+', linea)
                                dia = partes[0].lower()
                                horas_match = re.search(r'(\d{2}:\d{2})/(\d{2}:\d{2})', linea)
                                if not horas_match: continue
                                hora_ini, hora_fin = horas_match.groups()
                                resto = linea.split(horas_match.group(0), 1)[-1].strip()
                                
                                # Patrón: CURSO_NOMBRE LAB_CODE (Ej: SEGURIDAD EN COMPUTACION LAB A)
                                match_curso_lab = re.match(r'(.+?)\s(LAB\s[A-Z0-9]+)$', resto, re.IGNORECASE)
                                if not match_curso_lab: continue

                                nombre_curso, lab_code_academico = match_curso_lab.groups()
                                lab_code_academico = lab_code_academico.upper().strip()

                                # 3️⃣ BÚSQUEDA DEL CURSO (Difusa)
                                nombre_curso_limpio = _limpiar_texto_local(nombre_curso)
                                coincidencias = difflib.get_close_matches(nombre_curso_limpio, nombres_db_limpios, n=1, cutoff=0.7)

                                if not coincidencias: continue
                                course = course_map.get(coincidencias[0])
                                if not course: continue

                                # 4️⃣ Encontrar/Crear CourseGroup Base 
                                # Usar 'L' para el grupo base si es necesario, ya que la teoría no importa.
                                cg, _ = CourseGroup.objects.get_or_create(
                                    course=course,
                                    academic_period=period,
                                    group_code='L' 
                                )
                                
                                # 5️⃣ Encontrar/Crear el GRUPO ACADÉMICO DE LABORATORIO (LAB A, LAB B, etc.)
                                laboratory, lab_created = Laboratory.objects.get_or_create(
                                    course_group=cg,
                                    lab_code=lab_code_academico,
                                    defaults={
                                        "capacity": ambiente_fisico_actual.capacidad, 
                                        "lab_room": ambiente_fisico_actual.codigo,   # <- VINCULO AL AMBIENTE FÍSICO
                                        "schedule_info": {"notes": "Horario cargado por archivo"},
                                        "is_active": True
                                    }
                                )
                                if lab_created: laboratorios_creados += 1

                                # 6️⃣ Crear Horario (Vínculo de tiempo)
                                hora_inicio = datetime.strptime(hora_ini, "%H:%M").time()
                                hora_fin = datetime.strptime(hora_fin, "%H:%M").time()

                                _, creado = Horario.objects.get_or_create(
                                    course_group=cg,
                                    aula=ambiente_fisico_actual,
                                    dia_semana=dia,
                                    hora_inicio=hora_inicio,
                                    hora_fin=hora_fin,
                                    laboratory=laboratory # Clave: enlaza a la sección de laboratorio elegible
                                )

                                if creado: horarios_creados += 1

                            except Exception as e:
                                print(f"Error procesando línea: {linea}\nMotivo: {e}")
                                continue

        messages.success(request, f"{laboratorios_creados} grupos de laboratorio creados, {horarios_creados} horarios registrados en {DEFAULT_PERIOD_NAME}")

    except AcademicPeriod.DoesNotExist:
        messages.error(request, f"Error: El período '{DEFAULT_PERIOD_NAME}' no existe. Debe cargarse primero.")
    except Exception as e:
        messages.error(request, f"Error general en la carga de laboratorios: {e}")

    return redirect_url

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
