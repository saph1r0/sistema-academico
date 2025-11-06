#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vistas para el módulo de notas del estudiante
Permite ver notas por fases (primera, segunda, tercera) usando PhaseGrade model
Implementa Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.4
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Avg, Max, Min, Count

from repositorio.postgres_repository.models import (
    Student, Grade, Course, CourseGroup, Enrollment, AcademicPeriod, PhaseGrade
)
from presentacion.estudiante.mixins import EstudianteRequiredMixin
from servicios.servicioEstadisticasNotas import servicio_generador_graficos
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class StudentGradesView(EstudianteRequiredMixin, TemplateView):
    """
    Vista para mostrar las notas del estudiante por fases usando PhaseGrade model
    Implementa Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.4
    """
    template_name = 'estudiante/notas/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            student = self.request.user.student
            
            # Obtener período académico activo
            active_period = AcademicPeriod.objects.filter(is_active=True).first()
            
            # Obtener matrículas del estudiante
            enrollments = Enrollment.objects.filter(
                student=student,
                academic_period=active_period,
                status='active'
            ).select_related('course_group__course', 'course_group__teacher__user')
            
            # Organizar notas por curso y fase usando PhaseGrade
            courses_data = []
            total_final_grades = []
            
            for enrollment in enrollments:
                course_group = enrollment.course_group
                course = course_group.course
                
                # Obtener notas por fases para este curso
                phase_grades = PhaseGrade.objects.filter(
                    student=student,
                    course_group=course_group
                ).order_by('phase')
                
                # Organizar notas por fases
                phases_data = {
                    'primera': None,
                    'segunda': None,
                    'tercera': None
                }
                
                # Obtener estadísticas de clase para contexto
                class_statistics = {}
                
                for phase_grade in phase_grades:
                    phase = phase_grade.phase
                    
                    # Obtener estadísticas de la clase para esta fase
                    stats_data = servicio_generador_graficos.generate_statistics_summary_data(
                        str(course_group.id), phase
                    )
                    
                    if stats_data['success']:
                        class_stats = stats_data['student_summary']['class_statistics']
                        class_statistics[phase] = class_stats
                    
                    phases_data[phase] = {
                        'partial_grade': float(phase_grade.partial_grade),
                        'continuous_grade': float(phase_grade.continuous_grade),
                        'final_grade': float(phase_grade.final_phase_grade) if phase_grade.final_phase_grade else None,
                        'uploaded_at': phase_grade.uploaded_at,
                        'has_grades': True,
                        'class_statistics': class_statistics.get(phase, {})
                    }
                
                # Calcular promedio del curso (solo fases con notas)
                available_grades = [
                    phases_data[phase]['final_grade'] 
                    for phase in ['primera', 'segunda', 'tercera'] 
                    if phases_data[phase] and phases_data[phase]['final_grade'] is not None
                ]
                
                course_average = None
                if available_grades:
                    course_average = round(sum(available_grades) / len(available_grades), 2)
                    total_final_grades.append(course_average)
                
                courses_data.append({
                    'course': course,
                    'course_group': course_group,
                    'enrollment': enrollment,
                    'phases': phases_data,
                    'average': course_average,
                    'status': self._get_course_status(course_average),
                    'teacher_name': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar'
                })
            
            # Calcular promedio general
            general_average = None
            if total_final_grades:
                general_average = round(sum(total_final_grades) / len(total_final_grades), 2)
            
            context.update({
                'student': student,
                'courses_data': courses_data,
                'active_period': active_period,
                'total_courses': len(courses_data),
                'general_average': general_average,
                'passed_courses': len([c for c in courses_data if c['status'] == 'aprobado']),
                'failed_courses': len([c for c in courses_data if c['status'] == 'desaprobado']),
                'pending_courses': len([c for c in courses_data if c['status'] == 'pendiente']),
                'courses_with_grades': len([c for c in courses_data if c['average'] is not None])
            })
            
        except Student.DoesNotExist:
            messages.error(self.request, 'No se encontró información del estudiante')
            context['courses_data'] = []
            context['general_average'] = 0
        except Exception as e:
            messages.error(self.request, f'Error al cargar las notas: {str(e)}')
            context['courses_data'] = []
            context['general_average'] = 0
        
        return context
    
    def _get_student_position_in_class(self, student_grade, class_statistics):
        """
        Determina la posición relativa del estudiante en la clase
        
        Args:
            student_grade: Nota del estudiante
            class_statistics: Estadísticas de la clase
            
        Returns:
            String describiendo la posición del estudiante
        """
        if not student_grade or not class_statistics:
            return "Sin datos suficientes"
        
        class_avg = class_statistics.get('class_average', 0)
        
        if student_grade >= class_statistics.get('highest_grade', 20):
            return "Mejor nota de la clase"
        elif student_grade <= class_statistics.get('lowest_grade', 0):
            return "Nota más baja de la clase"
        elif student_grade > class_avg:
            diff = round(student_grade - class_avg, 1)
            return f"Por encima del promedio (+{diff})"
        elif student_grade < class_avg:
            diff = round(class_avg - student_grade, 1)
            return f"Por debajo del promedio (-{diff})"
        else:
            return "En el promedio de la clase"
    
    def _get_course_status(self, average):
        """Determinar el estado del curso basado en el promedio"""
        if average is None:
            return 'pendiente'
        elif average >= 10.5:
            return 'aprobado'
        else:
            return 'desaprobado'


