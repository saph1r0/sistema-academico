"""
Vistas simples para el módulo de profesores
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from repositorio.postgres_repository.models import (
    CourseGroup, Teacher, TeacherAttendance, CourseTopicContent, Enrollment
)
from servicios.servicioAsistenciaDocente import ServicioAsistenciaDocente
from servicios.servicioCalculadorProgreso import ProgressCalculator
from servicios.servicioContenidoCurso import CourseContentManager

class ProfesorDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard del profesor con clases reales, estadísticas de asistencia y progreso"""
    template_name = 'profesor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar que el usuario sea profesor
        if not self.request.user.is_teacher():
            messages.error(self.request, 'No tienes permisos de profesor.')
            return context
        
        try:
            # Obtener el profesor
            teacher = self.request.user.teacher
            
            # Obtener cursos asignados al profesor con información detallada
            cursos_asignados = CourseGroup.objects.filter(
                teacher=teacher
            ).select_related('course', 'academic_period')
            
            # Procesar cada curso para obtener estadísticas básicas
            cursos_con_estadisticas = []
            total_estudiantes = 0
            
            for curso in cursos_asignados:
                # Calcular número real de estudiantes matriculados
                try:
                    estudiantes_matriculados = Enrollment.objects.filter(
                        course_group=curso,
                        status='active'
                    ).count()
                except:
                    estudiantes_matriculados = curso.enrolled_students or 0
                
                # Obtener temas del curso
                try:
                    total_temas = CourseTopicContent.objects.filter(course_group=curso).count()
                    temas_completados = CourseTopicContent.objects.filter(
                        course_group=curso, is_completed=True
                    ).count()
                except:
                    total_temas = 0
                    temas_completados = 0
                
                # Determinar estado del curso basado en progreso
                progreso = curso.course_progress_percentage or 0
                if progreso >= 75:
                    estado = 'adelantado'
                    estado_color = 'green'
                elif progreso >= 50:
                    estado = 'normal'
                    estado_color = 'blue'
                elif progreso >= 25:
                    estado = 'atrasado'
                    estado_color = 'yellow'
                else:
                    estado = 'muy_atrasado'
                    estado_color = 'red'
                
                # Calcular porcentaje de asistencia docente
                try:
                    porcentaje_asistencia = (curso.classes_attended_by_teacher / curso.total_planned_classes * 100) if curso.total_planned_classes > 0 else 0
                except:
                    porcentaje_asistencia = 85.0
                
                curso_info = {
                    'curso': curso,
                    'total_estudiantes': estudiantes_matriculados,
                    'progreso_porcentaje': progreso,
                    'clases_asistidas': curso.classes_attended_by_teacher or 0,
                    'total_clases_programadas': curso.total_planned_classes or 68,
                    'porcentaje_asistencia_docente': round(porcentaje_asistencia, 1),
                    'total_temas': total_temas,
                    'temas_completados': temas_completados,
                    'estado': estado,
                    'estado_color': estado_color,
                    'progress_stats': {'success': True}
                }
                
                cursos_con_estadisticas.append(curso_info)
                total_estudiantes += estudiantes_matriculados
            
            # Calcular promedio de progreso de todos los cursos
            if cursos_con_estadisticas:
                promedio_progreso = sum(c['progreso_porcentaje'] for c in cursos_con_estadisticas) / len(cursos_con_estadisticas)
                promedio_asistencia = sum(c['porcentaje_asistencia_docente'] for c in cursos_con_estadisticas) / len(cursos_con_estadisticas)
            else:
                promedio_progreso = 0
                promedio_asistencia = 0
            
            # Obtener última sesión del profesor (si la tabla existe)
            ultima_sesion = None
            try:
                from django.db import connection
                # Verificar si la tabla existe antes de hacer la consulta
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass('teacher_attendance')")
                    table_exists = cursor.fetchone()[0] is not None
                
                if table_exists:
                    # Forzar la ejecución de la query para capturar errores aquí
                    query_result = TeacherAttendance.objects.filter(
                        teacher=teacher
                    ).order_by('-login_time')[:1]
                    ultima_sesion = list(query_result)[0] if query_result else None
            except Exception as e:
                # Si hay cualquier error, usar None
                ultima_sesion = None
            
            context.update({
                'cursos_asignados': cursos_con_estadisticas,
                'total_cursos': len(cursos_con_estadisticas),
                'total_estudiantes': total_estudiantes,
                'teacher': teacher,
                'estadisticas_generales': {'porcentaje_asistencia': round(promedio_asistencia, 1)},
                'promedio_progreso': round(promedio_progreso, 1),
                'impacto_progreso': [],
                'ultima_sesion': ultima_sesion,
                'fecha_actual': timezone.now().date(),
                # Estadísticas adicionales para las cards
                'total_horas_semanales': teacher.hours_per_week or 20,
                'porcentaje_asistencia_general': round(promedio_asistencia, 1),
                'total_clases_dictadas': sum(c['clases_asistidas'] for c in cursos_con_estadisticas),
                'total_clases_programadas': sum(c['total_clases_programadas'] for c in cursos_con_estadisticas)
            })
            
        except Exception as e:
            messages.error(self.request, f'Error cargando datos del dashboard: {str(e)}')
            context.update({
                'cursos_asignados': [],
                'total_cursos': 0,
                'total_estudiantes': 0,
                'teacher': self.request.user.teacher if hasattr(self.request.user, 'teacher') else None,
                'estadisticas_generales': {'porcentaje_asistencia': 0},
                'promedio_progreso': 0,
                'impacto_progreso': [],
                'ultima_sesion': None,
                'fecha_actual': timezone.now().date(),
                'total_horas_semanales': 20,
                'porcentaje_asistencia_general': 0,
                'total_clases_dictadas': 0,
                'total_clases_programadas': 0
            })
        
        return context


