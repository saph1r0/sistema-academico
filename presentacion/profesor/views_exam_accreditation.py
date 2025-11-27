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

from .mixins import ProfesorRequiredMixin
from .forms import ExamAccreditationForm
from servicios.servicioAcreditacionExamenes import servicio_acreditacion_examenes
from repositorio.postgres_repository.models import (
    CourseGroup, Teacher, ExamAccreditation, AcademicPeriod, Course
)

logger = logging.getLogger(__name__)


# ============================================================
#   VISTA PRINCIPAL PROFESOR
# ============================================================

class TeacherExamAccreditationView(ProfesorRequiredMixin, TemplateView):
    template_name = 'profesor/exam_accreditation/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            teacher = self.request.user.teacher

            # Obtener cursos del profesor
            course_groups = CourseGroup.objects.filter(
                teacher=teacher
            ).select_related("course", "academic_period").order_by('course__name')

            courses_data = []

            for cg in course_groups:
                # Contar acreditaciones por parcial (1, 2, 3)
                acc_counts = {
                    1: ExamAccreditation.objects.filter(course_group=cg, exam_number=1).exists(),
                    2: ExamAccreditation.objects.filter(course_group=cg, exam_number=2).exists(),
                    3: ExamAccreditation.objects.filter(course_group=cg, exam_number=3).exists(),
                }

                total_uploaded = sum(1 for uploaded in acc_counts.values() if uploaded)

                courses_data.append({
                    "id": str(cg.id),
                    "course_name": cg.course.name,
                    "course_code": cg.course.code,
                    "group_code": cg.group_code,
                    "academic_period": cg.academic_period.name,
                    "enrolled_students": cg.enrolled_students,
                    "accreditations_by_parcial": acc_counts,
                    "total_uploaded": total_uploaded,
                    "total_required": 3  # 3 parciales
                })

            # Curso seleccionado
            selected_course_id = self.request.GET.get("course_id")
            selected_course = next(
                (c for c in courses_data if c["id"] == selected_course_id),
                None
            )

            # Obtener acreditaciones del curso seleccionado
            accreditations = []
            if selected_course:
                accs = ExamAccreditation.objects.filter(
                    course_group_id=selected_course_id
                ).order_by('exam_number')

                for acc in accs:
                    accreditations.append({
                        'id': str(acc.id),
                        'exam_number': acc.exam_number,
                        'exam_number_display': acc.get_exam_number_display(),
                        'best_file': {
                            'name': os.path.basename(acc.best_exam_file.name) if acc.best_exam_file else None,
                            'url': acc.best_exam_file.url if acc.best_exam_file else None,
                            'size': acc.best_exam_file.size if acc.best_exam_file else 0,
                            'is_pdf': acc.best_exam_file.name.lower().endswith('.pdf') if acc.best_exam_file else False,
                        },
                        'worst_file': {
                            'name': os.path.basename(acc.worst_exam_file.name) if acc.worst_exam_file else None,
                            'url': acc.worst_exam_file.url if acc.worst_exam_file else None,
                            'size': acc.worst_exam_file.size if acc.worst_exam_file else 0,
                            'is_pdf': acc.worst_exam_file.name.lower().endswith('.pdf') if acc.worst_exam_file else False,
                        },
                        'statistics': {
                            'max': float(acc.max_grade) if acc.max_grade else 0,
                            'min': float(acc.min_grade) if acc.min_grade else 0,
                            'avg': float(acc.average_grade) if acc.average_grade else 0,
                            'total_students': acc.total_students
                        },
                        'uploaded_at': acc.uploaded_at.isoformat()
                    })

            context.update({
                "courses": courses_data,
                "selected_course": selected_course,
                "accreditations": accreditations,
                "upload_form": ExamAccreditationForm(initial={
                    "course_group_id": selected_course_id
                }) if selected_course_id else ExamAccreditationForm(),
            })

        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'courses': [],
                'selected_course': None,
                'accreditations': [],
                'upload_form': ExamAccreditationForm()
            })
        except Exception as e:
            logger.error(f"Error cargando acreditaciones: {e}")
            messages.error(self.request, f"Error cargando datos: {e}")
            context.update({
                'courses': [],
                'selected_course': None,
                'accreditations': [],
                'upload_form': ExamAccreditationForm()
            })

        return context

    def post(self, request, *args, **kwargs):
        """Procesar subida de exámenes"""
        try:
            teacher = request.user.teacher

            form = ExamAccreditationForm(request.POST, request.FILES)

            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                
                course_id = request.POST.get("course_group_id", "")
                return redirect(f"/profesor/exam-accreditation/?course_id={course_id}")

            course_group_id = str(form.cleaned_data['course_group_id'])
            exam_number = int(form.cleaned_data['exam_number'])
            best_exam_file = form.cleaned_data['best_exam_file']
            worst_exam_file = form.cleaned_data['worst_exam_file']

            result = servicio_acreditacion_examenes.upload_exam_accreditation(
                teacher_id=str(teacher.id),
                course_group_id=course_group_id,
                exam_number=exam_number,
                best_exam_file=best_exam_file,
                worst_exam_file=worst_exam_file,
                ip_address=self._get_client_ip(request)
            )

            if result["success"]:
                stats = result.get('statistics', {})
                messages.success(
                    request, 
                    f"Acreditación del {result['exam_info']['exam_number']} parcial subida correctamente. "
                    f"Estadísticas: Promedio {stats.get('avg', 0):.2f}, "
                    f"Máxima {stats.get('max', 0):.2f}, Mínima {stats.get('min', 0):.2f}"
                )
            else:
                messages.error(request, f"Error: {result['error']}")

            return redirect(f"/profesor/exam-accreditation/?course_id={course_group_id}")

        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
            return redirect("/profesor/exam-accreditation/")
        except Exception as e:
            logger.error(f"Error procesando POST: {e}")
            messages.error(request, f"Error interno: {e}")
            return redirect("/profesor/exam-accreditation/")

    def _get_client_ip(self, request):
        xf = request.META.get("HTTP_X_FORWARDED_FOR")
        return xf.split(',')[0] if xf else request.META.get("REMOTE_ADDR")


