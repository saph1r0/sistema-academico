"""
Vistas para el módulo de secretarios
"""
# 1. Importaciones Estándar de Python
import re
import unicodedata
from datetime import datetime

# 2. Importaciones de Bibliotecas de Terceros
import PyPDF2
import openpyxl
import pdfplumber
import difflib

# 3. Importaciones de Django
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.views.generic import TemplateView
from django.db import transaction
from django.db.models import Q

# 4. Importaciones de la Aplicación (Modelos y Servicios)
from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod, Aula, Horario, Student, Enrollment
)
from .mixins import SecretarioRequiredMixin
from servicios.servicioMatricula import ServicioMatricula
from servicios.servicioReservas import ServicioReservas
from servicios.servicioReportes import ServicioReportes
from servicios.servicioMonitoreo import ServicioMonitoreo

# --- Funciones de Utilidad ---

# Se mantiene la función para el manejo de texto en PDFs/Excels.
def limpiar_texto(txt: str) -> str:
    """Convierte el texto a mayúsculas y elimina tildes, signos raros y símbolos dañados del PDF."""
    if not txt:
        return ""
    # Elimina caracteres no ASCII
    txt = unicodedata.normalize("NFKD", txt)
    txt = txt.encode("ASCII", "ignore").decode("utf-8", errors="ignore")
    txt = re.sub(r"[^A-Z0-9\s]", " ", txt.upper())  # Solo letras, números y espacios
    txt = re.sub(r"\s+", " ", txt).strip()  # Colapsar espacios múltiples
    return txt


# --- Vistas de Dashboard y Gestión ---

class SecretarioDashboardView(SecretarioRequiredMixin, TemplateView):
    """Dashboard principal del secretario"""
    template_name = 'secretario/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'resumen_inscripciones': ServicioMatricula.obtener_resumen_inscripciones(),
            #'laboratorios_ocupacion': ServicioReservas.obtener_ocupacion_laboratorios(),
            'alertas_sistema': ServicioMonitoreo.obtener_alertas_academicas(),
            'estadisticas_generales': ServicioReportes.obtener_estadisticas_generales()
        })
        return context


class SecretarioLaboratoriosView(SecretarioRequiredMixin, TemplateView):
    """Gestión de inscripciones de laboratorio"""
    template_name = 'secretario/laboratorios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtros de búsqueda
        curso_filtro = self.request.GET.get('curso')
        laboratorio_filtro = self.request.GET.get('laboratorio')
        estado_filtro = self.request.GET.get('estado')

        context.update({
            'inscripciones_laboratorio': ServicioMatricula.obtener_inscripciones_laboratorio(
                curso=curso_filtro,
                laboratorio=laboratorio_filtro,
                estado=estado_filtro
            ),
            'cursos_disponibles': ServicioMatricula.obtener_cursos_con_laboratorio(),
            'laboratorios_disponibles': ServicioReservas.obtener_todos_laboratorios(),
            'estadisticas_ocupacion': ServicioReservas.obtener_estadisticas_ocupacion()
        })
        return context

    def post(self, request, *args, **kwargs):
        """Gestionar inscripciones de laboratorio"""
        accion = request.POST.get('accion')
        inscripcion_id = request.POST.get('inscripcion_id')
        redirect_url = redirect('secretario:laboratorios')

        if not inscripcion_id:
            messages.error(request, 'Error: ID de inscripción no proporcionado.')
            return redirect_url

        try:
            with transaction.atomic():
                if accion == 'aprobar':
                    ServicioMatricula.aprobar_inscripcion_laboratorio(inscripcion_id)
                    messages.success(request, 'Inscripción aprobada exitosamente.')
                elif accion == 'rechazar':
                    motivo = request.POST.get('motivo', 'Sin motivo especificado')
                    ServicioMatricula.rechazar_inscripcion_laboratorio(inscripcion_id, motivo)
                    messages.success(request, 'Inscripción rechazada.')
                elif accion == 'redistribuir':
                    nuevo_laboratorio_id = request.POST.get('nuevo_laboratorio_id')
                    if not nuevo_laboratorio_id:
                        raise ValueError("Debe seleccionar un nuevo laboratorio para redistribuir.")
                    ServicioMatricula.redistribuir_estudiante_laboratorio(inscripcion_id, nuevo_laboratorio_id)
                    messages.success(request, 'Estudiante redistribuido exitosamente.')
                else:
                    messages.warning(request, f'Acción "{accion}" no reconocida.')

        except ValueError as ve:
            messages.error(request, f'Error de validación: {str(ve)}')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')

        return redirect_url


