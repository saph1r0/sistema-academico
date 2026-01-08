#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de exportación de reportes de asistencia
Soporta Excel (.xlsx) y PDF con filtros aplicados
"""

from datetime import datetime, timedelta
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.utils import timezone

# Para Excel
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from repositorio.postgres_repository.models import (
    SimpleAttendanceRecord, Student, CourseGroup, 
    Enrollment, AcademicPeriod
)

TH_FILL = PatternFill("solid", fgColor="EEEEEE")   # gris claro
TH_FONT = Font(bold=True, size=10)
TD_FONT = Font(size=9)

CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center")

BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

def es_admin_o_secretaria(user):
   
    return True 


# =============================================================================
# EXPORTACIÓN A EXCEL - DASHBOARD GENERAL
# =============================================================================

@login_required
@user_passes_test(es_admin_o_secretaria)
def exportar_dashboard_excel(request):
    """
    Exporta el dashboard general de asistencia a Excel
    Incluye: métricas generales, estudiantes en riesgo, top cursos
    """
    # Obtener parámetros de filtro
    curso_id = request.GET.get('curso')
    estudiante_id = request.GET.get('estudiante')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Parsear fechas
    if not fecha_inicio:
        fecha_inicio = (timezone.now().date() - timedelta(days=30))
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Crear workbook
    wb = Workbook()
    
    # Hoja 1: Resumen General
    ws1 = wb.active
    ws1.title = "Resumen General"
    _crear_hoja_resumen_general(ws1, fecha_inicio, fecha_fin, curso_id, estudiante_id)
    
    # Hoja 2: Estudiantes en Riesgo
    ws2 = wb.create_sheet("Estudiantes en Riesgo")
    _crear_hoja_estudiantes_riesgo(ws2, fecha_inicio, fecha_fin)
    
    # Hoja 3: Top Cursos
    ws3 = wb.create_sheet("Top Cursos")
    _crear_hoja_top_cursos(ws3, fecha_inicio, fecha_fin)
    
    # Preparar respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'reporte_asistencia_general_{fecha_inicio}_{fecha_fin}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response


def _crear_hoja_resumen_general(ws, fecha_inicio, fecha_fin, curso_id, estudiante_id):
    """Crea la hoja de resumen general con métricas"""
    
    # Estilos
    header_fill = PatternFill(start_color="1E2125", end_color="1E2125", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    title_font = Font(bold=True, size=16)
    
    # Título
    ws['A1'] = 'REPORTE DE ASISTENCIA - RESUMEN GENERAL'
    ws['A1'].font = title_font
    ws.merge_cells('A1:F1')
    
    # Información del reporte
    ws['A3'] = f'Período: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}'
    ws['A4'] = f'Fecha de generación: {timezone.now().strftime("%d/%m/%Y %H:%M")}'
    
    # Obtener datos
    asistencias = SimpleAttendanceRecord.objects.filter(
        class_date__gte=fecha_inicio,
        class_date__lte=fecha_fin
    )
    
    if curso_id:
        asistencias = asistencias.filter(course_group_id=curso_id)
    if estudiante_id:
        asistencias = asistencias.filter(student_id=estudiante_id)
    
    total_registros = asistencias.count()
    total_presentes = asistencias.filter(status='PRESENTE').count()
    total_faltas = asistencias.filter(status='FALTA').count()
    tasa_global = (total_presentes / total_registros * 100) if total_registros > 0 else 0
    
    # Métricas
    ws['A7'] = 'MÉTRICAS GENERALES'
    ws['A7'].font = Font(bold=True, size=14)
    
    headers = ['Métrica', 'Valor']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=header)
        cell.fill = TH_FILL
        cell.font = TH_FONT
        cell.alignment = CENTER
        cell.border = BORDER
    
    metricas = [
        ['Total de Registros', total_registros],
        ['Total Presentes', total_presentes],
        ['Total Faltas', total_faltas],
        ['Tasa de Asistencia Global', f'{tasa_global:.1f}%'],
        ['Estudiantes Únicos', asistencias.values('student').distinct().count()],
        ['Cursos Activos', asistencias.values('course_group').distinct().count()],
    ]
    
    for row, (metrica, valor) in enumerate(metricas, start=9):
        ws.cell(row=row, column=1, value=metrica)
        ws.cell(row=row, column=2, value=valor)
    
    # Ajustar anchos de columna
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20


def _crear_hoja_estudiantes_riesgo(ws, fecha_inicio, fecha_fin):
    """Crea la hoja de estudiantes en riesgo"""
    
    # Estilos
    header_fill = PatternFill( start_color="1E2125",end_color="1E2125", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    alert_fill = PatternFill(start_color="FFFFFF",end_color="FFFFFF",fill_type="solid")
    
    # Título
    ws['A1'] = 'ESTUDIANTES EN RIESGO (>20% INASISTENCIAS)'
    ws['A1'].font = Font(bold=True, size=14, color="C00000")
    ws.merge_cells('A1:F1')
    
    # Headers
    headers = ['Código', 'Nombre', 'Email', 'Total Clases', 'Faltas', '% Faltas', 'Cursos con Problema']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=header)
        cell.fill = TH_FILL
        cell.font = TH_FONT
        cell.alignment = CENTER
        cell.border = BORDER
    
    # Obtener estudiantes en riesgo
    estudiantes_riesgo = []
    students = Student.objects.filter(enrollment__status='active').distinct()
    
    for student in students:
        registros = SimpleAttendanceRecord.objects.filter(
            student=student,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total = registros.count()
        if total == 0:
            continue
        
        faltas = registros.filter(status='FALTA').count()
        porcentaje_faltas = (faltas / total * 100)
        
        if porcentaje_faltas > 20:
            # Contar cursos con problemas
            enrollments = Enrollment.objects.filter(student=student, status='active')
            cursos_problema = 0
            
            for enrollment in enrollments:
                regs_curso = SimpleAttendanceRecord.objects.filter(
                    student=student,
                    course_group=enrollment.course_group,
                    class_date__gte=fecha_inicio,
                    class_date__lte=fecha_fin
                )
                total_curso = regs_curso.count()
                if total_curso > 0:
                    faltas_curso = regs_curso.filter(status='FALTA').count()
                    if (faltas_curso / total_curso * 100) > 20:
                        cursos_problema += 1
            
            estudiantes_riesgo.append({
                'codigo': student.student_code,
                'nombre': student.user.get_full_name(),
                'email': student.user.institutional_email,
                'total': total,
                'faltas': faltas,
                'porcentaje': porcentaje_faltas,
                'cursos_problema': cursos_problema,
            })
    
    # Ordenar por porcentaje de faltas
    estudiantes_riesgo.sort(key=lambda x: x['porcentaje'], reverse=True)
    
    # Llenar datos
    for row, est in enumerate(estudiantes_riesgo, start=4):
        ws.cell(row=row, column=1, value=est['codigo'])
        ws.cell(row=row, column=2, value=est['nombre'])
        ws.cell(row=row, column=3, value=est['email'])
        ws.cell(row=row, column=4, value=est['total'])
        ws.cell(row=row, column=5, value=est['faltas'])
        ws.cell(row=row, column=6, value=f"{est['porcentaje']:.1f}%")
        ws.cell(row=row, column=7, value=est['cursos_problema'])
        
        # Aplicar color de alerta a la fila
        for col in range(1, 8):
            ws.cell(row=row, column=col).fill = alert_fill
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 18


def _crear_hoja_top_cursos(ws, fecha_inicio, fecha_fin):
    """Crea la hoja de top cursos por asistencia"""
    
    # EstilE2125
    header_font = Font(color="FFFFFF", bold=True)
    
    # Título
    ws['A1'] = 'TOP CURSOS POR ASISTENCIA'
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:F1')
    
    # Headers
    headers = ['Código', 'Curso', 'Grupo', 'Profesor', 'Total Registros', '% Asistencia']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=header)
        cell.fill = TH_FILL
        cell.font = TH_FONT
        cell.alignment = CENTER
        cell.border = BORDER
    
    # Obtener datos
    cursos = CourseGroup.objects.select_related('course', 'teacher__user')
    cursos_stats = []
    
    for curso in cursos:
        registros = SimpleAttendanceRecord.objects.filter(
            course_group=curso,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total = registros.count()
        if total == 0:
            continue
        
        presentes = registros.filter(status='PRESENTE').count()
        porcentaje = (presentes / total * 100)
        
        cursos_stats.append({
            'codigo': curso.course.code,
            'nombre': curso.course.name,
            'grupo': curso.group_code,
            'profesor': curso.teacher.user.get_full_name() if curso.teacher else 'Sin asignar',
            'total': total,
            'porcentaje': porcentaje,
        })
    
    # Ordenar por porcentaje
    cursos_stats.sort(key=lambda x: x['porcentaje'], reverse=True)
    
    # Llenar datos (top 20)
    for row, curso in enumerate(cursos_stats[:20], start=4):
        ws.cell(row=row, column=1, value=curso['codigo'])
        ws.cell(row=row, column=2, value=curso['nombre'])
        ws.cell(row=row, column=3, value=curso['grupo'])
        ws.cell(row=row, column=4, value=curso['profesor'])
        ws.cell(row=row, column=5, value=curso['total'])
        ws.cell(row=row, column=6, value=f"{curso['porcentaje']:.1f}%")
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15


# =============================================================================
# EXPORTACIÓN A EXCEL - REPORTE POR CURSO
# =============================================================================

@login_required
@user_passes_test(es_admin_o_secretaria)
def exportar_curso_excel(request, curso_id):
    """Exporta el reporte detallado de un curso a Excel"""
    
    try:
        curso = CourseGroup.objects.select_related(
            'course', 'teacher__user', 'academic_period'
        ).get(id=curso_id)
    except CourseGroup.DoesNotExist:
        return HttpResponse('Curso no encontrado', status=404)
    
    # Fechas
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio:
        fecha_inicio = curso.academic_period.start_date
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia por Curso"
    
    # Estilos
    title_font = Font(bold=True, size=1E2125)
    header_font = Font(color="FFFFFF", bold=True)
    
    # Título
    ws['A1'] = f'REPORTE DE ASISTENCIA - {curso.course.name}'
    ws['A1'].font = title_font
    ws.merge_cells('A1:H1')
    
    # Información del curso
    ws['A3'] = f'Código: {curso.course.code}'
    ws['A4'] = f'Grupo: {curso.group_code}'
    ws['A5'] = f'Profesor: {curso.teacher.user.get_full_name() if curso.teacher else "Sin asignar"}'
    ws['A6'] = f'Período: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}'
    
    # Headers
    headers = ['Código', 'Estudiante', 'Email', 'Total Clases', 'Presentes', 'Faltas', '% Asistencia', 'Estado']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=header)
        cell.fill = TH_FILL
        cell.font = TH_FONT
        cell.alignment = CENTER
        cell.border = BORDER
    
    # Obtener estudiantes
    enrollments = Enrollment.objects.filter(
        course_group=curso,
        status='active'
    ).select_related('student__user')
    
    estudiantes_data = []
    
    for enrollment in enrollments:
        student = enrollment.student
        registros = SimpleAttendanceRecord.objects.filter(
            student=student,
            course_group=curso,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total = registros.count()
        presentes = registros.filter(status='PRESENTE').count()
        faltas = registros.filter(status='FALTA').count()
        porcentaje = (presentes / total * 100) if total > 0 else 0
        porcentaje_faltas = (faltas / total * 100) if total > 0 else 0
        
        estado = 'Normal'
        if porcentaje_faltas > 30:
            estado = 'Crítico'
        elif porcentaje_faltas > 20:
            estado = 'Riesgo'
        elif porcentaje_faltas > 10:
            estado = 'Alerta'
        
        estudiantes_data.append({
            'codigo': student.student_code,
            'nombre': student.user.get_full_name(),
            'email': student.user.institutional_email,
            'total': total,
            'presentes': presentes,
            'faltas': faltas,
            'porcentaje': porcentaje,
            'estado': estado,
        })
    
    # Ordenar por porcentaje de faltas
    estudiantes_data.sort(key=lambda x: x['porcentaje'])
    
    # Llenar datos
    for row, est in enumerate(estudiantes_data, start=9):
        ws.cell(row=row, column=1, value=est['codigo'])
        ws.cell(row=row, column=2, value=est['nombre'])
        ws.cell(row=row, column=3, value=est['email'])
        ws.cell(row=row, column=4, value=est['total'])
        ws.cell(row=row, column=5, value=est['presentes'])
        ws.cell(row=row, column=6, value=est['faltas'])
        ws.cell(row=row, column=7, value=f"{est['porcentaje']:.1f}%")
        ws.cell(row=row, column=8, value=est['estado'])
        
        fill = PatternFill(
            start_color="FFFFFF",
            end_color="FFFFFF",
            fill_type="solid"
        )
        for col in range(1, 9):
            cell = ws.cell(row=row, column=col)
            cell.font = TD_FONT
            cell.alignment = CENTER
            cell.border = BORDER
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 12
    
    # Respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'reporte_curso_{curso.course.code}_{fecha_inicio}_{fecha_fin}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response


def es_admin_o_secretaria(user):
    return user.is_staff or user.groups.filter(name__in=['Secretaria', 'Administrador']).exists()


@login_required
@user_passes_test(es_admin_o_secretaria)
def exportar_estudiante_excel(request, estudiante_id):
    """Exporta el reporte detallado de un estudiante a Excel"""
    
    try:
        student = Student.objects.select_related('user').get(id=estudiante_id)
    except Student.DoesNotExist:
        return HttpResponse('Estudiante no encontrado', status=404)
    
    # Fechas
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio:
        fecha_inicio = (timezone.now().date() - timedelta(days=30))
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia por Estudiante"
    
    # Estilos
    title_font = Font(bold=True, size=1E2125)
    header_font = Font(color="FFFFFF", bold=True)
    
    # Título
    ws['A1'] = f'REPORTE DE ASISTENCIA - {student.user.get_full_name()}'
    ws['A1'].font = title_font
    ws.merge_cells('A1:H1')
    
    # Información del estudiante
    ws['A3'] = f'Código: {student.student_code}'
    ws['A4'] = f'Email: {student.user.institutional_email}'
    ws['A5'] = f'Período: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}'
    
    # Calcular estadísticas globales
    total_clases_global = 0
    total_presentes_global = 0
    total_faltas_global = 0
    
    # Headers
    headers = ['Curso', 'Grupo', 'Profesor', 'Total Clases', 'Presentes', 'Faltas', '% Asistencia', 'Estado']
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=header)
        cell.fill = TH_FILL
        cell.font = TH_FONT
        cell.alignment = CENTER
        cell.border = BORDER
    
    # Obtener cursos
    enrollments = Enrollment.objects.filter(
        student=student,
        status='active'
    ).select_related('course_group__course', 'course_group__teacher__user')
    
    cursos_data = []
    
    for enrollment in enrollments:
        course_group = enrollment.course_group
        registros = SimpleAttendanceRecord.objects.filter(
            student=student,
            course_group=course_group,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total = registros.count()
        if total == 0:
            continue
        
        presentes = registros.filter(status='PRESENTE').count()
        faltas = registros.filter(status='FALTA').count()
        porcentaje = (presentes / total * 100)
        porcentaje_faltas = (faltas / total * 100)
        
        # Acumular para estadísticas globales
        total_clases_global += total
        total_presentes_global += presentes
        total_faltas_global += faltas
        
        estado = 'Normal'
        if porcentaje_faltas > 30:
            estado = 'Crítico'
        elif porcentaje_faltas > 20:
            estado = 'Riesgo'
        elif porcentaje_faltas > 10:
            estado = 'Alerta'
        
        cursos_data.append({
            'nombre': course_group.course.name,
            'grupo': course_group.group_code,
            'profesor': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar',
            'total': total,
            'presentes': presentes,
            'faltas': faltas,
            'porcentaje': porcentaje,
            'estado': estado,
        })
    
    # Llenar datos
    for row, curso in enumerate(cursos_data, start=9):
        ws.cell(row=row, column=1, value=curso['nombre'])
        ws.cell(row=row, column=2, value=curso['grupo'])
        ws.cell(row=row, column=3, value=curso['profesor'])
        ws.cell(row=row, column=4, value=curso['total'])
        ws.cell(row=row, column=5, value=curso['presentes'])
        ws.cell(row=row, column=6, value=curso['faltas'])
        ws.cell(row=row, column=7, value=f"{curso['porcentaje']:.1f}%")
        ws.cell(row=row, column=8, value=curso['estado'])
        
        # Color según estado
        fill = PatternFill(
            start_color="FFFFFF",
            end_color="FFFFFF",
            fill_type="solid"
        )
        for col in range(1, 9):
            cell = ws.cell(row=row, column=col)
            cell.font = TD_FONT
            cell.alignment = CENTER
            cell.border = BORDER
    
    # Agregar fila de resumen global
    last_row = len(cursos_data) + 10
    ws.cell(row=last_row, column=1, value='RESUMEN GLOBAL').font = Font(bold=True)
    ws.cell(row=last_row, column=4, value=total_clases_global).font = Font(bold=True)
    ws.cell(row=last_row, column=5, value=total_presentes_global).font = Font(bold=True)
    ws.cell(row=last_row, column=6, value=total_faltas_global).font = Font(bold=True)
    
    porcentaje_global = (total_presentes_global / total_clases_global * 100) if total_clases_global > 0 else 0
    ws.cell(row=last_row, column=7, value=f"{porcentaje_global:.1f}%").font = Font(bold=True)
    
    # Colorear fila de resumen
    summary_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    for col in range(1, 9):
        ws.cell(row=last_row, column=col).fill = summary_fill
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 12
    
    # Respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'reporte_estudiante_{student.student_code}_{fecha_inicio}_{fecha_fin}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