class ProfesorCourseDetailView(LoginRequiredMixin, TemplateView):
    """Vista de detalle de un curso específico del profesor"""
    template_name = 'profesor/course_detail.html'

    def post(self, request, *args, **kwargs):
        """Manejar acciones de gestión de temas del curso"""
        if not request.user.is_teacher():
            messages.error(request, 'No tienes permisos de profesor.')
            return redirect('profesor:dashboard')
        
        try:
            teacher = request.user.teacher
            course_group_id = kwargs.get('course_group_id')
            
            # Verificar que el curso pertenezca al profesor
            course_group = get_object_or_404(CourseGroup, id=course_group_id, teacher=teacher)
            
            # Inicializar servicio de contenido
            content_manager = CourseContentManager()
            
            action = request.POST.get('action')
            
            if action == 'upload_topics':
                # Subir múltiples temas del curso
                topics_data = []
                
                # Obtener temas desde el formulario
                topic_count = 0
                while f'topic_title_{topic_count}' in request.POST:
                    title = request.POST.get(f'topic_title_{topic_count}', '').strip()
                    description = request.POST.get(f'topic_description_{topic_count}', '').strip()
                    
                    if title:  # Solo agregar si tiene título
                        topics_data.append({
                            'title': title,
                            'description': description
                        })
                    
                    topic_count += 1
                
                if topics_data:
                    result = content_manager.upload_course_topics(
                        str(course_group_id), 
                        topics_data, 
                        str(teacher.id)
                    )
                    
                    if result['success']:
                        messages.success(request, result['message'])
                    else:
                        messages.error(request, result['error'])
                else:
                    messages.warning(request, 'No se proporcionaron temas válidos.')
            
            elif action == 'add_single_topic':
                # Agregar un solo tema
                title = request.POST.get('new_topic_title', '').strip()
                description = request.POST.get('new_topic_description', '').strip()
                
                if title:
                    result = content_manager.add_single_topic(
                        str(course_group_id),
                        {'title': title, 'description': description},
                        str(teacher.id)
                    )
                    
                    if result['success']:
                        messages.success(request, result['message'])
                    else:
                        messages.error(request, result['error'])
                else:
                    messages.warning(request, 'Debe proporcionar un título para el tema.')
            
            elif action == 'remove_topic':
                # Eliminar un tema
                topic_id = request.POST.get('topic_id')
                
                if topic_id:
                    result = content_manager.remove_topic(
                        str(course_group_id),
                        topic_id,
                        str(teacher.id)
                    )
                    
                    if result['success']:
                        messages.success(request, result['message'])
                    else:
                        messages.error(request, result['error'])
                else:
                    messages.warning(request, 'No se especificó el tema a eliminar.')
            
            elif action == 'bulk_upload':
                # Subida masiva de temas desde textarea
                bulk_topics = request.POST.get('bulk_topics', '').strip()
                
                if bulk_topics:
                    # Dividir por líneas y crear temas
                    lines = [line.strip() for line in bulk_topics.split('\n') if line.strip()]
                    topics_data = []
                    
                    for i, line in enumerate(lines):
                        # Permitir formato "Título - Descripción" o solo "Título"
                        if ' - ' in line:
                            title, description = line.split(' - ', 1)
                        else:
                            title = line
                            description = ''
                        
                        topics_data.append({
                            'title': title.strip(),
                            'description': description.strip()
                        })
                    
                    if topics_data:
                        result = content_manager.upload_course_topics(
                            str(course_group_id),
                            topics_data,
                            str(teacher.id)
                        )
                        
                        if result['success']:
                            messages.success(request, f'Se cargaron {len(topics_data)} temas exitosamente.')
                        else:
                            messages.error(request, result['error'])
                    else:
                        messages.warning(request, 'No se encontraron temas válidos en el texto.')
                else:
                    messages.warning(request, 'Debe proporcionar temas para cargar.')
            
            else:
                messages.warning(request, 'Acción no válida.')
        
        except Exception as e:
            messages.error(request, f'Error procesando la solicitud: {str(e)}')
        
        return redirect('profesor:course_detail', course_group_id=course_group_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Verificar que el usuario sea profesor
        if not self.request.user.is_teacher():
            messages.error(self.request, 'No tienes permisos de profesor.')
            return context
        
        try:
            # Obtener el profesor y el curso
            teacher = self.request.user.teacher
            course_group_id = kwargs.get('course_group_id')
            
            # Verificar que el curso pertenezca al profesor
            course_group = CourseGroup.objects.select_related(
                'course', 'academic_period'
            ).get(id=course_group_id, teacher=teacher)
            
            # Inicializar servicios
            servicio_asistencia = ServicioAsistenciaDocente()
            calculador_progreso = ProgressCalculator()
            
            # Obtener estadísticas detalladas del curso
            progress_stats = calculador_progreso.get_progress_statistics(str(course_group.id))
            
            # Obtener temas del curso
            temas = CourseTopicContent.objects.filter(
                course_group=course_group
            ).order_by('topic_order')
            
            # Obtener estudiantes matriculados
            estudiantes = Enrollment.objects.filter(
                course_group=course_group,
                status='active'
            ).select_related('student__user').count()
            
            # Obtener historial de asistencia del profesor para este curso
            # Usar lista vacía si la tabla no existe
            attendance_history = []
            try:
                from django.db import connection
                # Verificar si la tabla existe antes de hacer la consulta
                with connection.cursor() as cursor:
                    cursor.execute("SELECT to_regclass('teacher_attendance')")
                    table_exists = cursor.fetchone()[0] is not None
                
                if table_exists:
                    # Forzar la ejecución de la query con list() para capturar errores aquí
                    attendance_history = list(TeacherAttendance.objects.filter(
                        teacher=teacher
                    ).order_by('-login_time')[:10])  # Últimas 10 sesiones
            except Exception as e:
                # Si hay cualquier error, usar lista vacía
                attendance_history = []
            
            # Calcular estadísticas específicas del curso
            total_temas = temas.count()
            temas_completados = temas.filter(is_completed=True).count()
            
            # Determinar próximo tema a enseñar
            proximo_tema = temas.filter(is_completed=False).first()
            
            # Calcular porcentaje de asistencia docente
            attendance_percentage = 0
            if course_group.total_planned_classes and course_group.total_planned_classes > 0:
                attendance_percentage = (course_group.classes_attended_by_teacher or 0) * 100 / course_group.total_planned_classes
            
            context.update({
                'course_group': course_group,
                'teacher': teacher,
                'progress_stats': progress_stats,
                'temas': temas,
                'total_temas': total_temas,
                'temas_completados': temas_completados,
                'estudiantes_count': estudiantes,
                'attendance_history': attendance_history,
                'proximo_tema': proximo_tema,
                'porcentaje_temas_completados': (temas_completados / total_temas * 100) if total_temas > 0 else 0,
                'attendance_percentage': round(attendance_percentage, 1),
                'fecha_actual': timezone.now().date()
            })
            
        except CourseGroup.DoesNotExist:
            messages.error(self.request, 'Curso no encontrado o no tienes permisos para verlo.')
            context.update({
                'course_group': None,
                'error': True
            })
        except Exception as e:
            messages.error(self.request, f'Error cargando detalle del curso: {str(e)}')
            context.update({
                'course_group': None,
                'error': True
            })
        
        return context


class ProfesorAsistenciaView(LoginRequiredMixin, TemplateView):
    """Vista para gestión de asistencia del profesor"""
    template_name = 'profesor/asistencia/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not self.request.user.is_teacher():
            messages.error(self.request, 'No tienes permisos de profesor.')
            return context
        
        try:
            teacher = self.request.user.teacher
            
            # Obtener cursos del profesor
            cursos = CourseGroup.objects.filter(teacher=teacher).select_related('course')
            
            context.update({
                'teacher': teacher,
                'cursos': cursos,
                'fecha_actual': timezone.now().date()
            })
            
        except Exception as e:
            messages.error(self.request, f'Error cargando asistencia: {str(e)}')
        
        return context


class ProfesorReservasView(LoginRequiredMixin, TemplateView):
    """Vista para gestión de reservas del profesor"""
    template_name = 'profesor/reservas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not self.request.user.is_teacher():
            messages.error(self.request, 'No tienes permisos de profesor.')
            return context
        
        try:
            teacher = self.request.user.teacher
            
            # Obtener cursos del profesor
            cursos = CourseGroup.objects.filter(teacher=teacher).select_related('course')
            
            context.update({
                'teacher': teacher,
                'cursos': cursos,
                'fecha_actual': timezone.now().date()
            })
            
        except Exception as e:
            messages.error(self.request, f'Error cargando reservas: {str(e)}')
        
        return context


class ProfesorDebugDataView(LoginRequiredMixin, TemplateView):
    """Vista de debug para verificar datos del profesor"""
    template_name = 'profesor/debug/data.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not self.request.user.is_teacher():
            messages.error(self.request, 'No tienes permisos de profesor.')
            return context
        
        try:
            teacher = self.request.user.teacher
            
            # Información de debug
            debug_info = {
                'teacher_id': str(teacher.id),
                'teacher_code': teacher.teacher_code,
                'user_email': teacher.user.institutional_email,
                'cursos_count': CourseGroup.objects.filter(teacher=teacher).count(),
                'fecha_creacion': teacher.created_at,
            }
            
            # Obtener cursos con detalles
            cursos = CourseGroup.objects.filter(teacher=teacher).select_related('course', 'academic_period')
            
            context.update({
                'teacher': teacher,
                'debug_info': debug_info,
                'cursos': cursos,
                'fecha_actual': timezone.now()
            })
            
        except Exception as e:
            messages.error(self.request, f'Error en debug: {str(e)}')
        
        return context


class ProfesorDebugProcessExcelView(LoginRequiredMixin, TemplateView):
    """Vista de debug para procesar Excel"""
    template_name = 'profesor/debug/process_excel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not self.request.user.is_teacher():
            messages.error(self.request, 'No tienes permisos de profesor.')
            return context
        
        try:
            teacher = self.request.user.teacher
            
            context.update({
                'teacher': teacher,
                'fecha_actual': timezone.now()
            })
            
        except Exception as e:
            messages.error(self.request, f'Error en debug Excel: {str(e)}')
        
        return context