class SecretarioReportesView(SecretarioRequiredMixin, TemplateView):
    """Generación de reportes académicos"""
    template_name = 'secretario/reportes/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'tipos_reporte': [
                ('asistencia_general', 'Reporte de Asistencia General'),
                ('notas_por_curso', 'Reporte de Notas por Curso'),
                ('estadisticas_periodo', 'Estadísticas por Período'),
                ('ocupacion_laboratorios', 'Ocupación de Laboratorios'),
                ('rendimiento_academico', 'Rendimiento Académico')
            ],
            'periodos_academicos': ServicioReportes.obtener_periodos_disponibles(),
            'cursos_disponibles': ServicioReportes.obtener_cursos_disponibles(),
            'reportes_generados': ServicioReportes.obtener_reportes_recientes()
        })
        return context

    def post(self, request, *args, **kwargs):
        """Generar reportes académicos"""
        tipo_reporte = request.POST.get('tipo_reporte')
        formato = request.POST.get('formato', 'pdf')
        periodo_id = request.POST.get('periodo_id')
        curso_id = request.POST.get('curso_id')
        redirect_url = redirect('secretario:reportes')

        try:
            reporte_dispatch = {
                'asistencia_general': lambda: ServicioReportes.generar_reporte_asistencia_general(periodo_id=periodo_id, formato=formato),
                'notas_por_curso': lambda: ServicioReportes.generar_reporte_notas_curso(curso_id=curso_id, periodo_id=periodo_id, formato=formato),
                'estadisticas_periodo': lambda: ServicioReportes.generar_estadisticas_periodo(periodo_id=periodo_id, formato=formato),
                'ocupacion_laboratorios': lambda: ServicioReportes.generar_reporte_ocupacion_laboratorios(periodo_id=periodo_id, formato=formato),
                'rendimiento_academico': lambda: ServicioReportes.generar_reporte_rendimiento_academico(periodo_id=periodo_id, formato=formato),
            }

            if tipo_reporte in reporte_dispatch:
                response = reporte_dispatch[tipo_reporte]()
                if isinstance(response, HttpResponse):
                    return response
                raise Exception("El servicio de reporte no devolvió una respuesta válida.")
            else:
                messages.error(request, 'Tipo de reporte no válido.')
                return redirect_url

        except Exception as e:
            messages.error(request, f'Error al generar reporte: {str(e)}')
            return redirect_url


class SecretarioEstadisticasView(SecretarioRequiredMixin, TemplateView):
    """Vista de estadísticas académicas"""
    template_name = 'secretario/estadisticas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'estadisticas_matricula': ServicioMatricula.obtener_estadisticas_matricula(),
            'estadisticas_asistencia': ServicioReportes.obtener_estadisticas_asistencia(),
            'estadisticas_notas': ServicioReportes.obtener_estadisticas_notas(),
            'tendencias_academicas': ServicioReportes.obtener_tendencias_academicas(),
            'alertas_academicas': ServicioMonitoreo.obtener_alertas_detalladas()
        })
        return context

class SecretarioUsuariosView(SecretarioRequiredMixin, TemplateView):
    """Gestión de usuarios"""
    template_name = 'secretario/usuarios/lista.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Base Queryset
        queryset = User.objects.all().order_by('last_name', 'first_name')

        # 2. Filtros
        role_filter = self.request.GET.get('rol')
        if role_filter and role_filter != 'todos':
            queryset = queryset.filter(role=role_filter)

        status_filter = self.request.GET.get('estado')
        if status_filter == 'activo':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactivo':
            queryset = queryset.filter(is_active=False)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(institutional_email__icontains=search)
            )

        # 3. Contexto
        context.update({
            'usuarios': queryset,
            'page_title': 'Gestión de Usuarios',
            'roles_choices': User.ROLE_CHOICES,
            'current_filters': {
                'rol': self.request.GET.get('rol', 'todos'),
                'estado': self.request.GET.get('estado', 'todos'),
                'search': self.request.GET.get('search', '')
            },
            'total_usuarios': User.objects.count(),
            'usuarios_activos': User.objects.filter(is_active=True).count(),
            'usuarios_inactivos': User.objects.filter(is_active=False).count(),
        })

        return context

