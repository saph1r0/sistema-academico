#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para subida de notas por fases académicas
Implementa Requirements: 4.1, 4.2, 4.3, 4.4
"""

import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError

from .mixins import ProfesorRequiredMixin
from .forms import SubirNotasFaseForm
from servicios.servicioExcelNotas import ExcelGradeProcessingService
from servicios.servicioEstadisticasNotas import (
    servicio_estadisticas_notas, 
    servicio_generador_graficos,
    update_statistics_after_grade_upload
)
from repositorio.postgres_repository.models import CourseGroup, Teacher

logger = logging.getLogger(__name__)


class TeacherGradeUploadView(ProfesorRequiredMixin, TemplateView):
    """
    Vista principal para subida de notas por fases académicas
    Implementa Requirements: 4.1, 4.2, 4.3, 4.4
    """
    template_name = 'profesor/grade_upload/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener el profesor
            teacher = self.request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener cursos asignados al profesor
            course_groups = CourseGroup.objects.filter(
                teacher=teacher
            ).select_related('course', 'academic_period').order_by('course__name')
            
            # Preparar datos de cursos con información de notas existentes
            courses_data = []
            for course_group in course_groups:
                course_data = {
                    'id': str(course_group.id),
                    'course_name': course_group.course.name,
                    'course_code': course_group.course.code,
                    'group_code': course_group.group_code,
                    'academic_period': course_group.academic_period.name,
                    'enrolled_students': course_group.enrolled_students,
                    'phases_status': {}
                }
                
                # Verificar estado de notas por fase
                for phase in ['primera', 'segunda', 'tercera']:
                    stats = servicio_estadisticas_notas.calculate_basic_statistics(
                        str(course_group.id), phase
                    )
                    
                    if stats['success']:
                        course_data['phases_status'][phase] = {
                            'has_grades': stats['statistics']['graded_students'] > 0,
                            'graded_students': stats['statistics']['graded_students'],
                            'total_students': stats['statistics']['total_students'],
                            'average_grade': stats['statistics']['average_grade']
                        }
                    else:
                        course_data['phases_status'][phase] = {
                            'has_grades': False,
                            'graded_students': 0,
                            'total_students': course_group.enrolled_students,
                            'average_grade': 0
                        }
                
                courses_data.append(course_data)
            
            # Obtener curso seleccionado
            selected_course_id = self.request.GET.get('course_id')
            selected_course = None
            selected_phase = self.request.GET.get('phase', 'primera')
            
            if selected_course_id:
                selected_course = next(
                    (c for c in courses_data if c['id'] == selected_course_id), 
                    None
                )
            
            # Obtener estadísticas del curso seleccionado
            statistics_data = {}
            if selected_course:
                stats_result = servicio_generador_graficos.generate_statistics_summary_data(
                    selected_course_id, selected_phase
                )
                
                if stats_result['success']:
                    statistics_data = stats_result['teacher_summary']
                else:
                    # Si no hay datos, crear estructura vacía para evitar errores en template
                    statistics_data = {
                        'grade_metrics': {
                            'average_grade': 0,
                            'max_grade': 0,
                            'min_grade': 0,
                            'approval_rate': 0
                        },
                        'key_metrics': {
                            'graded_students': 0,
                            'total_enrolled': 0
                        },
                        'distribution_summary': {
                            'poor': {'count': 0},
                            'regular': {'count': 0},
                            'good': {'count': 0},
                            'excellent': {'count': 0}
                        }
                    }
            
            # Preparar formulario
            initial_data = {}
            if selected_course_id:
                initial_data['course_group_id'] = selected_course_id
            if selected_phase:
                initial_data['phase'] = selected_phase
            
            upload_form = SubirNotasFaseForm(initial=initial_data)
            
            context.update({
                'courses': courses_data,
                'selected_course': selected_course,
                'selected_phase': selected_phase,
                'statistics_data': statistics_data,
                'upload_form': upload_form,
                'phase_choices': [
                    {'value': 'primera', 'label': 'Primera Fase'},
                    {'value': 'segunda', 'label': 'Segunda Fase'},
                    {'value': 'tercera', 'label': 'Tercera Fase'},
                ]
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'courses': [],
                'selected_course': None,
                'statistics_data': {},
                'upload_form': SubirNotasFaseForm()
            })
        except Exception as e:
            logger.error(f"Error cargando datos de subida de notas: {str(e)}")
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'courses': [],
                'selected_course': None,
                'statistics_data': {},
                'upload_form': SubirNotasFaseForm()
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """
        Procesar subida de archivo Excel de notas
        Implementa Requirements: 4.1, 4.2, 4.4
        """
        try:
            teacher = request.user.teacher
            teacher_id = str(teacher.id)
            
            # Validar formulario
            form = SubirNotasFaseForm(request.POST, request.FILES)
            
            if not form.is_valid():
                messages.error(request, 'Datos del formulario inválidos.')
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                return redirect('profesor:grade_upload')
            
            # Obtener datos del formulario
            course_group_id = form.cleaned_data['course_group_id']
            phase = form.cleaned_data['phase']
            archivo_excel = form.cleaned_data['archivo_excel']
            allow_duplicates = form.cleaned_data['allow_duplicates']
            
            # Validar que el profesor tenga acceso al curso
            course_group = get_object_or_404(
                CourseGroup, 
                id=course_group_id, 
                teacher=teacher
            )
            
            # TODO: Verificar que las fechas estén habilitadas para subir notas
            # if not self._verify_submission_period_active(phase):
            #     messages.error(request, f'Las fechas para subir notas de {phase} fase no están habilitadas.')
            #     return redirect('profesor:grade_upload')
            
            # Procesar archivo Excel
            processing_service = ExcelGradeProcessingService(teacher_id)
            
            result = processing_service.process_and_upload_grades(
                file_path_or_buffer=archivo_excel,
                course_group_id=str(course_group_id),
                phase=phase,
                allow_duplicates=allow_duplicates
            )
            
            if result['success']:
                # Actualizar estadísticas
                update_statistics_after_grade_upload(str(course_group_id), phase)
                
                # Preparar mensaje de éxito
                summary = result['summary']
                upload_stats = summary['database_upload']
                
                success_msg = (
                    f'Notas de {phase} fase procesadas exitosamente. '
                    f'Creadas: {upload_stats["grades_created"]}, '
                    f'Actualizadas: {upload_stats["grades_updated"]}'
                )
                
                if upload_stats['invalid_students'] > 0:
                    success_msg += f', Estudiantes no encontrados: {upload_stats["invalid_students"]}'
                
                messages.success(request, success_msg)
                
                # Mostrar warnings si los hay
                processing_result = result['processing_result']
                if processing_result.get('warnings'):
                    for warning in processing_result['warnings'][:5]:  # Mostrar primeros 5 warnings
                        messages.warning(request, f'Advertencia: {warning}')
                
            else:
                # Manejar errores
                error_msg = result.get('error', 'Error desconocido procesando archivo')
                messages.error(request, f'Error: {error_msg}')
                
                # Mostrar errores específicos si los hay
                if 'processing_result' in result and result['processing_result'].get('errors'):
                    for error in result['processing_result']['errors'][:3]:  # Mostrar primeros 3 errores
                        messages.error(request, f'Error de procesamiento: {error}')
                
                if 'upload_result' in result and result['upload_result'].get('errors'):
                    for error in result['upload_result']['errors'][:3]:  # Mostrar primeros 3 errores
                        messages.error(request, f'Error de base de datos: {error}')
            
            # Redirigir con parámetros para mantener selección
            return redirect(f'profesor:grade_upload?course_id={course_group_id}&phase={phase}')
            
        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
            return redirect('profesor:grade_upload')
        except ValidationError as e:
            messages.error(request, f'Error de validación: {str(e)}')
            return redirect('profesor:grade_upload')
        except Exception as e:
            logger.error(f"Error procesando subida de notas: {str(e)}")
            messages.error(request, f'Error interno: {str(e)}')
            return redirect('profesor:grade_upload')

    def _verify_submission_period_active(self, phase):
        """
        Verificar si el período de subida de notas está activo
        TODO: Implementar con modelo GradeSubmissionPeriod
        """
        # Por ahora retorna True para permitir pruebas
        return True


class GradeUploadAjaxView(ProfesorRequiredMixin, View):
    """
    Vista AJAX para subida de notas con respuesta JSON
    Implementa Requirements: 4.1, 4.2, 4.4
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Procesar subida AJAX de archivo Excel"""
        try:
            teacher = request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener datos del request
            course_group_id = request.POST.get('course_group_id')
            phase = request.POST.get('phase')
            allow_duplicates = request.POST.get('allow_duplicates') == 'true'
            archivo_excel = request.FILES.get('archivo_excel')
            
            # Validaciones básicas
            if not all([course_group_id, phase, archivo_excel]):
                return JsonResponse({
                    'success': False,
                    'error': 'Faltan datos requeridos: course_group_id, phase, archivo_excel'
                }, status=400)
            
            # Validar acceso al curso
            try:
                course_group = CourseGroup.objects.get(id=course_group_id, teacher=teacher)
            except CourseGroup.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No tiene acceso a este curso'
                }, status=403)
            
            # Procesar archivo
            processing_service = ExcelGradeProcessingService(teacher_id)
            
            result = processing_service.process_and_upload_grades(
                file_path_or_buffer=archivo_excel,
                course_group_id=course_group_id,
                phase=phase,
                allow_duplicates=allow_duplicates
            )
            
            if result['success']:
                # Actualizar estadísticas
                update_statistics_after_grade_upload(course_group_id, phase)
                
                # Preparar respuesta de éxito
                summary = result['summary']
                
                return JsonResponse({
                    'success': True,
                    'message': f'Notas de {phase} fase procesadas exitosamente',
                    'summary': summary,
                    'course_group_id': course_group_id,
                    'phase': phase,
                    'processed_at': timezone.now().isoformat()
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Error procesando archivo'),
                    'details': {
                        'processing_errors': result.get('processing_result', {}).get('errors', []),
                        'upload_errors': result.get('upload_result', {}).get('errors', [])
                    }
                }, status=400)
                
        except AttributeError:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró perfil de profesor'
            }, status=403)
        except Exception as e:
            logger.error(f"Error en subida AJAX de notas: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=500)


class GradeStatisticsAjaxView(ProfesorRequiredMixin, View):
    """
    Vista AJAX para obtener estadísticas de notas
    Implementa Requirements: 3.1, 3.2, 3.3
    """
    
    def get(self, request, *args, **kwargs):
        """Obtener estadísticas y datos de gráficos"""
        try:
            teacher = request.user.teacher
            
            course_group_id = request.GET.get('course_group_id')
            phase = request.GET.get('phase', 'primera')
            
            if not course_group_id:
                return JsonResponse({
                    'success': False,
                    'error': 'course_group_id requerido'
                }, status=400)
            
            # Validar acceso al curso
            try:
                course_group = CourseGroup.objects.get(id=course_group_id, teacher=teacher)
            except CourseGroup.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No tiene acceso a este curso'
                }, status=403)
            
            # Obtener estadísticas completas
            stats_result = servicio_generador_graficos.generate_combined_chart_data(
                course_group_id, phase
            )
            
            if not stats_result['success']:
                return JsonResponse({
                    'success': False,
                    'error': stats_result.get('error', 'Error obteniendo estadísticas')
                }, status=500)
            
            return JsonResponse({
                'success': True,
                'statistics': stats_result,
                'course_group_id': course_group_id,
                'phase': phase,
                'generated_at': timezone.now().isoformat()
            })
            
        except AttributeError:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró perfil de profesor'
            }, status=403)
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas AJAX: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=500)


class TeacherStatisticsDashboardView(ProfesorRequiredMixin, TemplateView):
    """
    Vista para dashboard de estadísticas con gráficos
    Implementa Requirements: 3.1, 3.2, 3.3, 3.4
    """
    template_name = 'profesor/grade_upload/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener el profesor
            teacher = self.request.user.teacher
            
            # Obtener cursos asignados al profesor
            course_groups = CourseGroup.objects.filter(
                teacher=teacher
            ).select_related('course', 'academic_period').order_by('course__name')
            
            # Preparar datos de cursos
            courses_data = []
            for course_group in course_groups:
                courses_data.append({
                    'id': str(course_group.id),
                    'course_name': course_group.course.name,
                    'course_code': course_group.course.code,
                    'group_code': course_group.group_code,
                    'academic_period': course_group.academic_period.name,
                    'enrolled_students': course_group.enrolled_students,
                })
            
            # Obtener curso y fase seleccionados
            selected_course_id = self.request.GET.get('course_id')
            selected_phase = self.request.GET.get('phase', 'primera')
            view_type = self.request.GET.get('view_type', 'detailed')
            
            selected_course = None
            statistics_data = {}
            
            if selected_course_id:
                selected_course = next(
                    (c for c in courses_data if c['id'] == selected_course_id), 
                    None
                )
                
                if selected_course:
                    # Obtener estadísticas completas
                    stats_result = servicio_generador_graficos.generate_statistics_summary_data(
                        selected_course_id, selected_phase
                    )
                    
                    if stats_result['success']:
                        statistics_data = stats_result['teacher_summary']
                    else:
                        # Si no hay datos, crear estructura vacía para evitar errores en template
                        statistics_data = {
                            'grade_metrics': {
                                'average_grade': 0,
                                'max_grade': 0,
                                'min_grade': 0,
                                'approval_rate': 0
                            },
                            'key_metrics': {
                                'graded_students': 0,
                                'total_enrolled': 0
                            },
                            'distribution_summary': {
                                'poor': {'count': 0},
                                'regular': {'count': 0},
                                'good': {'count': 0},
                                'excellent': {'count': 0}
                            }
                        }
            
            # Debug: Imprimir datos para verificar
            print(f"DEBUG - Statistics data: {statistics_data}")
            print(f"DEBUG - Selected course: {selected_course}")
            print(f"DEBUG - Selected phase: {selected_phase}")
            
            context.update({
                'courses': courses_data,
                'selected_course': selected_course,
                'selected_phase': selected_phase,
                'view_type': view_type,
                'statistics_data': statistics_data,
                'phase_choices': [
                    {'value': 'primera', 'label': 'Primera Fase'},
                    {'value': 'segunda', 'label': 'Segunda Fase'},
                    {'value': 'tercera', 'label': 'Tercera Fase'},
                ]
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'courses': [],
                'selected_course': None,
                'statistics_data': {},
            })
        except Exception as e:
            logger.error(f"Error cargando dashboard de estadísticas: {str(e)}")
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'courses': [],
                'selected_course': None,
                'statistics_data': {},
            })
        
        return context


class DownloadExcelTemplateView(ProfesorRequiredMixin, View):
    """
    Vista para descargar plantilla Excel de notas
    Implementa Requirements: 4.1, 4.2
    """
    
    def get(self, request, *args, **kwargs):
        """Generar y descargar plantilla Excel"""
        try:
            import io
            import xlsxwriter
            from repositorio.postgres_repository.models import Student, Enrollment
            
            teacher = request.user.teacher
            course_group_id = request.GET.get('course_group_id')
            phase = request.GET.get('phase', 'primera')
            
            if not course_group_id:
                messages.error(request, 'Debe especificar un curso.')
                return redirect('profesor:grade_upload')
            
            # Validar acceso al curso
            try:
                course_group = CourseGroup.objects.get(id=course_group_id, teacher=teacher)
            except CourseGroup.DoesNotExist:
                messages.error(request, 'No tiene acceso a este curso.')
                return redirect('profesor:grade_upload')
            
            # Obtener estudiantes matriculados
            try:
                enrollments = Enrollment.objects.filter(
                    course_group=course_group,
                    status='active'
                ).select_related('student__user').order_by('student__student_code')
                
                students = [enrollment.student for enrollment in enrollments]
            except:
                # Si no existe tabla de matrículas, usar estudiantes de ejemplo
                students = []
                logger.warning(f"No se pudieron obtener estudiantes matriculados para curso {course_group_id}")
            
            # Si no hay estudiantes, crear algunos de ejemplo
            if not students:
                students = [
                    type('Student', (), {
                        'student_code': '20240001',
                        'user': type('User', (), {
                            'get_full_name': lambda: 'Estudiante Ejemplo 1'
                        })()
                    })(),
                    type('Student', (), {
                        'student_code': '20240002',
                        'user': type('User', (), {
                            'get_full_name': lambda: 'Estudiante Ejemplo 2'
                        })()
                    })(),
                    type('Student', (), {
                        'student_code': '20240003',
                        'user': type('User', (), {
                            'get_full_name': lambda: 'Estudiante Ejemplo 3'
                        })()
                    })(),
                ]
            
            # Crear archivo Excel
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet(f'Notas {phase.title()} Fase')
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            cell_format = workbook.add_format({'border': 1})
            number_format = workbook.add_format({'border': 1, 'num_format': '0.00'})
            
            # Encabezados
            headers = [
                'codigo_estudiante', 
                'nombre_estudiante', 
                'nota_parcial', 
                'nota_continua'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Datos de estudiantes
            for row, student in enumerate(students, 1):
                worksheet.write(row, 0, student.student_code, cell_format)
                worksheet.write(row, 1, student.user.get_full_name(), cell_format)
                worksheet.write(row, 2, '', number_format)  # nota_parcial vacía
                worksheet.write(row, 3, '', number_format)  # nota_continua vacía
            
            # Ajustar ancho de columnas
            worksheet.set_column('A:A', 18)  # codigo_estudiante
            worksheet.set_column('B:B', 30)  # nombre_estudiante
            worksheet.set_column('C:C', 15)  # nota_parcial
            worksheet.set_column('D:D', 15)  # nota_continua
            
            # Agregar instrucciones en una hoja separada
            instructions_sheet = workbook.add_worksheet('Instrucciones')
            
            instruction_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
            title_format = workbook.add_format({'bold': True, 'font_size': 14})
            
            instructions = [
                'INSTRUCCIONES PARA SUBIR NOTAS',
                '',
                '1. Complete las columnas "nota_parcial" y "nota_continua" con valores entre 0 y 20',
                '2. Use punto decimal (ejemplo: 15.5) para notas con decimales',
                '3. NO modifique las columnas "codigo_estudiante" y "nombre_estudiante"',
                '4. Guarde el archivo y súbalo en el sistema',
                '',
                'IMPORTANTE:',
                '- Las notas deben estar entre 0.00 y 20.00',
                '- Puede dejar celdas vacías si no tiene la nota aún',
                '- El sistema calculará automáticamente el promedio de fase',
                '',
                f'Plantilla generada para: {course_group.course.name} - {course_group.group_code}',
                f'Fase: {phase.title()}',
                f'Fecha: {timezone.now().strftime("%d/%m/%Y %H:%M")}'
            ]
            
            for row, instruction in enumerate(instructions):
                if row == 0:
                    instructions_sheet.write(row, 0, instruction, title_format)
                else:
                    instructions_sheet.write(row, 0, instruction, instruction_format)
            
            instructions_sheet.set_column('A:A', 80)
            
            workbook.close()
            output.seek(0)
            
            # Preparar respuesta
            filename = f'plantilla_notas_{phase}_{course_group.course.code}_{course_group.group_code}.xlsx'
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
            return redirect('profesor:grade_upload')
        except Exception as e:
            logger.error(f"Error generando plantilla Excel: {str(e)}")
            messages.error(request, f'Error generando plantilla: {str(e)}')
            return redirect('profesor:grade_upload')