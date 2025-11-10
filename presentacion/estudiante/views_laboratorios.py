#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vistas para matrícula de laboratorios del estudiante
Permite matricularse en laboratorios A o B con horarios óptimos
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from repositorio.postgres_repository.models import (
    Student, Laboratory, LaboratoryEnrollment, CourseGroup, 
    Enrollment, AcademicPeriod, Course
)
from presentacion.estudiante.mixins import StudentRequiredMixin


@method_decorator(login_required, name='dispatch')
class StudentLaboratoriesView(StudentRequiredMixin, TemplateView):
    """Vista para mostrar laboratorios disponibles para matrícula"""
    template_name = 'estudiante/laboratorios/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            student = self.request.user.student
            
            # Obtener período académico activo
            active_period = AcademicPeriod.objects.filter(is_active=True).first()
            
            # Verificar si está en período de matrícula de laboratorios
            is_enrollment_period = self._is_lab_enrollment_period(active_period)
            
            # Obtener cursos matriculados que tienen laboratorios
            enrolled_courses = Enrollment.objects.filter(
                student=student,
                academic_period=active_period,
                status='active'
            ).select_related('course_group__course')
            
            # Obtener laboratorios disponibles
            available_labs = []
            enrolled_labs = []
            
            for enrollment in enrolled_courses:
                course_group = enrollment.course_group
                
                # Verificar si el curso tiene laboratorios
                labs = Laboratory.objects.filter(
                    course_group=course_group,
                    is_active=True
                ).annotate(
                    enrolled_count=Count('laboratoryenrollment')
                )
                
                if labs.exists():
                    # Verificar si ya está matriculado en algún laboratorio de este curso
                    current_enrollment = LaboratoryEnrollment.objects.filter(
                        student=student,
                        laboratory__course_group=course_group,
                        status='active'
                    ).first()
                    
                    if current_enrollment:
                        enrolled_labs.append({
                            'course': course_group.course,
                            'laboratory': current_enrollment.laboratory,
                            'enrollment': current_enrollment,
                            'can_change': is_enrollment_period
                        })
                    else:
                        # Mostrar laboratorios disponibles para este curso
                        lab_options = []
                        for lab in labs:
                            availability = self._calculate_lab_availability(lab)
                            lab_options.append({
                                'laboratory': lab,
                                'availability': availability,
                                'schedule_info': lab.schedule_info,
                                'can_enroll': availability['available_spots'] > 0 and is_enrollment_period
                            })
                        
                        if lab_options:
                            available_labs.append({
                                'course': course_group.course,
                                'course_group': course_group,
                                'laboratories': lab_options
                            })
            
            context.update({
                'student': student,
                'available_labs': available_labs,
                'enrolled_labs': enrolled_labs,
                'is_enrollment_period': is_enrollment_period,
                'active_period': active_period,
                'enrollment_deadline': active_period.laboratory_enrollment_end if active_period else None
            })
            
        except Student.DoesNotExist:
            messages.error(self.request, 'No se encontró información del estudiante')
            context.update({
                'available_labs': [],
                'enrolled_labs': [],
                'is_enrollment_period': False
            })
        except Exception as e:
            messages.error(self.request, f'Error al cargar laboratorios: {str(e)}')
            context.update({
                'available_labs': [],
                'enrolled_labs': [],
                'is_enrollment_period': False
            })
        
        return context
    
    def _is_lab_enrollment_period(self, period):
        """Verificar si estamos en período de matrícula de laboratorios"""
        if not period:
            return False
        
        now = timezone.now().date()
        return (period.laboratory_enrollment_start <= now <= period.laboratory_enrollment_end)
    
    def _calculate_lab_availability(self, laboratory):
        """Calcular disponibilidad del laboratorio"""
        enrolled_count = LaboratoryEnrollment.objects.filter(
            laboratory=laboratory,
            status='active'
        ).count()
        
        available_spots = laboratory.capacity - enrolled_count
        occupancy_percentage = (enrolled_count / laboratory.capacity) * 100 if laboratory.capacity > 0 else 100
        
        return {
            'enrolled_count': enrolled_count,
            'capacity': laboratory.capacity,
            'available_spots': available_spots,
            'occupancy_percentage': round(occupancy_percentage, 1),
            'is_full': available_spots <= 0
        }