class SecretarioRecursosView(SecretarioRequiredMixin, TemplateView):
    """Gestión de recursos"""
    template_name = 'secretario/recursos/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recursos'] = []
        return context


class SecretarioMonitoreoView(SecretarioRequiredMixin, TemplateView):
    """Monitoreo del sistema"""
    template_name = 'secretario/monitoreo/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['metricas'] = ServicioMonitoreo.obtener_metricas_rendimiento()
        context['alertas'] = ServicioMonitoreo.obtener_alertas_activas()
        return context


class CargarDocumentosView(SecretarioRequiredMixin, TemplateView):
    """Vista principal para cargar documentos"""
    template_name = 'secretario/cargar_documentos/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener todos los cursos con sus docentes
        cursos_docentes = []
        # Uso de select_related y prefetch_related para reducir consultas
        courses = Course.objects.all().prefetch_related(
            'coursegroup_set__teacher__user',
            'coursegroup_set__horarios__aula'
        )

        for course in courses:
            for group in course.coursegroup_set.all():
                teacher = group.teacher
                # Prepara los strings de aula y horario
                aulas = ', '.join([h.aula.codigo for h in group.horarios.all() if h.aula]) if group.horarios.exists() else '-'
                horario_str = ', '.join([
                    f"{h.dia_semana[:3].upper()} {h.hora_inicio.strftime('%H:%M')}-{h.hora_fin.strftime('%H:%M')}"
                    for h in group.horarios.all()
                ]) if group.horarios.exists() else '-'

                cursos_docentes.append({
                    'codigo': course.code,
                    'asignatura': course.name,
                    'grupo': group.group_code,
                    'docente_nombre': teacher.user.get_full_name() if teacher and teacher.user else '-',
                    'docente_email': teacher.user.institutional_email if teacher and teacher.user else '-',
                    'aula': aulas,
                    'horario': horario_str
                })

        context['cursos_docentes'] = cursos_docentes
        return context


