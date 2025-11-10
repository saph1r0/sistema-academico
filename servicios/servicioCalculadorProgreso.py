#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para cálculo automático de progreso del curso
Implementa la fórmula: (clases asistidas / total programadas) * 100
Actualiza automáticamente el estado de temas completados
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from repositorio.postgres_repository.models import (
    CourseGroup, 
    Teacher, 
    TeacherAttendance,
    CourseTopicContent
)


logger = logging.getLogger(__name__)


class ProgressCalculator:
    """
    Servicio para cálculo automático de progreso del curso
    
    Funcionalidades:
    - Calcular progreso basado en asistencia docente
    - Actualizar automáticamente estado de temas completados
    - Obtener estadísticas de progreso esperado vs real
    """
    
    def __init__(self):
        self.logger = logger
    
    def calculate_course_progress(self, course_group_id: str) -> Dict:
        """
        Calcula el progreso del curso basado en la asistencia del docente
        
        Fórmula: (clases asistidas / total programadas) * 100
        
        Args:
            course_group_id: ID del grupo de curso
            
        Returns:
            Dict con información del progreso calculado
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            if not course_group.teacher:
                return {
                    'success': False,
                    'error': 'No hay profesor asignado a este curso',
                    'error_code': 'NO_TEACHER_ASSIGNED'
                }
            
            # Contar clases asistidas por el docente (sesiones válidas)
            classes_attended = self._count_valid_teacher_sessions(course_group.teacher)
            
            # Obtener total de clases programadas
            total_planned = course_group.total_planned_classes
            
            if total_planned <= 0:
                return {
                    'success': False,
                    'error': 'Total de clases programadas debe ser mayor a 0',
                    'error_code': 'INVALID_TOTAL_CLASSES'
                }
            
            # Calcular progreso usando la fórmula especificada
            progress_percentage = min((classes_attended / total_planned) * 100, 100.0)
            
            # Actualizar el modelo con el progreso calculado
            with transaction.atomic():
                course_group.classes_attended_by_teacher = classes_attended
                course_group.course_progress_percentage = round(progress_percentage, 2)
                course_group.save()
                
                # Actualizar automáticamente el estado de temas completados
                topics_update_result = self.update_topic_completion_status(course_group_id, progress_percentage)
            
            self.logger.info(
                f"Progreso calculado para {course_group.course.name} - "
                f"Grupo {course_group.group_code}: {progress_percentage:.2f}% "
                f"({classes_attended}/{total_planned} clases)"
            )
            
            return {
                'success': True,
                'course_group_id': course_group_id,
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'teacher_name': course_group.teacher.user.get_full_name(),
                'classes_attended': classes_attended,
                'total_planned_classes': total_planned,
                'progress_percentage': round(progress_percentage, 2),
                'previous_progress': course_group.course_progress_percentage,
                'topics_updated': topics_update_result.get('topics_updated', 0),
                'calculation_timestamp': timezone.now().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error calculando progreso del curso: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def update_topic_completion_status(self, course_group_id: str, progress_percentage: float) -> Dict:
        """
        Actualiza automáticamente el estado de temas completados basado en el progreso
        
        Args:
            course_group_id: ID del grupo de curso
            progress_percentage: Porcentaje de progreso actual
            
        Returns:
            Dict con resultado de la actualización
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener todos los temas ordenados
            topics = CourseTopicContent.objects.filter(
                course_group=course_group
            ).order_by('topic_order')
            
            if not topics.exists():
                return {
                    'success': True,
                    'message': 'No hay temas para actualizar',
                    'topics_updated': 0,
                    'total_topics': 0,
                    'completed_topics': 0
                }
            
            total_topics = topics.count()
            
            # Calcular cuántos temas deberían estar completados
            # Fórmula: floor(progreso * total_temas / 100)
            topics_to_complete = int((progress_percentage / 100.0) * total_topics)
            
            updated_count = 0
            
            with transaction.atomic():
                # Marcar temas como completados según el progreso
                for i, topic in enumerate(topics):
                    should_be_completed = i < topics_to_complete
                    
                    if should_be_completed and not topic.is_completed:
                        topic.mark_as_completed()
                        updated_count += 1
                        self.logger.debug(f"Tema completado: {topic.topic_title}")
                    elif not should_be_completed and topic.is_completed:
                        topic.mark_as_incomplete()
                        updated_count += 1
                        self.logger.debug(f"Tema marcado como incompleto: {topic.topic_title}")
            
            self.logger.info(
                f"Actualización de temas para {course_group.course.name}: "
                f"{topics_to_complete}/{total_topics} temas completados "
                f"({updated_count} cambios realizados)"
            )
            
            return {
                'success': True,
                'message': f'Se actualizaron {updated_count} temas',
                'topics_updated': updated_count,
                'total_topics': total_topics,
                'completed_topics': topics_to_complete,
                'progress_percentage': progress_percentage,
                'course_group': str(course_group)
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error actualizando estado de temas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def get_expected_vs_actual_progress(self, course_group_id: str) -> Dict:
        """
        Compara el progreso esperado vs el progreso real del curso
        
        Args:
            course_group_id: ID del grupo de curso
            
        Returns:
            Dict con comparación de progreso esperado vs real
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Calcular progreso esperado basado en semanas transcurridas
            expected_progress = self._calculate_expected_progress()
            
            # Obtener progreso real actual
            actual_progress = course_group.course_progress_percentage
            
            # Calcular diferencia
            progress_difference = actual_progress - expected_progress
            
            # Determinar estado del curso
            if progress_difference >= 5:
                status = 'adelantado'
                status_message = 'El curso va adelantado respecto al cronograma'
            elif progress_difference <= -10:
                status = 'atrasado'
                status_message = 'El curso va atrasado respecto al cronograma'
            else:
                status = 'normal'
                status_message = 'El curso va según el cronograma esperado'
            
            return {
                'success': True,
                'course_group_id': course_group_id,
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'expected_progress': round(expected_progress, 2),
                'actual_progress': round(actual_progress, 2),
                'progress_difference': round(progress_difference, 2),
                'status': status,
                'status_message': status_message,
                'classes_attended': course_group.classes_attended_by_teacher,
                'total_planned_classes': course_group.total_planned_classes,
                'calculation_date': timezone.now().date().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error comparando progreso esperado vs real: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def calculate_all_courses_progress(self, teacher_id: str = None) -> List[Dict]:
        """
        Calcula el progreso para todos los cursos o los cursos de un profesor específico
        
        Args:
            teacher_id: ID del profesor (opcional, si no se proporciona calcula para todos)
            
        Returns:
            Lista con resultados del cálculo para cada curso
        """
        try:
            # Filtrar cursos según el profesor
            if teacher_id:
                teacher = Teacher.objects.get(id=teacher_id)
                course_groups = CourseGroup.objects.filter(teacher=teacher)
            else:
                course_groups = CourseGroup.objects.filter(teacher__isnull=False)
            
            results = []
            
            for course_group in course_groups:
                result = self.calculate_course_progress(str(course_group.id))
                results.append(result)
            
            # Estadísticas generales
            successful_calculations = sum(1 for r in results if r.get('success', False))
            total_courses = len(results)
            
            self.logger.info(
                f"Cálculo masivo de progreso completado: "
                f"{successful_calculations}/{total_courses} cursos procesados exitosamente"
            )
            
            return results
            
        except Teacher.DoesNotExist:
            self.logger.error(f"Profesor con ID {teacher_id} no encontrado")
            return []
        except Exception as e:
            self.logger.error(f"Error en cálculo masivo de progreso: {str(e)}")
            return []
    
    def _count_valid_teacher_sessions(self, teacher: Teacher) -> int:
        """
        Cuenta las sesiones válidas del docente (más de 30 minutos)
        
        Args:
            teacher: Instancia del docente
            
        Returns:
            int: Número de sesiones válidas
        """
        try:
            # Intentar con la estructura nueva primero
            try:
                sessions = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    logout_time__isnull=False
                )
                
                # Contar solo sesiones válidas (más de 30 minutos)
                valid_sessions = 0
                for session in sessions:
                    if hasattr(session, 'is_valid_session') and session.is_valid_session:
                        valid_sessions += 1
                
                return valid_sessions
                
            except Exception:
                # Si falla, intentar con la estructura antigua
                from django.db import connection
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM teacher_attendance 
                        WHERE teacher_id = %s 
                        AND end_time IS NOT NULL
                        AND (
                            EXTRACT(EPOCH FROM (end_time - start_time)) >= 1800
                            OR end_time != start_time
                        )
                    """, [str(teacher.id)])
                    
                    result = cursor.fetchone()
                    return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Error contando sesiones válidas: {str(e)}")
            return 0
    
    def _calculate_expected_progress(self) -> float:
        """
        Calcula el progreso esperado basado en la semana actual del semestre
        
        Returns:
            float: Porcentaje de progreso esperado
        """
        try:
            # Por simplicidad, asumimos que estamos en la semana 8 de 17
            # En una implementación real, esto se calcularía basado en:
            # - Fecha de inicio del período académico
            # - Fecha actual
            # - Duración total del semestre
            
            current_week = 8  # Esto debería calcularse dinámicamente
            total_weeks = 17  # Duración estándar del semestre
            
            expected_progress = min((current_week / total_weeks) * 100, 100.0)
            
            return expected_progress
            
        except Exception as e:
            self.logger.error(f"Error calculando progreso esperado: {str(e)}")
            return 50.0  # Valor por defecto
    
    def get_progress_statistics(self, course_group_id: str) -> Dict:
        """
        Obtiene estadísticas detalladas del progreso del curso
        
        Args:
            course_group_id: ID del grupo de curso
            
        Returns:
            Dict con estadísticas detalladas
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener información de temas
            topics = CourseTopicContent.objects.filter(course_group=course_group)
            total_topics = topics.count()
            completed_topics = topics.filter(is_completed=True).count()
            
            # Obtener información de asistencia
            if course_group.teacher:
                valid_sessions = self._count_valid_teacher_sessions(course_group.teacher)
                
                # Obtener última sesión (intentar con ambas estructuras)
                try:
                    last_session = TeacherAttendance.objects.filter(
                        teacher=course_group.teacher
                    ).order_by('-login_time').first()
                except Exception:
                    # Si falla, intentar con estructura antigua
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT attendance_date, start_time 
                                FROM teacher_attendance 
                                WHERE teacher_id = %s 
                                ORDER BY attendance_date DESC, start_time DESC 
                                LIMIT 1
                            """, [str(course_group.teacher.id)])
                            
                            result = cursor.fetchone()
                            last_session = None
                            if result:
                                # Crear un objeto mock con la información necesaria
                                class MockSession:
                                    def __init__(self, date, time):
                                        from datetime import datetime
                                        self.login_time = datetime.combine(date, time)
                                
                                last_session = MockSession(result[0], result[1])
                    except Exception:
                        last_session = None
            else:
                valid_sessions = 0
                last_session = None
            
            # Calcular métricas
            attendance_rate = (valid_sessions / course_group.total_planned_classes * 100) if course_group.total_planned_classes > 0 else 0
            topic_completion_rate = (completed_topics / total_topics * 100) if total_topics > 0 else 0
            
            return {
                'success': True,
                'course_group_id': course_group_id,
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'teacher_name': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar',
                'progress_percentage': course_group.course_progress_percentage,
                'attendance_statistics': {
                    'classes_attended': valid_sessions,
                    'total_planned_classes': course_group.total_planned_classes,
                    'attendance_rate': round(attendance_rate, 2),
                    'last_session': last_session.login_time.isoformat() if last_session else None
                },
                'topic_statistics': {
                    'total_topics': total_topics,
                    'completed_topics': completed_topics,
                    'pending_topics': total_topics - completed_topics,
                    'completion_rate': round(topic_completion_rate, 2)
                },
                'expected_vs_actual': self.get_expected_vs_actual_progress(course_group_id),
                'last_updated': timezone.now().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de progreso: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def recalculate_progress_for_teacher_attendance(self, teacher_id: str, attendance_date: timezone.datetime) -> List[Dict]:
        """
        Recalcula el progreso de todos los cursos de un docente cuando registra asistencia
        
        Args:
            teacher_id: ID del docente
            attendance_date: Fecha/hora de la asistencia registrada
            
        Returns:
            Lista con resultados del recálculo para cada curso del docente
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Obtener todos los cursos del docente
            course_groups = CourseGroup.objects.filter(teacher=teacher)
            
            results = []
            
            for course_group in course_groups:
                result = self.calculate_course_progress(str(course_group.id))
                result['triggered_by_attendance'] = attendance_date.isoformat()
                results.append(result)
            
            self.logger.info(
                f"Progreso recalculado para {len(course_groups)} cursos del docente "
                f"{teacher.user.get_full_name()} por asistencia del {attendance_date.date()}"
            )
            
            return results
            
        except Teacher.DoesNotExist:
            self.logger.error(f"Docente con ID {teacher_id} no encontrado")
            return []
        except Exception as e:
            self.logger.error(f"Error recalculando progreso por asistencia: {str(e)}")
            return []


# Instancia global del servicio para uso en otras partes del sistema
progress_calculator = ProgressCalculator()