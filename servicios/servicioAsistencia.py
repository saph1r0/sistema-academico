#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de asistencia de estudiantes
Maneja registro de asistencia con PRESENTE/FALTA
"""

import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, date

from repositorio.postgres_repository.models import (
    Student, Teacher, Course, CourseGroup, Attendance, User
)

logger = logging.getLogger(__name__)


class ServicioAsistencia:
    """
    Servicio para manejo de asistencia de estudiantes
    """
    
    ESTADOS_ASISTENCIA = {
        'present': 'Presente',
        'absent': 'Falta',
        'late': 'Tardanza',
        'justified': 'Justificado'
    }
    
    def __init__(self):
        self.logger = logger
    
    def registrar_asistencia_clase(self, teacher_id: str, course_group_id: str, 
                                 fecha: date, asistencias: List[Dict]) -> Dict:
        """
        Registrar asistencia de una clase completa
        
        Args:
            teacher_id: ID del profesor
            course_group_id: ID del grupo de curso
            fecha: Fecha de la clase
            asistencias: Lista con asistencia de cada estudiante
                        [{'student_id': 'xxx', 'status': 'present'/'absent', 'notes': ''}]
            
        Returns:
            Dict con resultado del registro
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Verificar que el profesor puede tomar asistencia en este curso
            if course_group.teacher != teacher:
                return {
                    'success': False,
                    'error': 'El profesor no está asignado a este curso',
                    'error_code': 'TEACHER_NOT_ASSIGNED'
                }
            
            registros_exitosos = 0
            errores = []
            
            with transaction.atomic():
                for asistencia_data in asistencias:
                    try:
                        student_id = asistencia_data.get('student_id')
                        status = asistencia_data.get('status', 'absent')
                        notes = asistencia_data.get('notes', '')
                        
                        if not student_id:
                            errores.append("ID de estudiante requerido")
                            continue
                        
                        student = Student.objects.get(id=student_id)
                        
                        # Verificar que el estudiante está matriculado en el curso
                        from repositorio.postgres_repository.models import Enrollment
                        enrollment = Enrollment.objects.filter(
                            student=student,
                            course_group=course_group,
                            status='active'
                        ).first()
                        
                        if not enrollment:
                            errores.append(f"Estudiante {student.student_code} no matriculado en el curso")
                            continue
                        
                        # Crear o actualizar registro de asistencia
                        attendance, created = Attendance.objects.update_or_create(
                            student=student,
                            course=course_group.course,
                            date=fecha,
                            defaults={
                                'status': status,
                                'notes': notes,
                                'recorded_by': teacher
                            }
                        )
                        
                        registros_exitosos += 1
                        
                    except Student.DoesNotExist:
                        errores.append(f"Estudiante no encontrado: {student_id}")
                    except Exception as e:
                        errores.append(f"Error registrando asistencia: {str(e)}")
            
            return {
                'success': True,
                'registros_exitosos': registros_exitosos,
                'total_errores': len(errores),
                'errores': errores,
                'fecha': fecha.isoformat(),
                'course_name': course_group.course.name,
                'group_code': course_group.group_code
            }
            
        except (Teacher.DoesNotExist, CourseGroup.DoesNotExist) as e:
            return {
                'success': False,
                'error': 'Profesor o curso no encontrado',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error registrando asistencia: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def obtener_estudiantes_curso(self, course_group_id: str, fecha: date = None) -> Dict:
        """
        Obtener lista de estudiantes de un curso con su asistencia
        
        Args:
            course_group_id: ID del grupo de curso
            fecha: Fecha para verificar asistencia (opcional)
            
        Returns:
            Dict con lista de estudiantes y su asistencia
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener estudiantes matriculados
            from repositorio.postgres_repository.models import Enrollment
            enrollments = Enrollment.objects.filter(
                course_group=course_group,
                status='active'
            ).select_related('student__user')
            
            estudiantes = []
            fecha_consulta = fecha or timezone.now().date()
            
            for enrollment in enrollments:
                student = enrollment.student
                
                # Verificar asistencia para la fecha específica
                asistencia_hoy = None
                if fecha:
                    attendance = Attendance.objects.filter(
                        student=student,
                        course=course_group.course,
                        date=fecha
                    ).first()
                    
                    if attendance:
                        asistencia_hoy = {
                            'status': attendance.status,
                            'status_display': self.ESTADOS_ASISTENCIA.get(attendance.status, attendance.status),
                            'notes': attendance.notes,
                            'recorded_at': attendance.created_at.isoformat()
                        }
                
                # Calcular estadísticas de asistencia
                total_clases = Attendance.objects.filter(
                    student=student,
                    course=course_group.course
                ).count()
                
                presentes = Attendance.objects.filter(
                    student=student,
                    course=course_group.course,
                    status='present'
                ).count()
                
                porcentaje_asistencia = (presentes / total_clases * 100) if total_clases > 0 else 0
                
                estudiantes.append({
                    'student_id': str(student.id),
                    'student_code': student.student_code,
                    'student_name': student.user.get_full_name(),
                    'student_email': student.user.institutional_email,
                    'asistencia_hoy': asistencia_hoy,
                    'estadisticas': {
                        'total_clases': total_clases,
                        'presentes': presentes,
                        'ausentes': total_clases - presentes,
                        'porcentaje_asistencia': round(porcentaje_asistencia, 2)
                    }
                })
            
            return {
                'success': True,
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'fecha_consulta': fecha_consulta.isoformat(),
                'total_estudiantes': len(estudiantes),
                'estudiantes': estudiantes
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estudiantes: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def obtener_reporte_asistencia(self, course_group_id: str, 
                                 fecha_inicio: date = None, fecha_fin: date = None) -> Dict:
        """
        Obtener reporte de asistencia de un curso en un período
        
        Args:
            course_group_id: ID del grupo de curso
            fecha_inicio: Fecha de inicio del reporte
            fecha_fin: Fecha de fin del reporte
            
        Returns:
            Dict con reporte de asistencia
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Definir período por defecto (último mes)
            if not fecha_inicio:
                fecha_inicio = timezone.now().date().replace(day=1)
            if not fecha_fin:
                fecha_fin = timezone.now().date()
            
            # Obtener asistencias del período
            attendances = Attendance.objects.filter(
                course=course_group.course,
                date__range=[fecha_inicio, fecha_fin]
            ).select_related('student__user')
            
            # Agrupar por estudiante
            reporte_por_estudiante = {}
            
            for attendance in attendances:
                student_code = attendance.student.student_code
                
                if student_code not in reporte_por_estudiante:
                    reporte_por_estudiante[student_code] = {
                        'student_name': attendance.student.user.get_full_name(),
                        'student_code': student_code,
                        'total_clases': 0,
                        'presentes': 0,
                        'ausentes': 0,
                        'tardanzas': 0,
                        'justificadas': 0,
                        'porcentaje_asistencia': 0,
                        'detalle_por_fecha': {}
                    }
                
                estudiante_data = reporte_por_estudiante[student_code]
                estudiante_data['total_clases'] += 1
                
                if attendance.status == 'present':
                    estudiante_data['presentes'] += 1
                elif attendance.status == 'absent':
                    estudiante_data['ausentes'] += 1
                elif attendance.status == 'late':
                    estudiante_data['tardanzas'] += 1
                elif attendance.status == 'justified':
                    estudiante_data['justificadas'] += 1
                
                # Agregar detalle por fecha
                fecha_str = attendance.date.isoformat()
                estudiante_data['detalle_por_fecha'][fecha_str] = {
                    'status': attendance.status,
                    'status_display': self.ESTADOS_ASISTENCIA.get(attendance.status, attendance.status),
                    'notes': attendance.notes
                }
            
            # Calcular porcentajes
            for student_data in reporte_por_estudiante.values():
                if student_data['total_clases'] > 0:
                    student_data['porcentaje_asistencia'] = round(
                        (student_data['presentes'] / student_data['total_clases']) * 100, 2
                    )
            
            # Estadísticas generales del curso
            total_estudiantes = len(reporte_por_estudiante)
            promedio_asistencia = 0
            
            if total_estudiantes > 0:
                suma_porcentajes = sum(data['porcentaje_asistencia'] for data in reporte_por_estudiante.values())
                promedio_asistencia = round(suma_porcentajes / total_estudiantes, 2)
            
            return {
                'success': True,
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'periodo': {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat()
                },
                'estadisticas_generales': {
                    'total_estudiantes': total_estudiantes,
                    'promedio_asistencia': promedio_asistencia,
                    'total_clases_registradas': attendances.count()
                },
                'reporte_por_estudiante': list(reporte_por_estudiante.values()),
                'fecha_generacion': timezone.now().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error generando reporte de asistencia: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }


# Instancia global del servicio
servicio_asistencia = ServicioAsistencia()