@login_required
@require_POST
def cargar_cursos_docentes(request):
    """Procesa el PDF de cursos y docentes"""
    if not request.user.is_secretary(): # Si NO es secretario, deniega
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:cargar_documentos')
    
    pdf_file = request.FILES.get('pdf_file')
    if not pdf_file or not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Debe seleccionar un archivo PDF válido.')
        return redirect('secretario:cargar_documentos')

    # Patrón flexible para capturar: Nro Codigo Asignatura Ciclo Grupo Alum Docente Email
    PATTERN = r'^\s*(\d+)\s+(\d+)\s+(.+?)\s+([A-F])\s+([A-F])\s+(\d+)\s+(.+?)\s+([\w\-]+@unsa\.edu\.pe)'
    DEFAULT_PERIOD_NAME = "2025-I"

    grupos_creados = 0
    profesores_nuevos = 0
    lineas_procesadas = 0
    redirect_url = redirect('secretario:cargar_documentos')

    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        # Concatenar el texto de todas las páginas de forma segura
        text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        lines = text.split('\n')

        with transaction.atomic():
            period, _ = AcademicPeriod.objects.get_or_create(
                name=DEFAULT_PERIOD_NAME,
                defaults={
                    "is_active": True,
                    "start_date": "2025-03-01",
                    "end_date": "2025-07-30"
                }
            )

            for line in lines:
                match = re.search(PATTERN, line)
                if match:
                    try:
                        _, codigo_curso, nombre_curso, _, grupo, _, docente_nombre, email = match.groups()

                        # Limpiar y Normalizar datos
                        nombre_curso = nombre_curso.strip()
                        docente_nombre = docente_nombre.strip()
                        email = email.strip().lower()
                        password_plain = email.split('@')[0]
                        codigo_curso = codigo_curso.strip()
                        grupo = grupo.strip()

                        # 1. CREAR CURSO
                        course, _ = Course.objects.get_or_create(
                            code=codigo_curso,
                            defaults={
                                'name': nombre_curso,
                                'credits': 4,
                                'theory_hours': 2,
                                'practice_hours': 2,
                                'is_active': True
                            }
                        )

                        # 2. CREAR PROFESOR
                        if ',' in docente_nombre:
                            apellidos = docente_nombre.split(',')[0].strip()
                            nombres = docente_nombre.split(',', 1)[1].strip() or 'Profesor'
                        else:
                            partes = docente_nombre.split()
                            nombres = partes[0] if partes else 'Profesor'
                            apellidos = ' '.join(partes[1:]) if len(partes) > 1 else 'Docente'

                        user, user_created = User.objects.get_or_create(
                            institutional_email=email,
                            defaults={
                                'first_name': nombres[:30],
                                'last_name': apellidos[:30],
                                'role': 'teacher',                                
                                'password': make_password(password_plain),
                                'is_active': True
                            }
                        )

                        if user_created:
                            profesores_nuevos += 1

                        teacher, _ = Teacher.objects.get_or_create(
                            user=user,
                            defaults={
                                'teacher_code': password_plain,
                                'department': 'Ciencia de la Computación'
                            }
                        )

                        # 3. CREAR GRUPO Y ASIGNAR PROFESOR
                        course_group, group_created = CourseGroup.objects.get_or_create(
                            course=course,
                            academic_period=period,
                            group_code=grupo,
                            defaults={
                                'capacity': 50,
                                'teacher': teacher
                            }
                        )

                        if not group_created and course_group.teacher != teacher:
                            course_group.teacher = teacher
                            course_group.save(update_fields=['teacher'])

                        if group_created:
                            grupos_creados += 1

                        lineas_procesadas += 1

                    except Exception as e:
                        # Error de fila específica
                        print(f"Error en línea: {line}: {str(e)}")
                        continue

        messages.success(request, f'Procesado: {lineas_procesadas} cursos, {grupos_creados} grupos creados, {profesores_nuevos} profesores nuevos')

    except Exception as e:
        messages.error(request, f'Error al procesar PDF: {str(e)}')

    return redirect_url


