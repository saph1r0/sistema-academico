"""
Servicio para gestión de contenido del curso
Maneja temas del curso, cálculo automático de porcentajes y actualización de temas completados
"""

import uuid
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from repositorio.postgres_repository.models import (
    CourseGroup, 
    CourseTopicContent, 
    Teacher
)


class CourseContentManager:
    """
    Servicio para manejar el contenido de los cursos
    
    Funcionalidades:
    - Subida de temas con cálculo automático de porcentajes
    - Actualización automática de temas completados basado en progreso
    - Gestión de orden de temas
    """
    
    def __init__(self):
        self.model = CourseTopicContent
    
    def upload_course_topics(self, course_group_id: str, topics: List[Dict], teacher_id: str = None) -> Dict:
        """
        Sube temas del curso con cálculo automático de porcentajes
        
        Args:
            course_group_id: ID del grupo de curso
            topics: Lista de diccionarios con información de temas
                   [{'title': str, 'description': str}, ...]
            teacher_id: ID del profesor (opcional, para validación)
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar que el curso existe
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Validar que el profesor tiene permisos (si se proporciona)
            if teacher_id:
                teacher = Teacher.objects.get(id=teacher_id)
                if course_group.teacher != teacher:
                    raise ValidationError("El profesor no está asignado a este curso")
            
            # Validar que hay temas para procesar
            if not topics or len(topics) == 0:
                raise ValidationError("Debe proporcionar al menos un tema")
            
            if len(topics) > 20:
                raise ValidationError("No se pueden agregar más de 20 temas por curso")
            
            # Calcular porcentajes automáticamente
            percentages = self.calculate_topic_percentages(len(topics))
            
            with transaction.atomic():
                # Eliminar temas existentes para este curso
                self.model.objects.filter(course_group=course_group).delete()
                
                # Crear nuevos temas
                created_topics = []
                for i, topic_data in enumerate(topics):
                    topic = self.model.objects.create(
                        course_group=course_group,
                        topic_title=topic_data.get('title', f'Tema {i+1}'),
                        topic_description=topic_data.get('description', ''),
                        topic_order=i + 1,
                        percentage_weight=percentages[i],
                        is_completed=False
                    )
                    created_topics.append(topic)
                
                # Actualizar estado de completado basado en progreso actual
                self.update_topic_completion_by_progress(course_group_id)
            
            return {
                'success': True,
                'message': f'Se crearon {len(created_topics)} temas exitosamente',
                'topics_created': len(created_topics),
                'course_group': str(course_group),
                'topics': [
                    {
                        'id': str(topic.id),
                        'title': topic.topic_title,
                        'order': topic.topic_order,
                        'percentage': topic.percentage_weight,
                        'completed': topic.is_completed
                    }
                    for topic in created_topics
                ]
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado',
                'error_code': 'TEACHER_NOT_FOUND'
            }
        except ValidationError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def calculate_topic_percentages(self, num_topics: int) -> List[float]:
        """
        Calcula porcentajes automáticamente para los temas
        
        Args:
            num_topics: Número de temas
        
        Returns:
            Lista de porcentajes que suman 100%
        """
        if num_topics <= 0:
            return []
        
        # Calcular porcentaje base
        base_percentage = 100.0 / num_topics
        
        # Crear lista con porcentajes iguales
        percentages = [base_percentage] * num_topics
        
        # Ajustar para que sume exactamente 100%
        total = sum(percentages)
        if total != 100.0:
            # Ajustar el último elemento para que sume exactamente 100
            difference = 100.0 - total
            percentages[-1] += difference
        
        # Redondear a 2 decimales
        percentages = [round(p, 2) for p in percentages]
        
        return percentages
    
    def get_course_topics(self, course_group_id: str) -> Dict:
        """
        Obtiene todos los temas de un curso
        
        Args:
            course_group_id: ID del grupo de curso
        
        Returns:
            Dict con los temas del curso
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            topics = self.model.objects.filter(
                course_group=course_group
            ).order_by('topic_order')
            
            return {
                'success': True,
                'course_group': str(course_group),
                'total_topics': topics.count(),
                'completed_topics': topics.filter(is_completed=True).count(),
                'topics': [
                    {
                        'id': str(topic.id),
                        'title': topic.topic_title,
                        'description': topic.topic_description,
                        'order': topic.topic_order,
                        'percentage': topic.percentage_weight,
                        'completed': topic.is_completed,
                        'completion_date': topic.completion_date.isoformat() if topic.completion_date else None,
                        'created_at': topic.created_at.isoformat()
                    }
                    for topic in topics
                ]
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def get_completed_topics(self, course_group_id: str) -> List[Dict]:
        """
        Obtiene solo los temas completados de un curso
        
        Args:
            course_group_id: ID del grupo de curso
        
        Returns:
            Lista de temas completados
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            completed_topics = self.model.objects.filter(
                course_group=course_group,
                is_completed=True
            ).order_by('topic_order')
            
            return [
                {
                    'id': str(topic.id),
                    'title': topic.topic_title,
                    'description': topic.topic_description,
                    'order': topic.topic_order,
                    'percentage': topic.percentage_weight,
                    'completion_date': topic.completion_date.isoformat() if topic.completion_date else None
                }
                for topic in completed_topics
            ]
            
        except CourseGroup.DoesNotExist:
            return []
        except Exception:
            return []
    
    def update_topic_completion_by_progress(self, course_group_id: str) -> Dict:
        """
        Actualiza automáticamente qué temas están completados basado en el progreso del curso
        
        Args:
            course_group_id: ID del grupo de curso
        
        Returns:
            Dict con resultado de la actualización
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener progreso actual del curso
            current_progress = course_group.course_progress_percentage
            
            # Obtener todos los temas ordenados
            topics = self.model.objects.filter(
                course_group=course_group
            ).order_by('topic_order')
            
            if not topics.exists():
                return {
                    'success': True,
                    'message': 'No hay temas para actualizar',
                    'topics_updated': 0
                }
            
            # Calcular cuántos temas deberían estar completados
            total_topics = topics.count()
            topics_to_complete = int((current_progress / 100.0) * total_topics)
            
            updated_count = 0
            
            with transaction.atomic():
                # Marcar temas como completados según el progreso
                for i, topic in enumerate(topics):
                    should_be_completed = i < topics_to_complete
                    
                    if should_be_completed and not topic.is_completed:
                        topic.mark_as_completed()
                        updated_count += 1
                    elif not should_be_completed and topic.is_completed:
                        topic.mark_as_incomplete()
                        updated_count += 1
            
            return {
                'success': True,
                'message': f'Se actualizaron {updated_count} temas',
                'topics_updated': updated_count,
                'current_progress': current_progress,
                'total_topics': total_topics,
                'completed_topics': topics_to_complete,
                'course_group': str(course_group)
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def add_single_topic(self, course_group_id: str, topic_data: Dict, teacher_id: str = None) -> Dict:
        """
        Agrega un solo tema al curso y recalcula porcentajes
        
        Args:
            course_group_id: ID del grupo de curso
            topic_data: Datos del tema {'title': str, 'description': str}
            teacher_id: ID del profesor (opcional)
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Validar permisos del profesor
            if teacher_id:
                teacher = Teacher.objects.get(id=teacher_id)
                if course_group.teacher != teacher:
                    raise ValidationError("El profesor no está asignado a este curso")
            
            # Obtener temas existentes
            existing_topics = list(self.model.objects.filter(
                course_group=course_group
            ).order_by('topic_order'))
            
            # Validar límite máximo
            if len(existing_topics) >= 20:
                raise ValidationError("No se pueden agregar más de 20 temas por curso")
            
            with transaction.atomic():
                # Crear nuevo tema
                new_order = len(existing_topics) + 1
                new_topic = self.model.objects.create(
                    course_group=course_group,
                    topic_title=topic_data.get('title', f'Tema {new_order}'),
                    topic_description=topic_data.get('description', ''),
                    topic_order=new_order,
                    percentage_weight=0,  # Se calculará después
                    is_completed=False
                )
                
                # Recalcular porcentajes para todos los temas
                all_topics = list(self.model.objects.filter(
                    course_group=course_group
                ).order_by('topic_order'))
                
                new_percentages = self.calculate_topic_percentages(len(all_topics))
                
                # Actualizar porcentajes
                for topic, percentage in zip(all_topics, new_percentages):
                    topic.percentage_weight = percentage
                    topic.save()
                
                # Actualizar completado basado en progreso
                self.update_topic_completion_by_progress(course_group_id)
            
            return {
                'success': True,
                'message': 'Tema agregado exitosamente',
                'topic_created': {
                    'id': str(new_topic.id),
                    'title': new_topic.topic_title,
                    'order': new_topic.topic_order,
                    'percentage': new_topic.percentage_weight
                },
                'total_topics': len(all_topics)
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado',
                'error_code': 'TEACHER_NOT_FOUND'
            }
        except ValidationError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def remove_topic(self, course_group_id: str, topic_id: str, teacher_id: str = None) -> Dict:
        """
        Elimina un tema del curso y recalcula porcentajes
        
        Args:
            course_group_id: ID del grupo de curso
            topic_id: ID del tema a eliminar
            teacher_id: ID del profesor (opcional)
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            topic_to_remove = self.model.objects.get(id=topic_id, course_group=course_group)
            
            # Validar permisos del profesor
            if teacher_id:
                teacher = Teacher.objects.get(id=teacher_id)
                if course_group.teacher != teacher:
                    raise ValidationError("El profesor no está asignado a este curso")
            
            # Validar mínimo de temas
            total_topics = self.model.objects.filter(course_group=course_group).count()
            if total_topics <= 5:
                raise ValidationError("Debe mantener al menos 5 temas por curso")
            
            with transaction.atomic():
                removed_order = topic_to_remove.topic_order
                topic_title = topic_to_remove.topic_title
                
                # Eliminar el tema
                topic_to_remove.delete()
                
                # Reordenar temas restantes
                remaining_topics = self.model.objects.filter(
                    course_group=course_group,
                    topic_order__gt=removed_order
                ).order_by('topic_order')
                
                for topic in remaining_topics:
                    topic.topic_order -= 1
                    topic.save()
                
                # Recalcular porcentajes
                all_topics = list(self.model.objects.filter(
                    course_group=course_group
                ).order_by('topic_order'))
                
                new_percentages = self.calculate_topic_percentages(len(all_topics))
                
                for topic, percentage in zip(all_topics, new_percentages):
                    topic.percentage_weight = percentage
                    topic.save()
                
                # Actualizar completado basado en progreso
                self.update_topic_completion_by_progress(course_group_id)
            
            return {
                'success': True,
                'message': f'Tema "{topic_title}" eliminado exitosamente',
                'topic_removed': topic_title,
                'remaining_topics': len(all_topics)
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except self.model.DoesNotExist:
            return {
                'success': False,
                'error': 'Tema no encontrado',
                'error_code': 'TOPIC_NOT_FOUND'
            }
        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado',
                'error_code': 'TEACHER_NOT_FOUND'
            }
        except ValidationError as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'VALIDATION_ERROR'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def get_course_progress_summary(self, course_group_id: str) -> Dict:
        """
        Obtiene un resumen del progreso del curso
        
        Args:
            course_group_id: ID del grupo de curso
        
        Returns:
            Dict con resumen del progreso
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            topics = self.model.objects.filter(course_group=course_group)
            
            total_topics = topics.count()
            completed_topics = topics.filter(is_completed=True).count()
            
            return {
                'success': True,
                'course_group': str(course_group),
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'teacher': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar',
                'progress_percentage': course_group.course_progress_percentage,
                'total_topics': total_topics,
                'completed_topics': completed_topics,
                'pending_topics': total_topics - completed_topics,
                'completion_rate': (completed_topics / total_topics * 100) if total_topics > 0 else 0,
                'classes_attended': course_group.classes_attended_by_teacher,
                'total_planned_classes': course_group.total_planned_classes
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }


# Instancia global del servicio para uso en otras partes del sistema
course_content_manager = CourseContentManager()