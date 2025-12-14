#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de exportación de reportes de asistencia a PDF
Incluye: dashboard general, reporte por curso, reporte por estudiante
"""

from datetime import datetime, timedelta
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from repositorio.postgres_repository.models import (
    SimpleAttendanceRecord, Student, CourseGroup, 
    Enrollment, AcademicPeriod
)

COLOR_HEADER = colors.lightgrey
COLOR_GRID = colors.black
COLOR_TEXT = colors.black
COLOR_BG = colors.white
def es_admin_o_secretaria(user):
    return user.is_staff or user.groups.filter(name__in=['Secretaria', 'Administrador']).exists()


# =============================================================================
# EXPORTACIÓN A PDF - DASHBOARD GENERAL
# =============================================================================

@login_required
@user_passes_test(es_admin_o_secretaria)
def exportar_dashboard_pdf(request):
    """
    Exporta el dashboard general de asistencia a PDF
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
    
    # Crear buffer
    buffer = BytesIO()
    
    # Crear documento PDF (landscape para más espacio)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    
    # Container para elementos
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.black,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Título principal
    elements.append(Paragraph("REPORTE DE ASISTENCIA - RESUMEN GENERAL", title_style))
    elements.append(Spacer(1, 12))
    
    # Información del reporte
    info_style = styles['Normal']
    info_text = f"""
    <b>Período:</b> {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}<br/>
    <b>Fecha de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}<br/>
    <b>Generado por:</b> {request.user.get_full_name()}
    """
    elements.append(Paragraph(info_text, info_style))
    elements.append(Spacer(1, 20))
    
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
    
    # Sección: Métricas Generales
    elements.append(Paragraph("MÉTRICAS GENERALES", heading_style))
    
    metricas_data = [
        ['Métrica', 'Valor'],
        ['Total de Registros', str(total_registros)],
        ['Total Presentes', str(total_presentes)],
        ['Total Faltas', str(total_faltas)],
        ['Tasa de Asistencia Global', f'{tasa_global:.1f}%'],
        ['Estudiantes Únicos', str(asistencias.values('student').distinct().count())],
        ['Cursos Activos', str(asistencias.values('course_group').distinct().count())],
    ]
    
    metricas_table = Table(metricas_data, colWidths=[4*inch, 2*inch])
    metricas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),

        ('GRID', (0, 0), (-1, -1), 0.8, COLOR_GRID),
    ]))
    
    elements.append(metricas_table)
    elements.append(Spacer(1, 30))
    
    # Sección: Estudiantes en Riesgo
    elements.append(Paragraph("ESTUDIANTES EN RIESGO (>20% INASISTENCIAS)", heading_style))
    
    estudiantes_riesgo = []
    students = Student.objects.filter(enrollment__status='active').distinct()[:20]
    
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
            estudiantes_riesgo.append({
                'codigo': student.student_code,
                'nombre': student.user.get_full_name(),
                'total': total,
                'faltas': faltas,
                'porcentaje': porcentaje_faltas,
            })
    
    estudiantes_riesgo.sort(key=lambda x: x['porcentaje'], reverse=True)
    
    if estudiantes_riesgo:
        riesgo_data = [['Código', 'Nombre', 'Total', 'Faltas', '% Faltas']]
        
        for est in estudiantes_riesgo[:10]:  # Top 10
            riesgo_data.append([
                est['codigo'],
                est['nombre'][:30],  # Truncar nombre largo
                str(est['total']),
                str(est['faltas']),
                f"{est['porcentaje']:.1f}%"
            ])
        
        riesgo_table = Table(riesgo_data, colWidths=[1*inch, 3*inch, 1*inch, 1*inch, 1*inch])
        riesgo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
            ('GRID', (0, 0), (-1, -1), 0.8, COLOR_GRID),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(riesgo_table)
    else:
        elements.append(Paragraph("No hay estudiantes en riesgo en el período seleccionado.", styles['Normal']))
    
    elements.append(PageBreak())
    
    # Sección: Top Cursos
    elements.append(Paragraph("TOP 15 CURSOS POR ASISTENCIA", heading_style))
    
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
            'nombre': curso.course.name[:40],  # Truncar
            'grupo': curso.group_code,
            'total': total,
            'porcentaje': porcentaje,
        })
    
    cursos_stats.sort(key=lambda x: x['porcentaje'], reverse=True)
    
    if cursos_stats:
        cursos_data = [['Código', 'Curso', 'Grupo', 'Registros', '% Asist.']]
        
        for curso in cursos_stats[:15]:
            cursos_data.append([
                curso['codigo'],
                curso['nombre'],
                curso['grupo'],
                str(curso['total']),
                f"{curso['porcentaje']:.1f}%"
            ])
        
        cursos_table = Table(cursos_data, colWidths=[1*inch, 3.5*inch, 0.8*inch, 1*inch, 1*inch])
        cursos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),

                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),

                ('GRID', (0, 0), (-1, -1), 0.8, COLOR_GRID),
        ]))
        
        elements.append(cursos_table)
    
    # Construir PDF
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    
    # Respuesta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    filename = f'reporte_asistencia_general_{fecha_inicio}_{fecha_fin}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# =============================================================================
