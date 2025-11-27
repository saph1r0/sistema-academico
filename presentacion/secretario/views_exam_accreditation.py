#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para acreditación de exámenes (SIN FASES).
Profesor sube 2 exámenes (mejor y peor nota) por cada parcial (1, 2, 3)
"""

import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from servicios.servicioAcreditacionExamenes import servicio_acreditacion_examenes
from repositorio.postgres_repository.models import (
    CourseGroup, Teacher, ExamAccreditation, AcademicPeriod, Course
)
from presentacion.secretario.forms import SecretaryExamFilterForm

logger = logging.getLogger(__name__)


class ExamAccreditationDownloadView(View):
    """Descargar archivos de exámenes acreditados"""

    def get(self, request, accreditation_id, file_type, *args, **kwargs):
        """
        file_type: 'best' o 'worst'
        """
        try:
            acc = get_object_or_404(ExamAccreditation, id=accreditation_id)

            user = request.user

            # Validar permisos
            if user.is_teacher():
                if str(acc.uploaded_by_id) != str(user.teacher.id):
                    raise Http404("No tiene permiso para descargar este archivo")
            elif not user.is_secretary():
                raise Http404("No tiene permiso para descargar archivos")

            # Seleccionar archivo
            if file_type == 'best':
                file_field = acc.best_exam_file
            elif file_type == 'worst':
                file_field = acc.worst_exam_file
            else:
                raise Http404("Tipo de archivo inválido")

            if not file_field:
                raise Http404("Archivo no encontrado")

            response = FileResponse(file_field.open('rb'))
            filename = os.path.basename(file_field.name)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            
            return response

        except ExamAccreditation.DoesNotExist:
            raise Http404("Acreditación no encontrada")
        except Exception as e:
            logger.error(f"Error descarga: {e}")
            raise Http404("Error descargando archivo")


# ============================================================
#   VISTA SECRETARÍA
# ============================================================

class SecretaryExamAccreditationView(TemplateView):
    """Vista de secretaría para ver todas las acreditaciones"""
    template_name = 'secretario/acreditacion/index.html'

    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario sea secretaría"""
        if not request.user.is_secretary():
            messages.error(request, 'No tiene permiso para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener filtros
            filters = {
                'academic_period_id': self.request.GET.get('academic_period'),
                'course_id': self.request.GET.get('course'),
                'teacher_id': self.request.GET.get('teacher'),
                'exam_number': self.request.GET.get('exam_number'),
                'date_from': self.request.GET.get('date_from'),
                'date_to': self.request.GET.get('date_to'),
            }
            
            # Limpiar filtros vacíos
            filters = {k: v for k, v in filters.items() if v}
            
            # Query base
            accreditations_qs = ExamAccreditation.objects.select_related(
                'course_group__course',
                'course_group__academic_period',
                'uploaded_by__user'
            )
            
            # Aplicar filtros
            if filters.get('academic_period_id'):
                accreditations_qs = accreditations_qs.filter(
                    course_group__academic_period_id=filters['academic_period_id']
                )
            
            if filters.get('course_id'):
                accreditations_qs = accreditations_qs.filter(
                    course_group__course_id=filters['course_id']
                )
            
            if filters.get('teacher_id'):
                accreditations_qs = accreditations_qs.filter(
                    uploaded_by_id=filters['teacher_id']
                )
            
            if filters.get('exam_number'):
                accreditations_qs = accreditations_qs.filter(
                    exam_number=filters['exam_number']
                )
            
            if filters.get('date_from'):
                accreditations_qs = accreditations_qs.filter(
                    uploaded_at__gte=filters['date_from']
                )
            
            if filters.get('date_to'):
                accreditations_qs = accreditations_qs.filter(
                    uploaded_at__lte=filters['date_to']
                )
            
            accreditations_qs = accreditations_qs.order_by('-uploaded_at')
            
            # Preparar datos para template
            accreditations = []
            for acc in accreditations_qs:
                accreditations.append({
                    'id': str(acc.id),
                    'course': {
                        'code': acc.course_group.course.code,
                        'name': acc.course_group.course.name,
                        'group': acc.course_group.group_code
                    },
                    'teacher': {
                        'name': acc.uploaded_by.user.get_full_name(),
                        'code': acc.uploaded_by.teacher_code
                    },
                    'exam_number': acc.exam_number,
                    'exam_number_display': acc.get_exam_number_display(),
                    'best_file': {
                        'name': os.path.basename(acc.best_exam_file.name) if acc.best_exam_file else None,
                        'size': acc.best_exam_file.size if acc.best_exam_file else 0,
                        'is_pdf': acc.best_exam_file.name.lower().endswith('.pdf') if acc.best_exam_file else False,
                    },
                    'worst_file': {
                        'name': os.path.basename(acc.worst_exam_file.name) if acc.worst_exam_file else None,
                        'size': acc.worst_exam_file.size if acc.worst_exam_file else 0,
                        'is_pdf': acc.worst_exam_file.name.lower().endswith('.pdf') if acc.worst_exam_file else False,
                    },
                    'statistics': {
                        'max': float(acc.max_grade) if acc.max_grade else 0,
                        'min': float(acc.min_grade) if acc.min_grade else 0,
                        'avg': float(acc.average_grade) if acc.average_grade else 0,
                        'total_students': acc.total_students
                    },
                    'uploaded_at': acc.uploaded_at.isoformat(),
                    'academic_period': acc.course_group.academic_period.name
                })
            
            # Opciones para filtros
            academic_periods = AcademicPeriod.objects.filter(is_active=True).order_by('-start_date')
            courses = Course.objects.filter(is_active=True).order_by('name')
            teachers = Teacher.objects.select_related('user').order_by('user__last_name')
            
            context.update({
                'accreditations': accreditations,
                'total_accreditations': len(accreditations),
                'academic_periods': academic_periods,
                'courses': courses,
                'teachers': teachers,
                'filters_applied': filters,
                'filter_form': SecretaryExamFilterForm(initial=self.request.GET),
            })
            
        except Exception as e:
            logger.error(f"Error cargando acreditaciones para secretaría: {str(e)}")
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'accreditations': [],
                'total_accreditations': 0
            })
        
        return context