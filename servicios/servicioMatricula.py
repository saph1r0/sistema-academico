#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de matrícula de laboratorios
Maneja matrícula en laboratorios A y B con horarios
"""

import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count

from repositorio.postgres_repository.models import (
    Student, Laboratory, LaboratoryEnrollment, CourseGroup, Course, User
)

logger = logging.getLogger(__name__)


class ServicioMatricula:
    """
    Servicio para manejo de matrícula de laboratorios
    """
    
    def __init__(self):
        self.logger = logger
    
    def obtener_laboratorios_disponibles(self, student_id: str) -> Dict:
        """
        Obtener laboratorios disponibles para un estudiante
        
        Args:
            student_id: ID del estudiante
            
        Returns:
            Dict con laboratorios disponibles organizados por curso
        """
        try:
            student = Student.objects.get(id=student_id)
            
            # Obtener cursos en los que está matriculado el estudiante
            from repositorio.postgres_repository.models import Enrollment
            enrollments = Enrollment.objects.filter(
                student=student,
                status='active'
            ).select_related('course_group__course')
            
            laboratorios_por_curso = {}
            
            for enrollment in enrollments:
                course_group = enrollment.course_group
                course = course_group.course
                
                # Buscar laboratorios para este curso
                laboratories = Laboratory.objects.filter(
                    course_group=course_group,
                    is_active=True
                ).order_by('lab_code')
                
                if laboratories.exists():
                    # Verificar si ya está matriculado en algún laboratorio de este curso
                    existing_enrollment = LaboratoryEnrollment.objects.filter(
                        student=student,
                        laboratory__course_group=course_group,
                        status='active'
                    ).first()
                    
                    labs_info = []
                    for lab in laboratories:
                        # Contar estudiantes matriculados
                        enrolled_count = LaboratoryEnrollment.objects.filter(
                            laboratory=lab,
                            status='active'
                        ).count()
                        
                        # Verificar disponibilidad
                        is_available = enrolled_count < lab.capacity
                        
                        # Verificar si es el laboratorio actual del estudiante
                        is_current = existing_enrollment and existing_enrollment.laboratory == lab
                        
                        labs_info.append({
                            'lab_id': str(lab.id),
                            'lab_code': lab.lab_code,
                            'capacity': lab.capacity,
                            'enrolled_count': enrolled_count,
                            'available_spots': lab.capacity - enrolled_count,
                            'is_available': is_available,
                            'is_current': is_current,
                            'schedule_info': lab.schedule_info,
                            'lab_room': lab.lab_room,
                            'teacher_name': lab.teacher.user.get_full_name() if lab.teacher else 'Sin asignar'
                        })
                    
                    laboratorios_por_curso[course.name] = {
                        'course_id': str(course.id),
                        'course_name': course.name,
                        'course_code': course.code,
                        'group_code': course_group.group_code,
                        'laboratories': labs_info,
                        'current_enrollment': {
                            'lab_id': str(existing_enrollment.laboratory.id),
                            'lab_code': existing_enrollment.laboratory.lab_code,
                            'enrollment_date': existing_enrollment.enrollment_date.isoformat()
                        } if existing_enrollment else None
                    }
            
            return {
                'success': True,
                'student_name': student.user.get_full_name(),
                'student_code': student.student_code,
                'laboratorios_por_curso': laboratorios_por_curso,
                'total_cursos_con_lab': len(laboratorios_por_curso),
                'fecha_consulta': timezone.now().isoformat()
            }
            
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Estudiante no encontrado',
                'error_code': 'STUDENT_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo laboratorios disponibles: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def matricular_laboratorio(self, student_id: str, laboratory_id: str) -> Dict:
        """
        Matricular estudiante en un laboratorio
        
        Args:
            student_id: ID del estudiante
            laboratory_id: ID del laboratorio
            
        Returns:
            Dict con resultado de la matrícula
        """
        try:
            student = Student.objects.get(id=student_id)
            laboratory = Laboratory.objects.get(id=laboratory_id)
            
            with transaction.atomic():
                # Verificar que el estudiante está matriculado en el curso
                from repositorio.postgres_repository.models import Enrollment
                course_enrollment = Enrollment.objects.filter(
                    student=student,
                    course_group=laboratory.course_group,
                    status='active'
                ).first()
                
                if not course_enrollment:
                    return {
                        'success': False,
                        'error': 'El estudiante no está matriculado en este curso',
                        'error_code': 'NOT_ENROLLED_IN_COURSE'
                    }
                
                # Verificar disponibilidad del laboratorio
                enrolled_count = LaboratoryEnrollment.objects.filter(
                    laboratory=laboratory,
                    status='active'
                ).count()
                
                if enrolled_count >= laboratory.capacity:
                    return {
                        'success': False,
                        'error': 'El laboratorio está lleno',
                        'error_code': 'LABORATORY_FULL'
                    }
                
                # Verificar si ya está matriculado en otro laboratorio del mismo curso
                existing_enrollment = LaboratoryEnrollment.objects.filter(
                    student=student,
                    laboratory__course_group=laboratory.course_group,
                    status='active'
                ).first()
                
                if existing_enrollment:
                    if existing_enrollment.laboratory == laboratory:
                        return {
                            'success': False,
                            'error': 'Ya está matriculado en este laboratorio',
                            'error_code': 'ALREADY_ENROLLED'
                        }
                    else:
                        # Cambiar de laboratorio - desmatricular del anterior
                        existing_enrollment.status = 'withdrawn'
                        existing_enrollment.save()
                
                # Crear nueva matrícula
                lab_enrollment = LaboratoryEnrollment.objects.create(
                    student=student,
                    laboratory=laboratory,
                    enrollment_date=timezone.now().date(),
                    status='active'
                )
                
                # Actualizar contador de estudiantes matriculados
                laboratory.enrolled_students = LaboratoryEnrollment.objects.filter(
                    laboratory=laboratory,
                    status='active'
                ).count()
                laboratory.save()
                
                return {
                    'success': True,
                    'enrollment_id': str(lab_enrollment.id),
                    'laboratory_code': laboratory.lab_code,
                    'course_name': laboratory.course_group.course.name,
                    'enrollment_date': lab_enrollment.enrollment_date.isoformat(),
                    'schedule_info': laboratory.schedule_info,
                    'lab_room': laboratory.lab_room,
                    'teacher_name': laboratory.teacher.user.get_full_name() if laboratory.teacher else 'Sin asignar',
                    'message': f'Matriculado exitosamente en {laboratory.lab_code}'
                }
            
        except (Student.DoesNotExist, Laboratory.DoesNotExist) as e:
            return {
                'success': False,
                'error': 'Estudiante o laboratorio no encontrado',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error matriculando en laboratorio: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def desmatricular_laboratorio(self, student_id: str, laboratory_id: str) -> Dict:
        """
        Desmatricular estudiante de un laboratorio
        
        Args:
            student_id: ID del estudiante
            laboratory_id: ID del laboratorio
            
        Returns:
            Dict con resultado de la desmatrícula
        """
        try:
            student = Student.objects.get(id=student_id)
            laboratory = Laboratory.objects.get(id=laboratory_id)
            
            with transaction.atomic():
                # Buscar matrícula activa
                lab_enrollment = LaboratoryEnrollment.objects.filter(
                    student=student,
                    laboratory=laboratory,
                    status='active'
                ).first()
                
                if not lab_enrollment:
                    return {
                        'success': False,
                        'error': 'No está matriculado en este laboratorio',
                        'error_code': 'NOT_ENROLLED'
                    }
                
                # Verificar si está dentro del período de cambios
                # TODO: Implementar verificación de fechas límite
                
                # Desmatricular
                lab_enrollment.status = 'withdrawn'
                lab_enrollment.save()
                
                # Actualizar contador
                laboratory.enrolled_students = LaboratoryEnrollment.objects.filter(
                    laboratory=laboratory,
                    status='active'
                ).count()
                laboratory.save()
                
                return {
                    'success': True,
                    'laboratory_code': laboratory.lab_code,
                    'course_name': laboratory.course_group.course.name,
                    'withdrawal_date': timezone.now().date().isoformat(),
                    'message': f'Desmatriculado exitosamente de {laboratory.lab_code}'
                }
            
        except (Student.DoesNotExist, Laboratory.DoesNotExist) as e:
            return {
                'success': False,
                'error': 'Estudiante o laboratorio no encontrado',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error desmatriculando de laboratorio: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def obtener_matriculas_estudiante(self, student_id: str) -> Dict:
        """
        Obtener todas las matrículas de laboratorio de un estudiante
        
        Args:
            student_id: ID del estudiante
            
        Returns:
            Dict con matrículas del estudiante
        """
        try:
            student = Student.objects.get(id=student_id)
            
            # Obtener matrículas activas
            active_enrollments = LaboratoryEnrollment.objects.filter(
                student=student,
                status='active'
            ).select_related('laboratory__course_group__course', 'laboratory__teacher__user')
            
            matriculas_activas = []
            for enrollment in active_enrollments:
                lab = enrollment.laboratory
                
                matriculas_activas.append({
                    'enrollment_id': str(enrollment.id),
                    'laboratory_id': str(lab.id),
                    'laboratory_code': lab.lab_code,
                    'course_name': lab.course_group.course.name,
                    'course_code': lab.course_group.course.code,
                    'group_code': lab.course_group.group_code,
                    'enrollment_date': enrollment.enrollment_date.isoformat(),
                    'schedule_info': lab.schedule_info,
                    'lab_room': lab.lab_room,
                    'teacher_name': lab.teacher.user.get_full_name() if lab.teacher else 'Sin asignar',
                    'capacity': lab.capacity,
                    'enrolled_count': LaboratoryEnrollment.objects.filter(
                        laboratory=lab, status='active'
                    ).count()
                })
            
            return {
                'success': True,
                'student_name': student.user.get_full_name(),
                'student_code': student.student_code,
                'matriculas_activas': matriculas_activas,
                'total_matriculas': len(matriculas_activas),
                'fecha_consulta': timezone.now().isoformat()
            }
            
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Estudiante no encontrado',
                'error_code': 'STUDENT_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo matrículas del estudiante: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }


# Instancia global del servicio
servicio_matricula = ServicioMatricula()