# EXPORTACIÓN A PDF - REPORTE POR CURSO
# =============================================================================

@login_required
@user_passes_test(es_admin_o_secretaria)
def exportar_curso_pdf(request, curso_id):
    """Exporta el reporte detallado de un curso a PDF"""
    
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
    
    # Crear buffer
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Título
    elements.append(Paragraph(f"REPORTE DE ASISTENCIA - {curso.course.name}", title_style))
    elements.append(Spacer(1, 12))
    
    # Información del curso
    info_text = f"""
    <b>Código:</b> {curso.course.code} | <b>Grupo:</b> {curso.group_code}<br/>
    <b>Profesor:</b> {curso.teacher.user.get_full_name() if curso.teacher else 'Sin asignar'}<br/>
    <b>Período:</b> {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}<br/>
    <b>Fecha de generación:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Obtener estudiantes
    enrollments = Enrollment.objects.filter(
        course_group=curso,
        status='active'
    ).select_related('student__user')
    
    estudiantes_data = [['Cód.', 'Estudiante', 'Email', 'Total', 'Pres.', 'Faltas', '%', 'Estado']]
    
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
        
        estudiantes_data.append([
            student.student_code,
            student.user.get_full_name()[:25],  # Truncar
            student.user.institutional_email[:25],
            str(total),
            str(presentes),
            str(faltas),
            f"{porcentaje:.1f}%",
            estado
        ])
    
    # Tabla de estudiantes
    table = Table(estudiantes_data, colWidths=[0.8*inch, 2*inch, 2*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),

        ('GRID', (0, 0), (-1, -1), 0.8, COLOR_GRID),
    ]))
    
    elements.append(table)
    
    # Construir PDF
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    
    # Respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    filename = f'reporte_curso_{curso.course.code}_{fecha_inicio}_{fecha_fin}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# =============================================================================
# EXPORTACIÓN A PDF - REPORTE POR ESTUDIANTE
# =============================================================================

@login_required
@user_passes_test(es_admin_o_secretaria)
def exportar_estudiante_pdf(request, estudiante_id):
    """Exporta el reporte detallado de un estudiante a PDF"""
    
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
    
    # Crear buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Título
    elements.append(Paragraph(f"REPORTE DE ASISTENCIA - {student.user.get_full_name()}", title_style))
    elements.append(Spacer(1, 12))
    
    # Información del estudiante
    info_text = f"""
    <b>Código:</b> {student.student_code}<br/>
    <b>Email:</b> {student.user.institutional_email}<br/>
    <b>Período:</b> {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Obtener cursos
    enrollments = Enrollment.objects.filter(
        student=student,
        status='active'
    ).select_related('course_group__course', 'course_group__teacher__user')
    
    cursos_data = [['Curso', 'Profesor', 'Total', 'Pres.', 'Faltas', '%', 'Estado']]
    
    for enrollment in enrollments:
        registros = SimpleAttendanceRecord.objects.filter(
            student=student,
            course_group=enrollment.course_group,
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
        
        estado = 'Normal'
        if porcentaje_faltas > 30:
            estado = 'Crítico'
        elif porcentaje_faltas > 20:
            estado = 'Riesgo'
        elif porcentaje_faltas > 10:
            estado = 'Alerta'
        
        cursos_data.append([
            enrollment.course_group.course.name[:30],
            enrollment.course_group.teacher.user.get_full_name()[:25] if enrollment.course_group.teacher else 'N/A',
            str(total),
            str(presentes),
            str(faltas),
            f"{porcentaje:.1f}%",
            estado
        ])
    
    # Tabla
    table = Table(cursos_data, colWidths=[2.5*inch, 2*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.9*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),

        ('GRID', (0, 0), (-1, -1), 0.8, COLOR_GRID),
    ]))
    
    elements.append(table)
    
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    filename = f'reporte_estudiante_{student.student_code}_{fecha_inicio}_{fecha_fin}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# =============================================================================
# UTILIDADES
# =============================================================================

def _add_page_number(canvas, doc):
    """Agrega número de página al pie de página"""
    page_num = canvas.getPageNumber()
    text = f"Página {page_num}"
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(7.5*inch, 0.5*inch, text)
    canvas.restoreState()
