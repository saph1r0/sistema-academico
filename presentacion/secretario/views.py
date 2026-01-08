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
from xhtml2pdf import pisa

# 3. Importaciones de Django
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.views.generic import TemplateView
from django.db import transaction
from django.db.models import Q
from django.template.loader import get_template

# 4. Importaciones de la Aplicación (Modelos y Servicios)
from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod, Aula, Horario,Laboratory, Student, Enrollment,Classroom
)
from .mixins import SecretarioRequiredMixin
from servicios.servicioMatriculaLaboratorio import ServicioMatriculaLaboratorio, servicio_matricula_laboratorio
from servicios.servicioReservas import servicio_reservas
from servicios.servicioReportes import ServicioReportes
from servicios.servicioMonitoreo import ServicioMonitoreo
# Servicios de Reportes Específicos
from servicios.servicioReporteAsistencia import ServicioReporteAsistencia
from servicios.servicioReporteNotas import ServicioReporteNotas

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

        # Período activo
        current_period = AcademicPeriod.objects.filter(is_active=True).first()

        # Contadores principales
        context['total_teachers'] = Teacher.objects.count()
        context['total_students'] = Student.objects.count()
        context['total_courses'] = Course.objects.count()

        # Alertas simples: labs sin docente
        context['alerts_count'] = Laboratory.objects.filter(
            teacher__isnull=True
        ).count()

        # Profesores para el panel (máx 5)
        teachers = Teacher.objects.select_related('user')[:5]
        context['teachers_stats'] = [
            {
                'teacher': t,
                'courses_count': CourseGroup.objects.filter(teacher=t).count(),
                'hours_per_week': Horario.objects.filter(
                    laboratory__teacher=t
                ).count(),
                'status': 'activo' if t.user.is_active else 'inactivo',
                'virtual_percentage': 0
            }
            for t in teachers
        ]

        # Alertas del sistema (placeholder compatible con el HTML)
        context['system_alerts'] = []

        # Usuarios conectados (simple)
        context['active_users'] = User.objects.filter(is_active=True).count()

        context['current_period'] = current_period

        return context