@login_required
def enroll_in_laboratory(request, lab_id):
    """Matricular estudiante en un laboratorio"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        student = request.user.student
        laboratory = get_object_or_404(Laboratory, id=lab_id, is_active=True)
        
        # Verificar período de matrícula
        active_period = AcademicPeriod.objects.filter(is_active=True).first()
        if not active_period:
            return JsonResponse({'success': False, 'error': 'No hay período académico activo'})
        
        now = timezone.now().date()
        if not (active_period.laboratory_enrollment_start <= now <= active_period.laboratory_enrollment_end):
            return JsonResponse({'success': False, 'error': 'Fuera del período de matrícula de laboratorios'})
        
        # Verificar que el estudiante esté matriculado en el curso
        enrollment = Enrollment.objects.filter(
            student=student,
            course_group=laboratory.course_group,
            academic_period=active_period,
            status='active'
        ).first()
        
        if not enrollment:
            return JsonResponse({'success': False, 'error': 'No estás matriculado en este curso'})
        
        # Verificar que no esté ya matriculado en otro laboratorio del mismo curso
        existing_enrollment = LaboratoryEnrollment.objects.filter(
            student=student,
            laboratory__course_group=laboratory.course_group,
            status='active'
        ).first()
        
        if existing_enrollment:
            return JsonResponse({
                'success': False, 
                'error': f'Ya estás matriculado en el laboratorio {existing_enrollment.laboratory.lab_code}'
            })
        
        # Verificar disponibilidad
        enrolled_count = LaboratoryEnrollment.objects.filter(
            laboratory=laboratory,
            status='active'
        ).count()
        
        if enrolled_count >= laboratory.capacity:
            return JsonResponse({'success': False, 'error': 'Laboratorio lleno'})
        
        # Crear matrícula
        lab_enrollment = LaboratoryEnrollment.objects.create(
            student=student,
            laboratory=laboratory,
            enrollment_date=timezone.now().date(),
            status='active'
        )
        
        # Actualizar contador en el laboratorio
        laboratory.enrolled_students = enrolled_count + 1
        laboratory.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Matriculado exitosamente en {laboratory.lab_code}',
            'lab_code': laboratory.lab_code,
            'course_name': laboratory.course_group.course.name
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Estudiante no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def withdraw_from_laboratory(request, enrollment_id):
    """Retirar estudiante de un laboratorio"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        student = request.user.student
        enrollment = get_object_or_404(
            LaboratoryEnrollment, 
            id=enrollment_id, 
            student=student,
            status='active'
        )
        
        # Verificar período de cambios
        active_period = AcademicPeriod.objects.filter(is_active=True).first()
        if not active_period:
            return JsonResponse({'success': False, 'error': 'No hay período académico activo'})
        
        now = timezone.now().date()
        if now > active_period.enrollment_change_deadline:
            return JsonResponse({'success': False, 'error': 'Fuera del período de cambios de matrícula'})
        
        # Retirar matrícula
        laboratory = enrollment.laboratory
        enrollment.status = 'withdrawn'
        enrollment.save()
        
        # Actualizar contador en el laboratorio
        active_enrollments = LaboratoryEnrollment.objects.filter(
            laboratory=laboratory,
            status='active'
        ).count()
        
        laboratory.enrolled_students = active_enrollments
        laboratory.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Retirado exitosamente del laboratorio {laboratory.lab_code}'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Estudiante no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_laboratory_schedule(request, lab_id):
    """Obtener horario detallado de un laboratorio"""
    try:
        laboratory = get_object_or_404(Laboratory, id=lab_id)
        
        # Obtener información del horario
        schedule_info = laboratory.schedule_info or {}
        
        # Calcular disponibilidad
        availability = StudentLaboratoriesView()._calculate_lab_availability(None, laboratory)
        
        return JsonResponse({
            'success': True,
            'laboratory': {
                'code': laboratory.lab_code,
                'course': laboratory.course_group.course.name,
                'teacher': laboratory.teacher.user.get_full_name() if laboratory.teacher else 'Por asignar',
                'room': laboratory.lab_room,
                'schedule': schedule_info,
                'availability': availability
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def student_lab_summary(request):
    """Resumen de laboratorios del estudiante"""
    try:
        student = request.user.student
        
        # Obtener todas las matrículas de laboratorio
        lab_enrollments = LaboratoryEnrollment.objects.filter(
            student=student
        ).select_related(
            'laboratory__course_group__course',
            'laboratory__teacher__user'
        ).order_by('-enrollment_date')
        
        # Organizar por estado
        active_labs = lab_enrollments.filter(status='active')
        withdrawn_labs = lab_enrollments.filter(status='withdrawn')
        
        context = {
            'student': student,
            'active_labs': active_labs,
            'withdrawn_labs': withdrawn_labs,
            'total_labs': lab_enrollments.count(),
            'active_count': active_labs.count()
        }
        
        return render(request, 'estudiante/laboratorios/summary.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Estudiante no encontrado')
        return render(request, 'estudiante/laboratorios/summary.html', {})
    except Exception as e:
        messages.error(request, f'Error al cargar el resumen: {str(e)}')
        return render(request, 'estudiante/laboratorios/summary.html', {})