from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Q
import json
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

from .mixins import ProfesorRequiredMixin
from repositorio.postgres_repository.models import CourseGroup, SimpleAttendanceRecord, PhaseGrade, Enrollment

class ReportesView(ProfesorRequiredMixin, TemplateView):
    """Vista principal para seleccionar curso y tipo de reporte"""
    template_name = 'profesor/reportes/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user.teacher
        
        cursos = CourseGroup.objects.filter(teacher=teacher).select_related('course')
        context['cursos'] = cursos
        
        curso_id = self.request.GET.get('curso_id')
        tipo_reporte = self.request.GET.get('tipo_reporte')
        
        if curso_id and tipo_reporte:
            context['seleccion'] = {'curso_id': curso_id, 'tipo_reporte': tipo_reporte}
            try:
                curso_seleccionado = CourseGroup.objects.get(id=curso_id, teacher=teacher)
                context['curso_actual'] = curso_seleccionado
                
                if tipo_reporte == 'asistencia':
                    context['datos_grafico'] = self._get_datos_asistencia(curso_seleccionado)
                elif tipo_reporte == 'notas':
                    context['datos_grafico'] = self._get_datos_notas(curso_seleccionado)
                    
            except CourseGroup.DoesNotExist:
                messages.error(self.request, "El curso seleccionado no es válido.")
        
        return context

    def _get_datos_asistencia(self, curso):
        """Calcula % de asistencia vs faltas global del curso"""
        total_asistencias = SimpleAttendanceRecord.objects.filter(
            course_group=curso, status='PRESENTE'
        ).count()
        total_faltas = SimpleAttendanceRecord.objects.filter(
            course_group=curso, status='FALTA'
        ).count()
        
        if total_asistencias == 0 and total_faltas == 0:
            return json.dumps({
                'labels': ['Sin Registros'],
                'data': [1],
                'colors': ['#e5e7eb']
            })
        
        return json.dumps({
            'labels': ['Asistencias', 'Faltas'],
            'data': [total_asistencias, total_faltas],
            'colors': ['#10b981', '#ef4444'] 
        })

    def _get_datos_notas(self, curso):
        """Calcula Aprobados vs Desaprobados considerando TODAS las fases registradas"""
        
        notas = PhaseGrade.objects.filter(
            course_group=curso, 
            final_phase_grade__isnull=False
        )
        
        if not notas.exists():
            notas = PhaseGrade.objects.filter(
                course_group=curso,
                partial_grade__isnull=False
            )
            aprobados = notas.filter(partial_grade__gte=10.5).count()
            desaprobados = notas.filter(partial_grade__lt=10.5).count()
        else:
            aprobados = notas.filter(final_phase_grade__gte=10.5).count()
            desaprobados = notas.filter(final_phase_grade__lt=10.5).count()

        if aprobados == 0 and desaprobados == 0:
            return json.dumps({
                'labels': ['Sin Notas Registradas'],
                'data': [1],
                'colors': ['#e5e7eb'] 
            })
        
        return json.dumps({
            'labels': ['Notas Aprobatorias', 'Notas Desaprobatorias'],
            'data': [aprobados, desaprobados],
            'colors': ['#3b82f6', '#f59e0b']
        })


class GenerarPDFView(ProfesorRequiredMixin, View):
    """Genera el PDF oficial"""
    
    def get(self, request, *args, **kwargs):
        curso_id = request.GET.get('curso_id')
        tipo_reporte = request.GET.get('tipo_reporte')
        
        if not curso_id or not tipo_reporte:
            return redirect('profesor:reportes')
            
        try:
            teacher = request.user.teacher
            curso = CourseGroup.objects.get(id=curso_id, teacher=teacher)
            
            matriculas = Enrollment.objects.filter(
                course_group=curso, status='active'
            ).select_related('student__user').order_by('student__user__last_name')
            
            data_reporte = []
            headers = []
            titulo_reporte = ""
            
            if tipo_reporte == 'asistencia':
                titulo_reporte = "REPORTE DE ASISTENCIA GENERAL"
                headers = ["N°", "CUI", "Apellidos y Nombres", "Asist.", "Faltas", "%"]
                
                for idx, mat in enumerate(matriculas, 1):
                    student = mat.student
                    presentes = SimpleAttendanceRecord.objects.filter(student=student, course_group=curso, status='PRESENTE').count()
                    faltas = SimpleAttendanceRecord.objects.filter(student=student, course_group=curso, status='FALTA').count()
                    total = presentes + faltas
                    porcentaje = round((presentes/total * 100), 1) if total > 0 else 0
                    
                    data_reporte.append({
                        'index': idx,
                        'cui': student.student_code,
                        'nombre': student.user.get_full_name().upper(),
                        'col1': presentes,
                        'col2': faltas,
                        'col3': f"{porcentaje}%"
                    })
                    
            elif tipo_reporte == 'notas':
                titulo_reporte = "REPORTE DE NOTAS"
                headers = ["N°", "CUI", "Apellidos y Nombres", "Fase 1", "Fase 2", "Fase 3"]
                
                for idx, mat in enumerate(matriculas, 1):
                    student = mat.student
                    n1 = PhaseGrade.objects.filter(student=student, course_group=curso, phase='primera').first()
                    n2 = PhaseGrade.objects.filter(student=student, course_group=curso, phase='segunda').first()
                    n3 = PhaseGrade.objects.filter(student=student, course_group=curso, phase='tercera').first()
                    
                    def fmt_nota(n):
                        return str(n.final_phase_grade) if (n and n.final_phase_grade is not None) else "-"

                    data_reporte.append({
                        'index': idx,
                        'cui': student.student_code,
                        'nombre': student.user.get_full_name().upper(),
                        'col1': fmt_nota(n1),
                        'col2': fmt_nota(n2),
                        'col3': fmt_nota(n3)
                    })

            context = {
                'curso': curso,
                'docente': teacher,
                'titulo': titulo_reporte,
                'tipo': tipo_reporte,
                'headers': headers,
                'data': data_reporte,
                'fecha_impresion': timezone.now()
            }
            
            template = get_template('profesor/reportes/pdf_template.html')
            html = template.render(context)
            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
            
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf')
                filename = f"Reporte_{tipo_reporte}_{curso.course.code}.pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            
            return HttpResponse("Error al generar PDF: Error interno de libreria", status=500)
            
        except Exception as e:
            return HttpResponse(f"Error generando reporte: {str(e)}", status=500)