@login_required
@require_POST
def cargar_horarios(request):
    """Procesa el PDF de horarios (por aula, día y curso)"""
    if not request.user.is_secretary():        
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:cargar_documentos')

    pdf_file = request.FILES.get('pdf_file')
    if not pdf_file or not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Debe seleccionar un archivo PDF válido.')
        return redirect('secretario:cargar_documentos')

    horarios_creados = 0
    aulas_creadas = 0
    redirect_url = redirect('secretario:cargar_documentos')
    DEFAULT_PERIOD_NAME = "2025-I"

    def _limpiar_texto_local(txt: str) -> str:
        """Limpia caracteres dañados, tildes y convierte a mayúsculas uniformes"""
        if not txt:
            return ""
        txt = unicodedata.normalize("NFKD", txt)
        txt = txt.encode("ASCII", "ignore").decode("utf-8", errors="ignore")
        txt = re.sub(r"[^A-Z0-9\s,.\-]", " ", txt.upper())
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    try:
        with transaction.atomic():
            period = AcademicPeriod.objects.get(name=DEFAULT_PERIOD_NAME)
            course_map = {
                _limpiar_texto_local(c.name): c
                for c in Course.objects.all()
            }
            nombres_db_limpios = list(course_map.keys())

            with pdfplumber.open(pdf_file) as pdf:
                aula_actual = None
                for page in pdf.pages:
                    texto = page.extract_text() or ""
                    lineas = texto.split('\n')

                    for linea in lineas:
                        linea = linea.strip()
                        if not linea: continue

                        # 1️⃣ Detectar AULA
                        if linea.upper().startswith('AULA:'):
                            nombre_aula = linea.split(':', 1)[-1].strip()[:100]
                            aula_actual, creada = Aula.objects.get_or_create(
                                codigo=nombre_aula,
                                defaults={"nombre": nombre_aula, "capacidad": 40, "tipo": "teoria"}
                            )
                            if creada: aulas_creadas += 1
                            continue

                        # 2️⃣ Detectar línea de horario
                        if re.match(r'^(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO)', linea.upper()):
                            if not aula_actual: continue
                            try:
                                partes = re.split(r'\s+', linea)
                                dia = partes[0].lower()
                                horas_match = re.search(r'(\d{2}:\d{2})/(\d{2}:\d{2})', linea)
                                if not horas_match: continue
                                hora_ini, hora_fin = horas_match.groups()
                                resto = linea.split(horas_match.group(0), 1)[-1].strip()

                                match_curso_grupo = re.match(r'(.+?)\s*\(([A-F])\)', resto)
                                if not match_curso_grupo:
                                    continue
                                nombre_curso, grupo = match_curso_grupo.groups()

                                # BÚSQUEDA DIFUSA
                                nombre_curso_limpio = _limpiar_texto_local(nombre_curso)
                                coincidencias = difflib.get_close_matches(nombre_curso_limpio, nombres_db_limpios, n=1, cutoff=0.7)

                                if not coincidencias:
                                    continue

                                course = course_map.get(coincidencias[0])
                                if not course: continue

                                cg, _ = CourseGroup.objects.get_or_create(
                                    course=course,
                                    academic_period=period,
                                    group_code=grupo,
                                    defaults={"capacity": 50}
                                )

                                hora_inicio = datetime.strptime(hora_ini, "%H:%M").time()
                                hora_fin = datetime.strptime(hora_fin, "%H:%M").time()

                                _, creado = Horario.objects.get_or_create(
                                    course_group=cg,
                                    aula=aula_actual,
                                    dia_semana=dia,
                                    hora_inicio=hora_inicio,
                                    hora_fin=hora_fin
                                )

                                if creado:
                                    horarios_creados += 1

                            except Exception as e:
                                print(f"Error procesando línea: {linea}\nMotivo: {e}")
                                continue

        messages.success(request, f"{horarios_creados} horarios creados, {aulas_creadas} aulas nuevas")

    except AcademicPeriod.DoesNotExist:
        messages.error(request, f"Error: El período '{DEFAULT_PERIOD_NAME}' no existe.")
    except Exception as e:
        messages.error(request, f"Error general en la carga de horarios: {e}")

    return redirect_url