class SecretarioReportesView(SecretarioRequiredMixin, TemplateView):
    """Generación de reportes académicos y actas"""
    template_name = 'secretario/reportes/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Importamos los formularios aquí para evitar referencias circulares
        from .forms import ReporteAsistenciaForm, ReporteNotasForm, ReporteEstadisticasForm
        
        context.update({
            'page_title': 'Generación de Reportes y Actas',
            'form_asistencia': ReporteAsistenciaForm(),
            'form_notas': ReporteNotasForm(),
            'form_estadisticas': ReporteEstadisticasForm(),
        })
        return context

    def _render_pdf(self, template_src, context_dict, filename='reporte.pdf'):
        """Función auxiliar para generar PDF"""
        template = get_template(template_src)
        html = template.render(context_dict)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse(f'Error generando PDF: {pisa_status.err}')
        return response

    def post(self, request, *args, **kwargs):
        from .forms import ReporteAsistenciaForm, ReporteNotasForm, ReporteEstadisticasForm
        
        categoria = request.POST.get('categoria_reporte')
        
        try:
            # 1. REPORTE DE ASISTENCIA
            if categoria == 'asistencia':
                form = ReporteAsistenciaForm(request.POST)
                if form.is_valid():
                    filtros = form.cleaned_data
                    servicio = ServicioReporteAsistencia()
                    data_pdf = servicio.generar_data_reporte(filtros)
                    
                    if not data_pdf or not data_pdf.get('tablas'):
                        messages.warning(request, "No se encontraron registros de asistencia.")
                        return redirect('secretario:reportes')

                    # Reutilizamos el template visual (asegúrate de que la ruta sea accesible)
                    return self._render_pdf('administrador/reportes/reporte_asistencia.html', {
                        'reporte': data_pdf
                    }, filename=f"Reporte_Asistencia_{filtros['tipo_reporte']}.pdf")
                else:
                    self._mostrar_errores(request, form)

            # 2. REPORTE DE NOTAS
            elif categoria == 'notas':
                form = ReporteNotasForm(request.POST)
                if form.is_valid():
                    filtros = form.cleaned_data
                    servicio = ServicioReporteNotas()
                    data_pdf = servicio.generar_data_reporte_oficial(filtros)
                    
                    if not data_pdf or not data_pdf.get('tablas'):
                        messages.warning(request, "No se encontraron notas con esos filtros.")
                        return redirect('secretario:reportes')

                    return self._render_pdf('administrador/reportes/acta_notas.html', {
                        'reporte': data_pdf,
                        'headers': ['CUI', 'ALUMNO', 'NOTA FINAL', 'ESTADO']
                    }, filename=f"Acta_Notas_{filtros['tipo_reporte']}.pdf")
                else:
                    self._mostrar_errores(request, form)

            # 3. ESTADÍSTICAS
            elif categoria == 'estadisticas':
                form = ReporteEstadisticasForm(request.POST)
                if form.is_valid():
                    servicio = ServicioReportes()
                    # Este servicio retorna el PDF response directamente
                    return servicio.generar_reporte_estadisticas_global(
                        periodo=form.cleaned_data['periodo'],
                        fecha_inicio=form.cleaned_data['fecha_inicio'],
                        fecha_fin=form.cleaned_data['fecha_fin'],
                        formato='pdf',
                        incluir_graficos=True
                    )
                else:
                    self._mostrar_errores(request, form)

            else:
                messages.error(request, 'Tipo de reporte no válido.')

        except Exception as e:
            messages.error(request, f'Error al generar reporte: {str(e)}')

        return redirect('secretario:reportes')

    def _mostrar_errores(self, request, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")


class SecretarioEstadisticasView(SecretarioRequiredMixin, TemplateView):
    """Vista de estadísticas académicas"""
    template_name = 'secretario/estadisticas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'estadisticas_matricula': ServicioMatriculaLaboratorio.obtener_estadisticas_matricula(),
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
    DEFAULT_PERIOD_NAME = "2025-II"

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
                    "start_date": "2025-09-01",
                    "end_date": "2025-12-31"
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
    DEFAULT_PERIOD_NAME = "2025-II"

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
                            if creada:
                                Classroom.objects.get_or_create(
                                    code=nombre_aula[:20],
                                    defaults={
                                        "name": nombre_aula,
                                        "room_type": "teoria",
                                        "capacity": 40,
                                        "equipment": "",
                                        "location": "",
                                        "is_active": True,
                                    }
                                )
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
    """
    Procesa Excel de estudiantes. 
    Identifica el CURSO por el CÓDIGO en el nombre del archivo.
    Identifica el GRUPO en el contenido del archivo Excel.
    """
    if not request.user.is_secretary():        
        messages.error(request, 'No tienes permisos.')
        return redirect('secretario:cargar_documentos')

    excel_file = request.FILES.get('excel_file')
    if not excel_file or not excel_file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
        messages.error(request, 'Debe seleccionar un archivo Excel o CSV válido.')
        return redirect('secretario:cargar_documentos')

    estudiantes_creados = 0
    matriculas_creadas = 0
    redirect_url = redirect('secretario:cargar_documentos')
    DEFAULT_PERIOD_NAME = "2025-II"
    
    # --------------------------------------------------------------------------
    # PASO 1: EXTRACCIÓN DEL CÓDIGO DEL CURSO DESDE EL NOMBRE DEL ARCHIVO
    # --------------------------------------------------------------------------
    file_name = excel_file.name.upper()
    
    # Patrón para capturar el Código (6 o 7 dígitos)
    # Buscamos la última secuencia de dígitos que podría ser el código, antes de la extensión.
    PATTERN_CODIGO = r'(\d{6,7})[_\.]' 
    
    match_data = list(re.finditer(PATTERN_CODIGO, file_name))
    
    if not match_data:
        messages.error(
            request, 
            f'Error: El nombre del archivo no contiene el CÓDIGO del curso (ej: 1705267).'
        )
        return redirect_url

    # Usar la última coincidencia encontrada (la más cercana al final del nombre)
    codigo_curso_file = match_data[-1].group(1)
    
    # Inicializar variables para el manejo de errores
    grupo_cell = None 
    
    try:
        with transaction.atomic():
            period = AcademicPeriod.objects.get(name=DEFAULT_PERIOD_NAME)

            # Leer Excel
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active

            # --------------------------------------------------------------------------
            # PASO 2: EXTRACCIÓN DEL GRUPO DESDE EL CONTENIDO DEL EXCEL
            # --------------------------------------------------------------------------
            for row in ws.iter_rows(min_row=1, max_row=10, values_only=True):
                row_text = ' '.join(str(cell) for cell in row if cell).upper()
                if 'GRUPO' in row_text:
                    match_grupo = re.search(r'GRUPO\s*:\s*([A-Z0-9])', row_text, re.IGNORECASE)
                    if match_grupo: 
                        grupo_cell = match_grupo.group(1).strip().upper()
                        break # Salir del bucle una vez que el grupo es encontrado

            if not grupo_cell:
                messages.error(request, 'No se pudo detectar el Grupo del Excel. Asegúrese de que aparezca "GRUPO: [A|B|C]" en las primeras filas.')
                return redirect_url
            
            # --------------------------------------------------------------------------
            # PASO 3: BÚSQUEDA DEL CURSO Y GRUPO POR CÓDIGO (Infallible)
            # --------------------------------------------------------------------------
            try:
                # 1. Buscar el Curso por el código extraído
                course_excel = Course.objects.get(code=codigo_curso_file)
            except Course.DoesNotExist:
                messages.error(request, f'Error: Curso con código "{codigo_curso_file}" no encontrado en la BD.')
                return redirect_url

            # 2. Buscar el CourseGroup
            grupos_encontrados = CourseGroup.objects.filter(
                course=course_excel, 
                group_code=grupo_cell, 
                academic_period=period
            )

            if grupos_encontrados.count() == 1:
                group_excel = grupos_encontrados.first()
            else:
                messages.error(
                    request, 
                    f'Error: El grupo {grupo_cell} para "{course_excel.name}" (Cód: {codigo_curso_file}) no fue encontrado en el período {period.name} (o hay duplicados).'
                )
                return redirect_url
            # --------------------------------------------------------------------------

            # --- 4. ENCONTRAR CABECERA DE DATOS (CUI, NOMBRES) ---
            header_row_index = None
            for idx, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=True), start=1):
                row_text = ' '.join(str(cell).upper() for cell in row if cell)
                if 'CUI' in row_text and ('APELLIDOS' in row_text or 'NOMBRES' in row_text):
                    header_row_index = idx
                    break

            if not header_row_index:
                messages.error(request, 'No se encontró el encabezado de datos (CUI, APELLIDOS, NOMBRES).')
                return redirect_url

            # --- 5. PROCESAR ESTUDIANTES ---
            for row in ws.iter_rows(min_row=header_row_index + 1, values_only=True):
                try:
                    # ... (Lógica de extracción de CUI, nombres, y creación de Usuario/Estudiante) ...
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

                    # Matricular en el curso específico del Excel 
                    _, created_excel = Enrollment.objects.get_or_create(
                        student=student, course_group=group_excel, academic_period=period,
                        defaults={'enrollment_type': 'regular', 'status': 'active'}
                    )
                    if created_excel: matriculas_creadas += 1

                except Exception as e:
                    print(f"Error procesando estudiante (CUI: {cui if 'cui' in locals() else 'N/A'}): {e}")
                    continue

        messages.success(request, f'{estudiantes_creados} estudiantes nuevos, {matriculas_creadas} matrículas en {course_excel.name} - {group_excel.group_code}')

    except AcademicPeriod.DoesNotExist:
        messages.error(request, f"Error: El período '{DEFAULT_PERIOD_NAME}' no existe.")
    except Exception as e:
        messages.error(request, f'Error general en la carga de estudiantes: {str(e)}')

    return redirect_url
