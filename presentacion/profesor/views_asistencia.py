#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para gestión de asistencia del profesor
Registro simple: PRESENTE/FALTA
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
import json
from django.urls import reverse

from .mixins import ProfesorRequiredMixin
from servicios.servicioAsistencia import servicio_asistencia
from servicios.servicioNotas import servicio_notas
from repositorio.postgres_repository.models import SimpleAttendanceRecord, Student, CourseGroup, Enrollment


class asistencia(ProfesorRequiredMixin, TemplateView):
    """Vista principal para registro de asistencia con PRESENTE/FALTA"""
    template_name = 'profesor/asistencia/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = self.request.user.teacher
            
            # Obtener cursos del profesor
            cursos = self._obtener_cursos_profesor(teacher)
            
            # Obtener curso seleccionado
            curso_seleccionado = None
            estudiantes = []
            fecha_seleccionada = timezone.now().date()
            
            course_group_id = self.request.GET.get('course_group_id')
            if course_group_id and cursos:
                curso_seleccionado = next(
                    (c for c in cursos if str(c['id']) == course_group_id), 
                    None
                )
                
                if curso_seleccionado:
                    # Obtener fecha seleccionada (hoy por defecto)
                    fecha_str = self.request.GET.get('fecha', timezone.now().date().isoformat())
                    try:
                        fecha_seleccionada = date.fromisoformat(fecha_str)
                    except ValueError:
                        fecha_seleccionada = timezone.now().date()
                    
                    # Obtener estudiantes del curso con su asistencia
                    estudiantes = self._obtener_estudiantes_con_asistencia(
                        course_group_id, fecha_seleccionada
                    )
            
            context.update({
                'cursos': cursos,
                'curso_seleccionado': curso_seleccionado,
                'estudiantes': estudiantes,
                'fecha_seleccionada': fecha_seleccionada,
                'fecha_hoy': timezone.now().date(),
                'total_estudiantes': len(estudiantes),
                'estados_asistencia': [
                    {'value': 'PRESENTE', 'label': 'Presente', 'class': 'success'},
                    {'value': 'FALTA', 'label': 'Falta', 'class': 'danger'}
                ]
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'estudiantes': [],
                'fecha_seleccionada': timezone.now().date(),
                'total_estudiantes': 0
            })
        except Exception as e:
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'estudiantes': [],
                'fecha_seleccionada': timezone.now().date(),
                'total_estudiantes': 0
            })
        
        return context
    
    def _obtener_cursos_profesor(self, teacher):
        """Obtener cursos asignados al profesor"""
        try:
            course_groups = CourseGroup.objects.filter(teacher=teacher).select_related('course', 'academic_period')
            cursos = []
            
            for cg in course_groups:
                cursos.append({
                    'id': cg.id,
                    'course_name': cg.course.name,
                    'course_code': cg.course.code,
                    'group_code': cg.group_code,
                    'academic_period': cg.academic_period.name,
                    'display_name': f"{cg.course.code} - {cg.course.name} (Grupo {cg.group_code})"
                })
            
            return cursos
        except Exception as e:
            return []
    
    def _obtener_estudiantes_con_asistencia(self, course_group_id, fecha):
        """Obtener estudiantes matriculados con su asistencia del día"""
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener estudiantes matriculados
            enrollments = Enrollment.objects.filter(
                course_group=course_group,
                status='active'
            ).select_related('student__user')
            
            estudiantes = []
            
            for enrollment in enrollments:
                student = enrollment.student
                
                # Verificar asistencia para la fecha específica
                attendance_record = SimpleAttendanceRecord.objects.filter(
                    student=student,
                    course_group=course_group,
                    class_date=fecha
                ).first()
                
                # Calcular estadísticas de asistencia
                total_records = SimpleAttendanceRecord.objects.filter(
                    student=student,
                    course_group=course_group
                ).count()
                
                present_count = SimpleAttendanceRecord.objects.filter(
                    student=student,
                    course_group=course_group,
                    status='PRESENTE'
                ).count()
                
                attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
                
                estudiantes.append({
                    'id': str(student.id),
                    'student_code': student.student_code,
                    'full_name': student.user.get_full_name(),
                    'email': student.user.institutional_email,
                    'current_status': attendance_record.status if attendance_record else None,
                    'has_attendance_today': attendance_record is not None,
                    'attendance_stats': {
                        'total_classes': total_records,
                        'present_count': present_count,
                        'absent_count': total_records - present_count,
                        'percentage': round(attendance_percentage, 1)
                    }
                })
            
            return estudiantes
            
        except CourseGroup.DoesNotExist:
            return []
        except Exception as e:
            return []

    def post(self, request, *args, **kwargs):
        """Registrar asistencia de la clase con validación de duplicados"""
        try:
            teacher = request.user.teacher
            
            # Obtener datos del formulario
            course_group_id = request.POST.get('course_group_id')
            fecha_str = request.POST.get('fecha')
            accion = request.POST.get('accion')
            
            if not all([course_group_id, fecha_str]):
                messages.error(request, 'Datos incompletos: curso y fecha son requeridos.')
                return redirect('profesor:asistencia')
            
            try:
                fecha = date.fromisoformat(fecha_str)
                course_group = CourseGroup.objects.get(id=course_group_id)
            except ValueError:
                messages.error(request, 'Fecha inválida.')
                return redirect('profesor:asistencia')
            except CourseGroup.DoesNotExist:
                messages.error(request, 'Curso no encontrado.')
                return redirect('profesor:asistencia')
            
            # Verificar que el profesor puede tomar asistencia en este curso
            if course_group.teacher != teacher:
                messages.error(request, 'No tiene permisos para tomar asistencia en este curso.')
                return redirect('profesor:asistencia')
            
            # Procesar según la acción
            if accion == 'marcar_todos_presentes':
                resultado = self._marcar_todos_presentes(teacher, course_group, fecha)
                
                if resultado['success']:
                    messages.success(
                        request, 
                        f'Todos los estudiantes marcados como presentes. '
                        f'Registros creados: {resultado["created"]}, actualizados: {resultado["updated"]}'
                    )
                    if resultado['errors']:
                        messages.warning(request, f'Errores encontrados: {len(resultado["errors"])}')
                else:
                    messages.error(request, f'Error: {resultado["error"]}')
            
            elif accion == 'registrar_asistencia':
                resultado = self._registrar_asistencia_individual(teacher, course_group, fecha, request.POST)
                
                if resultado['success']:
                    messages.success(
                        request, 
                        f'Asistencia registrada exitosamente. '
                        f'Registros creados: {resultado["created"]}, actualizados: {resultado["updated"]}'
                    )
                    if resultado['errors']:
                        messages.warning(request, f'Errores encontrados: {len(resultado["errors"])}')
                else:
                    messages.error(request, f'Error: {resultado["error"]}')
 
            # Obtenemos la URL base primero
            base_url = reverse('profesor:asistencia')
            # Concatenamos los parámetros manualmente
            return redirect(f'{base_url}?course_group_id={course_group_id}&fecha={fecha_str}')
   
            
        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
        except Exception as e:
            messages.error(request, f'Error procesando asistencia: {str(e)}')
        
        return redirect('profesor:asistencia')
    
    def _marcar_todos_presentes(self, teacher, course_group, fecha):
        """Marcar todos los estudiantes como presentes"""
        try:
            # Obtener estudiantes matriculados
            enrollments = Enrollment.objects.filter(
                course_group=course_group,
                status='active'
            ).select_related('student')
            
            attendance_data = []
            for enrollment in enrollments:
                attendance_data.append({
                    'student_id': str(enrollment.student.id),
                    'status': 'PRESENTE'
                })
            
            if not attendance_data:
                return {'success': False, 'error': 'No hay estudiantes matriculados en este curso'}
            
            # Usar el método de registro masivo del modelo
            created, updated, errors = SimpleAttendanceRecord.record_bulk_attendance(
                teacher=teacher,
                course_group=course_group,
                class_date=fecha,
                attendance_data=attendance_data
            )
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _registrar_asistencia_individual(self, teacher, course_group, fecha, post_data):
        """Registrar asistencia individual de estudiantes"""
        try:
            attendance_data = []
            
            # Extraer datos de asistencia del POST
            for key, value in post_data.items():
                if key.startswith('asistencia_'):
                    student_id = key.replace('asistencia_', '')
                    status = value
                    
                    if status in ['PRESENTE', 'FALTA']:
                        attendance_data.append({
                            'student_id': student_id,
                            'status': status
                        })
            
            if not attendance_data:
                return {'success': False, 'error': 'No se encontraron datos de asistencia para registrar'}
            
            # Usar el método de registro masivo del modelo
            created, updated, errors = SimpleAttendanceRecord.record_bulk_attendance(
                teacher=teacher,
                course_group=course_group,
                class_date=fecha,
                attendance_data=attendance_data
            )
            
            return {
                'success': True,
                'created': created,
                'updated': updated,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ProfesorReporteAsistenciaView(ProfesorRequiredMixin, TemplateView):
    """Vista para reportes de asistencia"""
    template_name = 'profesor/asistencia/reporte.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = self.request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener cursos del profesor
            cursos = servicio_notas.obtener_cursos_profesor(teacher_id)
            
            # Obtener curso seleccionado
            curso_seleccionado = None
            reporte_data = {}
            
            course_group_id = self.request.GET.get('course_group_id')
            if course_group_id and cursos:
                curso_seleccionado = next(
                    (c for c in cursos if c['course_group_id'] == course_group_id), 
                    None
                )
                
                if curso_seleccionado:
                    # Obtener fechas del reporte (último mes por defecto)
                    from datetime import timedelta
                    fecha_fin = timezone.now().date()
                    fecha_inicio = fecha_fin - timedelta(days=30)
                    
                    # Obtener parámetros de fecha si se proporcionan
                    fecha_inicio_str = self.request.GET.get('fecha_inicio')
                    fecha_fin_str = self.request.GET.get('fecha_fin')
                    
                    if fecha_inicio_str:
                        try:
                            fecha_inicio = date.fromisoformat(fecha_inicio_str)
                        except ValueError:
                            pass
                    
                    if fecha_fin_str:
                        try:
                            fecha_fin = date.fromisoformat(fecha_fin_str)
                        except ValueError:
                            pass
                    
                    # Obtener reporte de asistencia
                    reporte_data = servicio_asistencia.obtener_reporte_asistencia(
                        course_group_id, fecha_inicio, fecha_fin
                    )
                    
                    if not reporte_data.get('success'):
                        messages.error(self.request, f'Error generando reporte: {reporte_data.get("error", "Error desconocido")}')
                        reporte_data = {}
            
            context.update({
                'cursos': cursos,
                'curso_seleccionado': curso_seleccionado,
                'reporte': reporte_data,
                'fecha_inicio': reporte_data.get('periodo', {}).get('fecha_inicio'),
                'fecha_fin': reporte_data.get('periodo', {}).get('fecha_fin')
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'reporte': {}
            })
        except Exception as e:
            messages.error(self.request, f'Error cargando reporte: {str(e)}')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'reporte': {}
            })
        
        return context


