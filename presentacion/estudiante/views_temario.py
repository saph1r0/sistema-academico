# apps/estudiante/views/temario.py
"""
Vista del temario para estudiantes
"""
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from presentacion.estudiante.mixins import EstudianteRequiredMixin
from repositorio.postgres_repository.models import (
    Student, Enrollment, CourseGroup, Syllabus
)


class EstudianteCursoTemarioView(EstudianteRequiredMixin, TemplateView):
    """Vista del temario de un curso para el estudiante"""
    template_name = 'estudiante/curso_temario.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_group_id = self.kwargs.get('course_group_id')
        
        try:
            # Obtener estudiante
            student = Student.objects.get(user=self.request.user)
            
            # Obtener curso
            course_group = get_object_or_404(CourseGroup, id=course_group_id)
            
            # Verificar que el estudiante está matriculado
            enrollment = Enrollment.objects.filter(
                student=student,
                course_group=course_group,
                status='active'
            ).first()
            
            if not enrollment:
                context.update({
                    'error': 'No estás matriculado en este curso',
                    'has_access': False
                })
                return context
            
            # Obtener sílabo
            try:
                syllabus = Syllabus.objects.get(course_group=course_group)
                has_syllabus = True
                
                # Obtener temas con subtemas
                main_topics = syllabus.main_topics.prefetch_related('subtopics').all()
                
                # Calcular progreso
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
                'has_access': True,
                'student': student,
                'course_group': course_group,
                'course': course_group.course,
                'has_syllabus': has_syllabus,
                'syllabus': syllabus,
                'main_topics': main_topics,
                'progress_info': progress_info,
            })
            
        except Student.DoesNotExist:
            context.update({
                'error': 'No se encontró información de estudiante',
                'has_access': False
            })
        except Exception as e:
            context.update({
                'error': f'Error al cargar temario: {str(e)}',
                'has_access': False
            })
        
        return context


class EstudianteMisCursosView(EstudianteRequiredMixin, TemplateView):
    """Vista de lista de cursos matriculados del estudiante"""
    template_name = 'estudiante/cursos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            student = Student.objects.get(user=self.request.user)
            
            # Obtener matrículas activas
            enrollments = Enrollment.objects.filter(
                student=student,
                status='active'
            ).select_related('course_group__course', 'course_group__teacher__user')
            
            # Obtener información de cada curso
            courses_info = []
            for enrollment in enrollments:
                course_group = enrollment.course_group
                
                # Verificar si tiene sílabo
                try:
                    syllabus = Syllabus.objects.get(course_group=course_group)
                    has_syllabus = True
                    progress_info = syllabus.get_topics_progress()
                except Syllabus.DoesNotExist:
                    has_syllabus = False
                    progress_info = {
                        'progress_percentage': 0,
                        'current_week': 0,
                        'total_weeks': 16
                    }
                
                courses_info.append({
                    'enrollment': enrollment,
                    'course_group': course_group,
                    'course': course_group.course,
                    'teacher': course_group.teacher,
                    'has_syllabus': has_syllabus,
                    'progress_info': progress_info
                })
            
            context.update({
                'student': student,
                'courses_info': courses_info,
            })
            
        except Student.DoesNotExist:
            context.update({
                'error': 'No se encontró información de estudiante'
            })
        except Exception as e:
            context.update({
                'error': f'Error al cargar cursos: {str(e)}'
            })
        
        return context