# =============================================================================
# MONITOR DE NOTAS - VISTAS ADICIONALES
# =============================================================================

from django.views.generic import View
import csv

class SecretarioNotasAlumnosAPIView(SecretarioRequiredMixin, View):
    """API para cargar alumnos dinámicamente según el curso"""
    def get(self, request, *args, **kwargs):
        curso_id = request.GET.get('curso_id')
        if not curso_id:
            return JsonResponse({'error': 'Falta curso_id'}, status=400)
            
        servicio = ServicioReporteNotas()
        alumnos = servicio.obtener_lista_alumnos_curso(curso_id)
        return JsonResponse({'alumnos': alumnos})


class SecretarioNotasEstudiantesView(SecretarioRequiredMixin, TemplateView):
    """Dashboard de monitoreo de notas para secretaría"""
    template_name = 'secretario/notas_estudiantes/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        servicio = ServicioReporteNotas()
        
        context['stats'] = servicio.obtener_dashboard_admin()
        context['lista_cursos'] = CourseGroup.objects.select_related('course').order_by('course__name')

        curso_id = self.request.GET.get('curso_id')
        busqueda = self.request.GET.get('busqueda')
        
        resultados_busqueda = []
        if curso_id or busqueda:
            resultados_busqueda = servicio.buscar_notas_detalladas(curso_id, busqueda)
            
        context['resultados_busqueda'] = resultados_busqueda
        context['filtros_activos'] = {'curso_id': curso_id, 'busqueda': busqueda}
        return context


class ExportarNotasCSVSecretarioView(SecretarioRequiredMixin, View):
    """Exportación de resumen de notas en CSV"""
    def get(self, request, *args, **kwargs):
        servicio = ServicioReporteNotas()
        stats = servicio.obtener_dashboard_admin()
        response = HttpResponse(content_type='text/csv')
        nombre_archivo = f"Resumen_Notas_Sec_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        writer = csv.writer(response)
        writer.writerow(['REPORTE DE NOTAS - RESUMEN GENERAL (SECRETARIA)'])
        writer.writerow(['Fecha:', datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow([]) 
        writer.writerow(['METRICAS GENERALES'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Promedio Ponderado Global', stats['promedio_global']])
        writer.writerow(['Tasa de Aprobacion Global', f"{stats['tasa_aprobacion']}%"])
        writer.writerow(['Total Estudiantes Evaluados', stats['total_evaluados']])
        writer.writerow(['Cantidad Estudiantes en Riesgo', stats['cantidad_riesgo']])
        
        return response