@login_required
@require_POST
def cargar_estudiantes(request):
    """Procesa Excel de estudiantes y los matricula"""
    if not request.user.is_secretary():        
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:cargar_documentos')

    excel_file = request.FILES.get('excel_file')
    if not excel_file or not excel_file.name.lower().endswith(('.xlsx', '.xls')):
        messages.error(request, 'Debe seleccionar un archivo Excel válido.')
        return redirect('secretario:cargar_documentos')

    estudiantes_creados = 0
    matriculas_creadas = 0
    redirect_url = redirect('secretario:cargar_documentos')
    DEFAULT_PERIOD_NAME = "2025-I"

    try:
        with transaction.atomic():
            period = AcademicPeriod.objects.get(name=DEFAULT_PERIOD_NAME)

            # Leer Excel
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            # --- 1. DETECTAR ASIGNATURA Y GRUPO del Excel ---
            asignatura_cell = None
            grupo_cell = None
            for row in ws.iter_rows(min_row=1, max_row=10, values_only=True):
                row_text = ' '.join(str(cell) for cell in row if cell).upper()
                if 'ASIGNATURA' in row_text:
                    match_asig = re.search(r'ASIGNATURA\s*:\s*(.+)', row_text, re.IGNORECASE)
                    if match_asig: asignatura_cell = match_asig.group(1).strip()
                if 'GRUPO' in row_text:
                    match_grupo = re.search(r'GRUPO\s*:\s*([A-Z0-9])', row_text, re.IGNORECASE)
                    if match_grupo: grupo_cell = match_grupo.group(1).strip().upper()

            if not asignatura_cell or not grupo_cell:
                messages.error(request, 'No se pudo detectar la asignatura o grupo del Excel.')
                return redirect_url

            course_excel = Course.objects.filter(name__icontains=asignatura_cell[:30]).first()
            if not course_excel:
                messages.error(request, f'Curso "{asignatura_cell}" no encontrado en el sistema.')
                return redirect_url

            group_excel = CourseGroup.objects.get(
                course=course_excel, group_code=grupo_cell, academic_period=period
            )

            profesor_excel = group_excel.teacher
            if not profesor_excel:
                messages.error(request, f'El grupo {grupo_cell} del curso {asignatura_cell} no tiene profesor asignado.')
                return redirect_url

            grupos_a_profesor = CourseGroup.objects.filter(
                academic_period=period, group_code='A', teacher=profesor_excel
            )

            # --- 2. ENCONTRAR CABECERA DE DATOS ---
            header_row_index = None
            for idx, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=True), start=1):
                row_text = ' '.join(str(cell).upper() for cell in row if cell)
                if 'CUI' in row_text and ('APELLIDOS' in row_text or 'NOMBRES' in row_text):
                    header_row_index = idx
                    break

            if not header_row_index:
                messages.error(request, 'No se encontró el encabezado de datos (CUI, APELLIDOS, NOMBRES).')
                return redirect_url

            # --- 3. PROCESAR ESTUDIANTES ---
            for row in ws.iter_rows(min_row=header_row_index + 1, values_only=True):
                try:
                    if len(row) < 3 or not row[1] or not row[2]: continue

                    cui = str(row[1]).strip()
                    apellidos_nombres = str(row[2]).strip()
                    apellidos_nombres = apellidos_nombres.replace('/', ' ')
                    if not cui or cui.upper() == 'NONE': continue

                    if ',' in apellidos_nombres:
                        apellidos, nombres = apellidos_nombres.split(',', 1)
                        apellidos = apellidos.strip()
                        nombres = nombres.strip()
                    else:
                        partes = apellidos_nombres.split()
                        apellidos = ' '.join(partes[:2]) if len(partes) > 1 else apellidos_nombres
                        nombres = ' '.join(partes[2:]) if len(partes) > 2 else 'Estudiante'

                    email = f"{cui}@unsa.edu.pe"
                    password_default = cui

                    # Crear Usuario
                    user, user_created = User.objects.get_or_create(
                        institutional_email=email,
                        defaults={
                            'first_name': nombres[:30],
                            'last_name': apellidos[:30],
                            'role': 'student',                            
                            'password': make_password(password_default),
                            'is_active': True
                        }
                    )

                    # Crear Estudiante
                    student, student_created = Student.objects.get_or_create(
                        user=user,
                        defaults={
                            'student_code': cui,
                            'career': 'Ciencia de la Computación',
                            'current_cycle': 1,
                            'academic_status': 'active'
                        }
                    )
                    if student_created: estudiantes_creados += 1

                    # 1. Matricular en el curso específico del Excel
                    _, created_excel = Enrollment.objects.get_or_create(
                        student=student, course_group=group_excel, academic_period=period,
                        defaults={'enrollment_type': 'regular', 'status': 'active'}
                    )
                    if created_excel: matriculas_creadas += 1

                    # 2. Matricular en cursos grupo 'A' del mismo profesor
                    for grupo_a in grupos_a_profesor:
                        _, created_a = Enrollment.objects.get_or_create(
                            student=student, course_group=grupo_a, academic_period=period,
                            defaults={'enrollment_type': 'regular', 'status': 'active'}
                        )
                        if created_a: matriculas_creadas += 1

                except Exception as e:
                    print(f"Error procesando estudiante (CUI: {cui if 'cui' in locals() else 'N/A'}): {e}")
                    continue

        messages.success(request, f'{estudiantes_creados} estudiantes nuevos, {matriculas_creadas} matrículas')

    except AcademicPeriod.DoesNotExist:
        messages.error(request, f"Error: El período '{DEFAULT_PERIOD_NAME}' no existe.")
    except CourseGroup.DoesNotExist:
        messages.error(request, f'Error: El grupo {grupo_cell} del curso {asignatura_cell} no fue encontrado.')
    except Exception as e:
        messages.error(request, f'Error general en la carga de estudiantes: {e}')

    return redirect_url