# ============================================================
#   AJAX UPLOAD
# ============================================================

class ExamAccreditationUploadAjaxView(ProfesorRequiredMixin, View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            teacher = request.user.teacher

            course_group_id = request.POST.get("course_group_id")
            exam_number = request.POST.get("exam_number")
            best_exam_file = request.FILES.get("best_exam_file")
            worst_exam_file = request.FILES.get("worst_exam_file")

            if not all([course_group_id, exam_number, best_exam_file, worst_exam_file]):
                return JsonResponse({
                    "success": False, 
                    "error": "Faltan datos requeridos."
                }, status=400)

            result = servicio_acreditacion_examenes.upload_exam_accreditation(
                teacher_id=str(teacher.id),
                course_group_id=course_group_id,
                exam_number=int(exam_number),
                best_exam_file=best_exam_file,
                worst_exam_file=worst_exam_file,
                ip_address=request.META.get("REMOTE_ADDR")
            )

            return JsonResponse(result, status=200 if result["success"] else 400)

        except AttributeError:
            return JsonResponse({
                "success": False, 
                "error": "No se encontró perfil de profesor"
            }, status=403)
        except Exception as e:
            logger.error(f"AJAX ERROR: {e}")
            return JsonResponse({
                "success": False, 
                "error": str(e)
            }, status=500)


# ============================================================
#   DESCARGA DE ARCHIVOS
# ============================================================

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
    template_name = 'secretario/exam_accreditation/index.html'

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
                'filters_applied': filters
            })
            
        except Exception as e:
            logger.error(f"Error cargando acreditaciones para secretaría: {str(e)}")
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'accreditations': [],
                'total_accreditations': 0
            })
        
        return context