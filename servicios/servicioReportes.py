#!/usr/bin/python
# -*- coding: utf-8 -*-

import io
import os
from datetime import datetime, date, timedelta
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Count, Avg, Q
from repositorio.postgres_repository.models import UsuarioModel, EstudianteModel, MatriculaModel

# PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Excel generation
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class ReporteGeneracionException(Exception):
    """Excepción para errores en la generación de reportes"""
    pass


class ServicioReportes:
    def __init__(self):
        self._repositorio_reporte = None
        self._servicio_asistencia = None
        self._servicio_notas = None
        self._servicio_avance = None

    def generar_reporte_asistencia_global(self, fecha_inicio, fecha_fin, formato='pdf', incluir_detalle=False):
        """
        Genera un reporte global de asistencia para el período especificado
        """
        try:
            # Obtener datos de asistencia (simulado por ahora)
            datos_asistencia = self._obtener_datos_asistencia(fecha_inicio, fecha_fin)
            
            if formato == 'pdf':
                return self._generar_pdf_asistencia(datos_asistencia, fecha_inicio, fecha_fin, incluir_detalle)
            elif formato == 'excel':
                return self._generar_excel_asistencia(datos_asistencia, fecha_inicio, fecha_fin, incluir_detalle)
            else:
                raise ReporteGeneracionException(f"Formato no soportado: {formato}")
                
        except Exception as e:
            raise ReporteGeneracionException(f"Error generando reporte de asistencia: {str(e)}")

    def generar_reporte_notas_global(self, ciclo, tipo_reporte='global', curso_codigo=None, 
                                   docente_email=None, formato='pdf', incluir_estadisticas=True):
        """
        Genera un reporte global de notas según los parámetros especificados
        """
        try:
            # Obtener datos de notas (simulado por ahora)
            datos_notas = self._obtener_datos_notas(ciclo, tipo_reporte, curso_codigo, docente_email)
            
            if formato == 'pdf':
                return self._generar_pdf_notas(datos_notas, ciclo, tipo_reporte, incluir_estadisticas)
            elif formato == 'excel':
                return self._generar_excel_notas(datos_notas, ciclo, tipo_reporte, incluir_estadisticas)
            else:
                raise ReporteGeneracionException(f"Formato no soportado: {formato}")
                
        except Exception as e:
            raise ReporteGeneracionException(f"Error generando reporte de notas: {str(e)}")

    def generar_reporte_estadisticas_global(self, periodo, fecha_inicio=None, fecha_fin=None, 
                                          formato='pdf', incluir_graficos=True):
        """
        Genera un reporte de estadísticas generales del sistema
        """
        try:
            # Calcular fechas según el período
            if periodo != 'personalizado':
                fecha_inicio, fecha_fin = self._calcular_fechas_periodo(periodo)
            
            # Obtener estadísticas del sistema
            estadisticas = self._obtener_estadisticas_sistema(fecha_inicio, fecha_fin)
            
            if formato == 'pdf':
                return self._generar_pdf_estadisticas(estadisticas, periodo, fecha_inicio, fecha_fin, incluir_graficos)
            elif formato == 'excel':
                return self._generar_excel_estadisticas(estadisticas, periodo, fecha_inicio, fecha_fin)
            else:
                raise ReporteGeneracionException(f"Formato no soportado: {formato}")
                
        except Exception as e:
            raise ReporteGeneracionException(f"Error generando reporte de estadísticas: {str(e)}")

    def _obtener_datos_asistencia(self, fecha_inicio, fecha_fin):
        """Obtiene datos de asistencia del período especificado"""
        # Por ahora retornamos datos simulados
        # En una implementación real, esto consultaría la base de datos
        return {
            'total_estudiantes': EstudianteModel.objects.filter(estado='ACTIVO').count(),
            'total_sesiones': 45,  # Simulado
            'promedio_asistencia': 85.5,
            'asistencias_por_curso': [
                {'curso': 'MAT101', 'estudiantes': 25, 'promedio': 88.2},
                {'curso': 'FIS201', 'estudiantes': 30, 'promedio': 82.1},
                {'curso': 'QUI301', 'estudiantes': 22, 'promedio': 90.5},
            ],
            'detalle_estudiantes': [
                {'codigo': '20210001', 'nombre': 'Juan Pérez', 'asistencias': 38, 'porcentaje': 84.4},
                {'codigo': '20210002', 'nombre': 'María García', 'asistencias': 42, 'porcentaje': 93.3},
            ] if fecha_inicio and fecha_fin else []
        }

    def _obtener_datos_notas(self, ciclo, tipo_reporte, curso_codigo, docente_email):
        """Obtiene datos de notas según los parámetros especificados"""
        # Por ahora retornamos datos simulados
        return {
            'ciclo': ciclo,
            'tipo_reporte': tipo_reporte,
            'total_estudiantes': EstudianteModel.objects.filter(estado='ACTIVO').count(),
            'promedio_general': 14.2,
            'notas_por_curso': [
                {'curso': 'MAT101', 'estudiantes': 25, 'promedio': 15.1, 'aprobados': 22, 'desaprobados': 3},
                {'curso': 'FIS201', 'estudiantes': 30, 'promedio': 13.8, 'aprobados': 25, 'desaprobados': 5},
                {'curso': 'QUI301', 'estudiantes': 22, 'promedio': 16.2, 'aprobados': 21, 'desaprobados': 1},
            ],
            'estadisticas': {
                'nota_maxima': 18.5,
                'nota_minima': 8.2,
                'desviacion_estandar': 2.3,
                'porcentaje_aprobacion': 78.5
            }
        }

    def _obtener_estadisticas_sistema(self, fecha_inicio, fecha_fin):
        """Obtiene estadísticas generales del sistema"""
        usuarios_stats = UsuarioModel.objects.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True)),
            estudiantes=Count('id', filter=Q(rol='estudiante')),
            docentes=Count('id', filter=Q(rol='docente')),
            secretarias=Count('id', filter=Q(rol='secretaria')),
            admins=Count('id', filter=Q(rol='admin'))
        )
        
        estudiantes_stats = EstudianteModel.objects.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(estado='ACTIVO')),
            retirados=Count('id', filter=Q(estado='RETIRADO'))
        )
        
        matriculas_stats = MatriculaModel.objects.aggregate(
            total=Count('id'),
            matriculados=Count('id', filter=Q(estado='MATRICULADO'))
        )
        
        return {
            'periodo': f"{fecha_inicio} - {fecha_fin}",
            'usuarios': usuarios_stats,
            'estudiantes': estudiantes_stats,
            'matriculas': matriculas_stats,
            'cursos_activos': 15,  # Simulado
            'laboratorios_disponibles': 8,  # Simulado
            'reservas_pendientes': 12,  # Simulado
        }

    def _calcular_fechas_periodo(self, periodo):
        """Calcula las fechas de inicio y fin según el período especificado"""
        hoy = date.today()
        
        if periodo == 'mensual':
            inicio = hoy.replace(day=1)
            fin = hoy
        elif periodo == 'trimestral':
            mes_inicio = ((hoy.month - 1) // 3) * 3 + 1
            inicio = hoy.replace(month=mes_inicio, day=1)
            fin = hoy
        elif periodo == 'semestral':
            mes_inicio = 1 if hoy.month <= 6 else 7
            inicio = hoy.replace(month=mes_inicio, day=1)
            fin = hoy
        elif periodo == 'anual':
            inicio = hoy.replace(month=1, day=1)
            fin = hoy
        else:
            inicio = hoy - timedelta(days=30)
            fin = hoy
            
        return inicio, fin

    def _generar_pdf_asistencia(self, datos, fecha_inicio, fecha_fin, incluir_detalle):
        """Genera reporte de asistencia en formato PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ReporteGeneracionException("ReportLab no está disponible para generar PDFs")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Reporte Global de Asistencia", title_style))
        story.append(Paragraph(f"Período: {fecha_inicio} - {fecha_fin}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Resumen general
        story.append(Paragraph("Resumen General", styles['Heading2']))
        resumen_data = [
            ['Total de Estudiantes', str(datos['total_estudiantes'])],
            ['Total de Sesiones', str(datos['total_sesiones'])],
            ['Promedio de Asistencia', f"{datos['promedio_asistencia']}%"],
        ]
        
        resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(resumen_table)
        story.append(Spacer(1, 20))
        
        # Asistencia por curso
        story.append(Paragraph("Asistencia por Curso", styles['Heading2']))
        curso_data = [['Curso', 'Estudiantes', 'Promedio Asistencia']]
        for curso in datos['asistencias_por_curso']:
            curso_data.append([curso['curso'], str(curso['estudiantes']), f"{curso['promedio']}%"])
        
        curso_table = Table(curso_data, colWidths=[2*inch, 1.5*inch, 2*inch])
        curso_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(curso_table)
        
        # Detalle por estudiante si se solicita
        if incluir_detalle and datos['detalle_estudiantes']:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Detalle por Estudiante", styles['Heading2']))
            detalle_data = [['Código', 'Nombre', 'Asistencias', 'Porcentaje']]
            for estudiante in datos['detalle_estudiantes']:
                detalle_data.append([
                    estudiante['codigo'],
                    estudiante['nombre'],
                    str(estudiante['asistencias']),
                    f"{estudiante['porcentaje']}%"
                ])
            
            detalle_table = Table(detalle_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
            detalle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(detalle_table)
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_asistencia_{fecha_inicio}_{fecha_fin}.pdf"'
        return response

    def _generar_excel_asistencia(self, datos, fecha_inicio, fecha_fin, incluir_detalle):
        """Genera reporte de asistencia en formato Excel"""
        if not OPENPYXL_AVAILABLE:
            raise ReporteGeneracionException("openpyxl no está disponible para generar archivos Excel")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Asistencia"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                       top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Título
        ws['A1'] = "Reporte Global de Asistencia"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A2'] = f"Período: {fecha_inicio} - {fecha_fin}"
        
        # Resumen general
        row = 4
        ws[f'A{row}'] = "Resumen General"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        headers = ['Concepto', 'Valor']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        resumen_data = [
            ['Total de Estudiantes', datos['total_estudiantes']],
            ['Total de Sesiones', datos['total_sesiones']],
            ['Promedio de Asistencia', f"{datos['promedio_asistencia']}%"],
        ]
        
        for data_row in resumen_data:
            row += 1
            for col, value in enumerate(data_row, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Asistencia por curso
        row += 3
        ws[f'A{row}'] = "Asistencia por Curso"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        curso_headers = ['Curso', 'Estudiantes', 'Promedio Asistencia']
        for col, header in enumerate(curso_headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        for curso in datos['asistencias_por_curso']:
            row += 1
            curso_data = [curso['curso'], curso['estudiantes'], f"{curso['promedio']}%"]
            for col, value in enumerate(curso_data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Detalle por estudiante si se solicita
        if incluir_detalle and datos['detalle_estudiantes']:
            row += 3
            ws[f'A{row}'] = "Detalle por Estudiante"
            ws[f'A{row}'].font = Font(bold=True, size=14)
            
            row += 1
            detalle_headers = ['Código', 'Nombre', 'Asistencias', 'Porcentaje']
            for col, header in enumerate(detalle_headers, 1):
                cell = ws.cell(row=row, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
            
            for estudiante in datos['detalle_estudiantes']:
                row += 1
                estudiante_data = [
                    estudiante['codigo'],
                    estudiante['nombre'],
                    estudiante['asistencias'],
                    f"{estudiante['porcentaje']}%"
                ]
                for col, value in enumerate(estudiante_data, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.border = border
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_asistencia_{fecha_inicio}_{fecha_fin}.xlsx"'
        return response

    def _generar_pdf_notas(self, datos, ciclo, tipo_reporte, incluir_estadisticas):
        """Genera reporte de notas en formato PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ReporteGeneracionException("ReportLab no está disponible para generar PDFs")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Reporte de Notas - {tipo_reporte.title()}", title_style))
        story.append(Paragraph(f"Ciclo: {ciclo}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Resumen general
        story.append(Paragraph("Resumen General", styles['Heading2']))
        resumen_data = [
            ['Total de Estudiantes', str(datos['total_estudiantes'])],
            ['Promedio General', str(datos['promedio_general'])],
        ]
        
        if incluir_estadisticas:
            stats = datos['estadisticas']
            resumen_data.extend([
                ['Nota Máxima', str(stats['nota_maxima'])],
                ['Nota Mínima', str(stats['nota_minima'])],
                ['Desviación Estándar', str(stats['desviacion_estandar'])],
                ['% Aprobación', f"{stats['porcentaje_aprobacion']}%"],
            ])
        
        resumen_table = Table(resumen_data, colWidths=[3*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(resumen_table)
        story.append(Spacer(1, 20))
        
        # Notas por curso
        story.append(Paragraph("Notas por Curso", styles['Heading2']))
        curso_data = [['Curso', 'Estudiantes', 'Promedio', 'Aprobados', 'Desaprobados']]
        for curso in datos['notas_por_curso']:
            curso_data.append([
                curso['curso'],
                str(curso['estudiantes']),
                str(curso['promedio']),
                str(curso['aprobados']),
                str(curso['desaprobados'])
            ])
        
        curso_table = Table(curso_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        curso_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(curso_table)
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_notas_{ciclo}_{tipo_reporte}.pdf"'
        return response

    def _generar_excel_notas(self, datos, ciclo, tipo_reporte, incluir_estadisticas):
        """Genera reporte de notas en formato Excel"""
        if not OPENPYXL_AVAILABLE:
            raise ReporteGeneracionException("openpyxl no está disponible para generar archivos Excel")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Notas"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                       top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Título
        ws['A1'] = f"Reporte de Notas - {tipo_reporte.title()}"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A2'] = f"Ciclo: {ciclo}"
        
        # Resumen general
        row = 4
        ws[f'A{row}'] = "Resumen General"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        headers = ['Concepto', 'Valor']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        resumen_data = [
            ['Total de Estudiantes', datos['total_estudiantes']],
            ['Promedio General', datos['promedio_general']],
        ]
        
        if incluir_estadisticas:
            stats = datos['estadisticas']
            resumen_data.extend([
                ['Nota Máxima', stats['nota_maxima']],
                ['Nota Mínima', stats['nota_minima']],
                ['Desviación Estándar', stats['desviacion_estandar']],
                ['% Aprobación', f"{stats['porcentaje_aprobacion']}%"],
            ])
        
        for data_row in resumen_data:
            row += 1
            for col, value in enumerate(data_row, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Notas por curso
        row += 3
        ws[f'A{row}'] = "Notas por Curso"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        curso_headers = ['Curso', 'Estudiantes', 'Promedio', 'Aprobados', 'Desaprobados']
        for col, header in enumerate(curso_headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        for curso in datos['notas_por_curso']:
            row += 1
            curso_data = [
                curso['curso'],
                curso['estudiantes'],
                curso['promedio'],
                curso['aprobados'],
                curso['desaprobados']
            ]
            for col, value in enumerate(curso_data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_notas_{ciclo}_{tipo_reporte}.xlsx"'
        return response

    def _generar_pdf_estadisticas(self, datos, periodo, fecha_inicio, fecha_fin, incluir_graficos):
        """Genera reporte de estadísticas en formato PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ReporteGeneracionException("ReportLab no está disponible para generar PDFs")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Reporte de Estadísticas del Sistema", title_style))
        story.append(Paragraph(f"Período: {periodo.title()}", styles['Normal']))
        story.append(Paragraph(f"Fechas: {fecha_inicio} - {fecha_fin}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Estadísticas de usuarios
        story.append(Paragraph("Estadísticas de Usuarios", styles['Heading2']))
        usuarios_data = [
            ['Concepto', 'Cantidad'],
            ['Total de Usuarios', str(datos['usuarios']['total'])],
            ['Usuarios Activos', str(datos['usuarios']['activos'])],
            ['Estudiantes', str(datos['usuarios']['estudiantes'])],
            ['Docentes', str(datos['usuarios']['docentes'])],
            ['Secretarias', str(datos['usuarios']['secretarias'])],
            ['Administradores', str(datos['usuarios']['admins'])],
        ]
        
        usuarios_table = Table(usuarios_data, colWidths=[3*inch, 2*inch])
        usuarios_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(usuarios_table)
        story.append(Spacer(1, 20))
        
        # Estadísticas del sistema
        story.append(Paragraph("Estadísticas del Sistema", styles['Heading2']))
        sistema_data = [
            ['Concepto', 'Cantidad'],
            ['Cursos Activos', str(datos['cursos_activos'])],
            ['Laboratorios Disponibles', str(datos['laboratorios_disponibles'])],
            ['Reservas Pendientes', str(datos['reservas_pendientes'])],
            ['Matrículas Totales', str(datos['matriculas']['total'])],
            ['Matrículas Activas', str(datos['matriculas']['matriculados'])],
        ]
        
        sistema_table = Table(sistema_data, colWidths=[3*inch, 2*inch])
        sistema_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(sistema_table)
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_estadisticas_{periodo}_{fecha_inicio}_{fecha_fin}.pdf"'
        return response

    def _generar_excel_estadisticas(self, datos, periodo, fecha_inicio, fecha_fin):
        """Genera reporte de estadísticas en formato Excel"""
        if not OPENPYXL_AVAILABLE:
            raise ReporteGeneracionException("openpyxl no está disponible para generar archivos Excel")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Estadísticas Sistema"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                       top=Side(style='thin'), bottom=Side(style='thin'))
        
        # Título
        ws['A1'] = "Reporte de Estadísticas del Sistema"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A2'] = f"Período: {periodo.title()}"
        ws['A3'] = f"Fechas: {fecha_inicio} - {fecha_fin}"
        
        # Estadísticas de usuarios
        row = 5
        ws[f'A{row}'] = "Estadísticas de Usuarios"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        headers = ['Concepto', 'Cantidad']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        usuarios_data = [
            ['Total de Usuarios', datos['usuarios']['total']],
            ['Usuarios Activos', datos['usuarios']['activos']],
            ['Estudiantes', datos['usuarios']['estudiantes']],
            ['Docentes', datos['usuarios']['docentes']],
            ['Secretarias', datos['usuarios']['secretarias']],
            ['Administradores', datos['usuarios']['admins']],
        ]
        
        for data_row in usuarios_data:
            row += 1
            for col, value in enumerate(data_row, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Estadísticas del sistema
        row += 3
        ws[f'A{row}'] = "Estadísticas del Sistema"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        sistema_data = [
            ['Cursos Activos', datos['cursos_activos']],
            ['Laboratorios Disponibles', datos['laboratorios_disponibles']],
            ['Reservas Pendientes', datos['reservas_pendientes']],
            ['Matrículas Totales', datos['matriculas']['total']],
            ['Matrículas Activas', datos['matriculas']['matriculados']],
        ]
        
        for data_row in sistema_data:
            row += 1
            for col, value in enumerate(data_row, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_estadisticas_{periodo}_{fecha_inicio}_{fecha_fin}.xlsx"'
        return response
        
        
        for data_row in usuarios_data:
            row += 1
            for col, value in enumerate(data_row, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Estadísticas del sistema
        row += 3
        ws[f'A{row}'] = "Estadísticas del Sistema"
        ws[f'A{row}'].font = Font(bold=True, size=14)
        
        row += 1
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        
        sistema_data = [
            ['Cursos Activos', datos['cursos_activos']],
            ['Laboratorios Disponibles', datos['laboratorios_disponibles']],
            ['Reservas Pendientes', datos['reservas_pendientes']],
            ['Matrículas Totales', datos['matriculas']['total']],
            ['Matrículas Activas', datos['matriculas']['matriculados']],
        ]
        
        for data_row in sistema_data:
            row += 1
            for col, value in enumerate(data_row, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.border = border
        
        # Ajustar ancho de columnas
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="reporte_estadisticas_{periodo}_{fecha_inicio}_{fecha_fin}.xlsx"'
        return response

    # Legacy methods for compatibility
    def exportar_reporte_pdf(self, reporte):
        """Método legacy - usar los nuevos métodos específicos"""
        pass

    def exportar_reporte_excel(self, reporte):
        """Método legacy - usar los nuevos métodos específicos"""
        pass

    def generar_reporte_asistencia(self, curso_id):
        """Método legacy - usar generar_reporte_asistencia_global"""
        pass

    def generar_reporte_notas(self, curso_id):
        """Método legacy - usar generar_reporte_notas_global"""
        pass

    def generar_reporte_avance(self, curso_id):
        pass

    def generar_reporte_global(self, periodo_id):
        """Método legacy - usar generar_reporte_estadisticas_global"""
        pass

    def generar_lista_profesores(self, periodo_id):
        pass

    def generar_lista_alumnos(self, criterio):
        pass

    def obtener_tipos_reportes_disponibles(self):
        """Retorna los tipos de reportes disponibles y sus formatos soportados"""
        return {
            'asistencia': {
                'nombre': 'Reportes de Asistencia',
                'descripcion': 'Reportes globales de asistencia por período',
                'formatos': ['pdf', 'excel'],
                'parametros': ['fecha_inicio', 'fecha_fin', 'incluir_detalle']
            },
            'notas': {
                'nombre': 'Reportes de Notas',
                'descripcion': 'Reportes de calificaciones por curso, docente o global',
                'formatos': ['pdf', 'excel'],
                'parametros': ['ciclo', 'tipo_reporte', 'curso_codigo', 'docente_email', 'incluir_estadisticas']
            },
            'estadisticas': {
                'nombre': 'Estadísticas del Sistema',
                'descripcion': 'Reportes estadísticos generales del sistema académico',
                'formatos': ['pdf', 'excel'],
                'parametros': ['periodo', 'fecha_inicio', 'fecha_fin', 'incluir_graficos']
            }
        }

    def validar_disponibilidad_librerias(self):
        """Valida que las librerías necesarias estén disponibles"""
        return {
            'reportlab_disponible': REPORTLAB_AVAILABLE,
            'openpyxl_disponible': OPENPYXL_AVAILABLE,
            'pdf_habilitado': REPORTLAB_AVAILABLE,
            'excel_habilitado': OPENPYXL_AVAILABLE
        }