class ProfesorAsistenciaRapidaAPIView(ProfesorRequiredMixin, TemplateView):
    """API para registro rápido de asistencia"""
    
    def post(self, request, *args, **kwargs):
        """Cambiar estado de asistencia de un estudiante específico"""
        try:
            teacher = request.user.teacher
            
            # Obtener datos JSON
            data = json.loads(request.body)
            
            student_id = data.get('student_id')
            course_group_id = data.get('course_group_id')
            fecha_str = data.get('fecha')
            nuevo_estado = data.get('estado')
            
            if not all([student_id, course_group_id, fecha_str, nuevo_estado]):
                return JsonResponse({'error': 'Datos incompletos'}, status=400)
            
            if nuevo_estado not in ['PRESENTE', 'FALTA']:
                return JsonResponse({'error': 'Estado inválido. Use PRESENTE o FALTA'}, status=400)
            
            try:
                fecha = date.fromisoformat(fecha_str)
                course_group = CourseGroup.objects.get(id=course_group_id)
                student = Student.objects.get(id=student_id)
            except ValueError:
                return JsonResponse({'error': 'Fecha inválida'}, status=400)
            except (CourseGroup.DoesNotExist, Student.DoesNotExist):
                return JsonResponse({'error': 'Curso o estudiante no encontrado'}, status=404)
            
            # Verificar permisos del profesor
            if course_group.teacher != teacher:
                return JsonResponse({'error': 'No tiene permisos para este curso'}, status=403)
            
            # Verificar que el estudiante está matriculado
            enrollment = Enrollment.objects.filter(
                student=student,
                course_group=course_group,
                status='active'
            ).first()
            
            if not enrollment:
                return JsonResponse({'error': 'Estudiante no matriculado en este curso'}, status=400)
            
            # Crear o actualizar registro de asistencia
            attendance, created = SimpleAttendanceRecord.objects.update_or_create(
                student=student,
                course_group=course_group,
                class_date=fecha,
                defaults={
                    'status': nuevo_estado,
                    'recorded_by': teacher,
                    'session_info': {
                        'api_update': True,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Asistencia {"creada" if created else "actualizada"} a {nuevo_estado}',
                'nuevo_estado': nuevo_estado,
                'created': created,
                'student_name': student.user.get_full_name()
            })
            
        except AttributeError:
            return JsonResponse({'error': 'No se encontró perfil de profesor'}, status=403)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ProfesorAsistenciaHistorialView(ProfesorRequiredMixin, TemplateView):
    """Vista para historial y estadísticas de asistencia"""
    template_name = 'profesor/asistencia/historial.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = self.request.user.teacher
            
            # Obtener cursos del profesor
            cursos = self._obtener_cursos_profesor(teacher)
            
            # Obtener curso seleccionado
            curso_seleccionado = None
            estadisticas = {}
            historial = []
            
            course_group_id = self.request.GET.get('course_group_id')
            if course_group_id and cursos:
                curso_seleccionado = next(
                    (c for c in cursos if str(c['id']) == course_group_id), 
                    None
                )
                
                if curso_seleccionado:
                    # Obtener fechas del período (último mes por defecto)
                    from datetime import timedelta
                    fecha_fin = timezone.now().date()
                    fecha_inicio = fecha_fin - timedelta(days=30)
                    
                    # Obtener parámetros de fecha si se proporcionan
                    fecha_inicio_str = self.request.GET.get('fecha_inicio')
                    fecha_fin_str = self.request.GET.get('fecha_fin')
                    
                    if fecha_inicio_str:
                        try:
                            fecha_inicio = date.fromisoformat(fecha_inicio_str)
                        except ValueError:
                            pass
                    
                    if fecha_fin_str:
                        try:
                            fecha_fin = date.fromisoformat(fecha_fin_str)
                        except ValueError:
                            pass
                    
                    # Obtener estadísticas y historial
                    estadisticas = self._calcular_estadisticas_curso(course_group_id, fecha_inicio, fecha_fin)
                    historial = self._obtener_historial_asistencia(course_group_id, fecha_inicio, fecha_fin)
            
            context.update({
                'cursos': cursos,
                'curso_seleccionado': curso_seleccionado,
                'estadisticas': estadisticas,
                'historial': historial,
                'fecha_inicio': fecha_inicio if 'fecha_inicio' in locals() else None,
                'fecha_fin': fecha_fin if 'fecha_fin' in locals() else None
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'estadisticas': {},
                'historial': []
            })
        except Exception as e:
            messages.error(self.request, f'Error cargando historial: {str(e)}')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'estadisticas': {},
                'historial': []
            })
        
        return context
    
    def _obtener_cursos_profesor(self, teacher):
        """Obtener cursos asignados al profesor"""
        try:
            course_groups = CourseGroup.objects.filter(teacher=teacher).select_related('course', 'academic_period')
            cursos = []
            
            for cg in course_groups:
                cursos.append({
                    'id': cg.id,
                    'course_name': cg.course.name,
                    'course_code': cg.course.code,
                    'group_code': cg.group_code,
                    'academic_period': cg.academic_period.name,
                    'display_name': f"{cg.course.code} - {cg.course.name} (Grupo {cg.group_code})"
                })
            
            return cursos
        except Exception as e:
            return []
    
    def _calcular_estadisticas_curso(self, course_group_id, fecha_inicio, fecha_fin):
        """Calcular estadísticas de asistencia del curso"""
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener todos los registros del período
            records = SimpleAttendanceRecord.objects.filter(
                course_group=course_group,
                class_date__range=[fecha_inicio, fecha_fin]
            )
            
            total_records = records.count()
            present_records = records.filter(status='PRESENTE').count()
            absent_records = records.filter(status='FALTA').count()
            
            # Calcular porcentaje promedio
            attendance_percentage = (present_records / total_records * 100) if total_records > 0 else 0
            
            # Contar estudiantes únicos
            unique_students = records.values('student').distinct().count()
            
            # Contar clases únicas
            unique_dates = records.values('class_date').distinct().count()
            
            return {
                'total_records': total_records,
                'present_records': present_records,
                'absent_records': absent_records,
                'attendance_percentage': round(attendance_percentage, 1),
                'unique_students': unique_students,
                'unique_dates': unique_dates,
                'period_start': fecha_inicio,
                'period_end': fecha_fin
            }
            
        except CourseGroup.DoesNotExist:
            return {}
        except Exception as e:
            return {}
    
    def _obtener_historial_asistencia(self, course_group_id, fecha_inicio, fecha_fin):
        """Obtener historial detallado de asistencia"""
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener registros ordenados por fecha
            records = SimpleAttendanceRecord.objects.filter(
                course_group=course_group,
                class_date__range=[fecha_inicio, fecha_fin]
            ).select_related('student__user').order_by('-class_date', 'student__student_code')
            
            # Agrupar por fecha
            historial_por_fecha = {}
            
            for record in records:
                fecha_str = record.class_date.isoformat()
                
                if fecha_str not in historial_por_fecha:
                    historial_por_fecha[fecha_str] = {
                        'fecha': record.class_date,
                        'registros': [],
                        'total_presente': 0,
                        'total_falta': 0
                    }
                
                historial_por_fecha[fecha_str]['registros'].append({
                    'student_code': record.student.student_code,
                    'student_name': record.student.user.get_full_name(),
                    'status': record.status,
                    'recorded_at': record.recorded_at
                })
                
                if record.status == 'PRESENTE':
                    historial_por_fecha[fecha_str]['total_presente'] += 1
                else:
                    historial_por_fecha[fecha_str]['total_falta'] += 1
            
            # Convertir a lista ordenada
            historial = list(historial_por_fecha.values())
            historial.sort(key=lambda x: x['fecha'], reverse=True)
            
            return historial
            
        except CourseGroup.DoesNotExist:
            return []
        except Exception as e:
            return []