@login_required
def get_course_grades_detail(request, course_id):
    """API para obtener detalle de notas de un curso específico"""
    try:
        student = request.user.student
        course = get_object_or_404(Course, id=course_id)
        
        # Verificar que el estudiante esté matriculado en el curso
        enrollment = Enrollment.objects.filter(
            student=student,
            course_group__course=course,
            status='active'
        ).first()
        
        if not enrollment:
            return JsonResponse({
                'success': False,
                'error': 'No estás matriculado en este curso'
            })
        
        # Obtener todas las notas del curso
        grades = Grade.objects.filter(
            student=student,
            course=course
        ).order_by('exam_type', 'grade_component')
        
        # Organizar datos para el gráfico
        grades_data = []
        for grade in grades:
            grades_data.append({
                'component': grade.grade_component,
                'score': float(grade.grade),
                'exam_type': grade.get_exam_type_display(),
                'date': grade.created_at.strftime('%Y-%m-%d')
            })
        
        # Calcular estadísticas
        scores = [float(g.grade) for g in grades]
        statistics = {
            'count': len(scores),
            'average': round(sum(scores) / len(scores), 2) if scores else 0,
            'max': max(scores) if scores else 0,
            'min': min(scores) if scores else 0
        }
        
        return JsonResponse({
            'success': True,
            'course_name': course.name,
            'grades': grades_data,
            'statistics': statistics
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Estudiante no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def student_grades_summary(request):
    """Vista para resumen general de notas del estudiante"""
    try:
        student = request.user.student
        
        # Obtener período académico activo
        active_period = AcademicPeriod.objects.filter(is_active=True).first()
        
        # Estadísticas generales
        total_enrollments = Enrollment.objects.filter(
            student=student,
            academic_period=active_period,
            status='active'
        ).count()
        
        # Cursos con notas
        courses_with_grades = Grade.objects.filter(
            student=student
        ).values('course').distinct().count()
        
        # Promedio general
        all_grades = Grade.objects.filter(student=student)
        general_average = all_grades.aggregate(Avg('grade'))['grade__avg']
        
        context = {
            'student': student,
            'total_courses': total_enrollments,
            'courses_with_grades': courses_with_grades,
            'courses_pending': total_enrollments - courses_with_grades,
            'general_average': round(general_average, 2) if general_average else 0,
            'active_period': active_period
        }
        
        return render(request, 'estudiante/notas/summary.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Estudiante no encontrado')
        return render(request, 'estudiante/notas/summary.html', {})
    except Exception as e:
        messages.error(request, f'Error al cargar el resumen: {str(e)}')
        return render(request, 'estudiante/notas/summary.html', {})