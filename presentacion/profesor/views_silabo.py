# apps/profesor/views/syllabus.py
"""
Vistas completas para la gestión de sílabo del profesor con selección de curso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

from .mixins import ProfesorRequiredMixin
from repositorio.postgres_repository.models import (
    CourseGroup, AcademicPeriod, Teacher, Course,
    Syllabus, SyllabusMainTopic, SyllabusSubTopic
)


class ProfesorMisCursosView(ProfesorRequiredMixin, TemplateView):
    """Vista de lista de cursos del profesor"""
    template_name = 'profesor/silabo/mis_cursos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            
            # Obtener todos los cursos asignados al profesor
            course_groups = CourseGroup.objects.filter(
                teacher=teacher
            ).select_related('course', 'academic_period').order_by('course__name')
            
            # Preparar información de cada curso
            courses_info = []
            for course_group in course_groups:
                # Verificar si tiene sílabo
                try:
                    syllabus = Syllabus.objects.get(course_group=course_group)
                    has_syllabus = True
                    progress_info = syllabus.get_topics_progress()
                except Syllabus.DoesNotExist:
                    has_syllabus = False
                    progress_info = {
                        'progress_percentage': 0,
                        'total_topics': 0,
                        'completed_topics': 0
                    }
                
                courses_info.append({
                    'course_group': course_group,
                    'course': course_group.course,
                    'has_syllabus': has_syllabus,
                    'progress_info': progress_info
                })
            
            context.update({
                'teacher': teacher,
                'courses_info': courses_info,
            })
            
        except Teacher.DoesNotExist:
            context.update({
                'error': 'No se encontró información de profesor'
            })
        except Exception as e:
            context.update({
                'error': f'Error al cargar cursos: {str(e)}'
            })
        
        return context


class ProfesorSilaboView(ProfesorRequiredMixin, TemplateView):
    """Vista principal de gestión de sílabo para un curso específico"""
    template_name = 'profesor/silabo/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_group_id = self.kwargs.get('course_group_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            
            # Obtener curso específico
            course_group = get_object_or_404(
                CourseGroup, 
                id=course_group_id,
                teacher=teacher
            )
            
            # Verificar si existe sílabo
            try:
                syllabus = Syllabus.objects.get(course_group=course_group)
                has_syllabus = True
                
                # Obtener temas principales con subtemas
                main_topics = syllabus.main_topics.prefetch_related('subtopics').all()
                
                # Calcular estadísticas
                progress_info = syllabus.get_topics_progress()
                
            except Syllabus.DoesNotExist:
                syllabus = None
                has_syllabus = False
                main_topics = []
                progress_info = {
                    'total_topics': 0,
                    'completed_topics': 0,
                    'current_week': 0,
                    'total_weeks': 16,
                    'progress_percentage': 0
                }
            
            context.update({
                'has_course': True,
                'course_group': course_group,
                'course': course_group.course,
                'has_syllabus': has_syllabus,
                'syllabus': syllabus,
                'main_topics': main_topics,
                'progress_info': progress_info,
            })
            
        except Teacher.DoesNotExist:
            context.update({
                'error': 'No se encontró información de profesor',
                'has_course': False
            })
        except Exception as e:
            context.update({
                'error': f'Error al cargar datos: {str(e)}',
                'has_course': False
            })
        
        return context


class SubirSilaboView(ProfesorRequiredMixin, View):
    """Vista para subir el sílabo en bloque"""
    
    def get(self, request, course_group_id, *args, **kwargs):
        """Muestra el formulario de carga"""
        try:
            teacher = get_object_or_404(Teacher, user=request.user)
            course_group = get_object_or_404(
                CourseGroup,
                id=course_group_id,
                teacher=teacher
            )
            
            # Verificar si ya tiene sílabo
            if hasattr(course_group, 'syllabus'):
                messages.warning(request, 'Ya has subido un sílabo para este curso. Puedes editarlo.')
                return redirect('profesor:silabo', course_group_id=course_group_id)
            
            context = {
                'course_group': course_group,
                'course': course_group.course,
            }
            return render(request, 'profesor/silabo/subir.html', context)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('profesor:mis_cursos')
    
    @transaction.atomic
    def post(self, request, course_group_id, *args, **kwargs):
        """Procesa la carga del sílabo"""
        try:
            teacher = get_object_or_404(Teacher, user=request.user)
            course_group = get_object_or_404(
                CourseGroup,
                id=course_group_id,
                teacher=teacher
            )
            
            # Verificar si ya existe sílabo
            if hasattr(course_group, 'syllabus'):
                messages.error(request, 'Ya existe un sílabo para este curso')
                return redirect('profesor:silabo', course_group_id=course_group_id)
            
            # Obtener período académico activo
            academic_period = AcademicPeriod.objects.filter(is_active=True).first()
            if not academic_period:
                messages.error(request, 'No hay período académico activo')
                return redirect('profesor:mis_cursos')
            
            # Obtener datos del formulario
            total_weeks = int(request.POST.get('total_weeks', 16))
            start_date_str = request.POST.get('start_date')
            
            if not start_date_str:
                messages.error(request, 'Debes especificar la fecha de inicio')
                return redirect('profesor:subir_silabo', course_group_id=course_group_id)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date + timedelta(weeks=total_weeks)
            
            # Crear sílabo
            syllabus = Syllabus.objects.create(
                course_group=course_group,
                academic_period=academic_period,
                uploaded_by=teacher,
                total_weeks=total_weeks,
                start_date=start_date,
                end_date=end_date
            )
            
            # Procesar temas principales
            main_topics_count = int(request.POST.get('main_topics_count', 0))
            
            if main_topics_count < 1:
                syllabus.delete()
                raise ValueError('Debes agregar al menos un tema principal')
            
            topics_created = 0
            
            for i in range(1, main_topics_count + 1):
                title = request.POST.get(f'main_topic_{i}_title', '').strip()
                description = request.POST.get(f'main_topic_{i}_description', '').strip()
                
                if not title:
                    continue
                
                # Crear tema principal
                main_topic = SyllabusMainTopic.objects.create(
                    syllabus=syllabus,
                    order=topics_created + 1,
                    title=title,
                    description=description
                )
                
                topics_created += 1
                
                # Procesar subtemas (opcional)
                subtopics_count = int(request.POST.get(f'main_topic_{i}_subtopics_count', 0))
                
                for j in range(1, subtopics_count + 1):
                    subtopic_title = request.POST.get(f'main_topic_{i}_subtopic_{j}', '').strip()
                    
                    if subtopic_title:
                        SyllabusSubTopic.objects.create(
                            main_topic=main_topic,
                            order=j,
                            title=subtopic_title
                        )
            
            if topics_created == 0:
                syllabus.delete()
                messages.error(request, 'No se creó ningún tema. Debes agregar al menos un tema.')
                return redirect('profesor:subir_silabo', course_group_id=course_group_id)
            
            messages.success(request, f'Sílabo subido exitosamente con {topics_created} temas principales.')
            return redirect('profesor:silabo', course_group_id=course_group_id)
            
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('profesor:subir_silabo', course_group_id=course_group_id)
        except Exception as e:
            messages.error(request, f'Error al subir sílabo: {str(e)}')
            return redirect('profesor:subir_silabo', course_group_id=course_group_id)


class EditarSilaboView(ProfesorRequiredMixin, View):
    """Vista para editar el sílabo existente"""
    
    def get(self, request, course_group_id, *args, **kwargs):
        """Muestra el formulario de edición"""
        try:
            teacher = get_object_or_404(Teacher, user=request.user)
            course_group = get_object_or_404(
                CourseGroup,
                id=course_group_id,
                teacher=teacher
            )
            
            try:
                syllabus = Syllabus.objects.get(course_group=course_group)
                main_topics = syllabus.main_topics.prefetch_related('subtopics').all()
                
                # Preparar datos de temas para JavaScript
                topics_data = []
                for topic in main_topics:
                    subtopics_data = []
                    for subtopic in topic.subtopics.all():
                        subtopics_data.append({
                            'order': subtopic.order,
                            'title': subtopic.title
                        })
                    
                    topics_data.append({
                        'order': topic.order,
                        'topic_name': topic.title,
                        'description': topic.description or '',
                        'subtopics': subtopics_data
                    })
                
                context = {
                    'course_group': course_group,
                    'course': course_group.course,
                    'syllabus': syllabus,
                    'main_topics': json.dumps(topics_data),
                }
                return render(request, 'profesor/silabo/editar.html', context)
                
            except Syllabus.DoesNotExist:
                messages.error(request, 'No has subido un sílabo aún para este curso')
                return redirect('profesor:subir_silabo', course_group_id=course_group_id)
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('profesor:mis_cursos')
    
    @transaction.atomic
    def post(self, request, course_group_id, *args, **kwargs):
        """Procesa la edición del sílabo"""
        try:
            teacher = get_object_or_404(Teacher, user=request.user)
            course_group = get_object_or_404(
                CourseGroup,
                id=course_group_id,
                teacher=teacher
            )
            syllabus = get_object_or_404(Syllabus, course_group=course_group)
            
            # Actualizar fechas si es necesario
            start_date_str = request.POST.get('start_date')
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                syllabus.start_date = start_date
                syllabus.end_date = start_date + timedelta(weeks=syllabus.total_weeks)
                syllabus.save()
            
            # Eliminar temas existentes y crear nuevos
            syllabus.main_topics.all().delete()
            
            # Procesar temas principales
            main_topics_count = int(request.POST.get('main_topics_count', 0))
            
            if main_topics_count < 1:
                messages.error(request, 'Debes tener al menos un tema principal')
                return redirect('profesor:editar_silabo', course_group_id=course_group_id)
            
            topics_created = 0
            
            for i in range(1, main_topics_count + 1):
                title = request.POST.get(f'main_topic_{i}_title', '').strip()
                description = request.POST.get(f'main_topic_{i}_description', '').strip()
                
                if not title:
                    continue
                
                main_topic = SyllabusMainTopic.objects.create(
                    syllabus=syllabus,
                    order=topics_created + 1,
                    title=title,
                    description=description
                )
                
                topics_created += 1
                
                # Procesar subtemas
                subtopics_count = int(request.POST.get(f'main_topic_{i}_subtopics_count', 0))
                
                for j in range(1, subtopics_count + 1):
                    subtopic_title = request.POST.get(f'main_topic_{i}_subtopic_{j}', '').strip()
                    
                    if subtopic_title:
                        SyllabusSubTopic.objects.create(
                            main_topic=main_topic,
                            order=j,
                            title=subtopic_title
                        )
            
            if topics_created == 0:
                messages.error(request, 'No se actualizó ningún tema. Debes tener al menos un tema.')
                return redirect('profesor:editar_silabo', course_group_id=course_group_id)
            
            messages.success(request, f'Sílabo actualizado exitosamente con {topics_created} temas principales.')
            return redirect('profesor:silabo', course_group_id=course_group_id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar sílabo: {str(e)}')
            return redirect('profesor:editar_silabo', course_group_id=course_group_id)


class EliminarSilaboView(ProfesorRequiredMixin, View):
    """Vista para eliminar el sílabo (opcional)"""
    
    def post(self, request, course_group_id, *args, **kwargs):
        """Elimina el sílabo"""
        try:
            teacher = get_object_or_404(Teacher, user=request.user)
            course_group = get_object_or_404(
                CourseGroup,
                id=course_group_id,
                teacher=teacher
            )
            
            try:
                syllabus = Syllabus.objects.get(course_group=course_group)
                syllabus.delete()
                messages.success(request, 'Sílabo eliminado exitosamente')
                return JsonResponse({'success': True})
            except Syllabus.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'No existe sílabo para eliminar'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})