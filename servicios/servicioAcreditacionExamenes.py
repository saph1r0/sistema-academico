#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de acreditación de exámenes
Implementa lógica de negocio siguiendo DDD, sin fases.
"""

import logging
from django.db import transaction
from django.core.exceptions import PermissionDenied

from repositorio.postgres_repository.models import (
    Teacher,
    CourseGroup,
    ExamAccreditation,
    PhaseGrade
)

logger = logging.getLogger(__name__)


class ExamAccreditationService:

    def __init__(self):
        self.logger = logger

    def upload_exam_accreditation(
        self,
        teacher_id: str,
        course_group_id: str,
        exam_number: int,
        best_exam_file,
        worst_exam_file,
        ip_address: str = None
    ) -> dict:
        """
        Subir acreditación de examen para un parcial.
        El profesor sube:
            - Examen de mejor nota
            - Examen de peor nota

        Sin fases: solo exam_number = 1, 2, 3
        """

        try:
            # Validar profesor
            teacher = Teacher.objects.select_related('user').get(id=teacher_id)

            # Validar curso
            course_group = CourseGroup.objects.select_related(
                'course', 'academic_period', 'teacher'
            ).get(id=course_group_id)

            # Validar que el profesor es el asignado al curso
            if str(course_group.teacher_id) != str(teacher_id):
                raise PermissionDenied("No tiene permiso para subir exámenes de este curso.")

            # Validar parcial
            if exam_number not in [1, 2, 3]:
                return {
                    'success': False,
                    'error': 'Número de parcial inválido (solo 1, 2 o 3).',
                    'error_code': 'INVALID_EXAM_NUMBER'
                }

            # Verificar que existan notas para calcular estadísticas
            if not PhaseGrade.objects.filter(course_group=course_group).exists():
                return {
                    'success': False,
                    'error': 'No hay notas registradas. Debe subir las notas antes de acreditar el examen.',
                    'error_code': 'NO_GRADES_FOUND'
                }

            with transaction.atomic():
                # Verificar si ya existe acreditación
                accreditation = ExamAccreditation.objects.filter(
                    course_group=course_group,
                    exam_number=exam_number
                ).first()

                action = "created"

                if accreditation:
                    # Actualizar archivos
                    if best_exam_file:
                        accreditation.best_exam_file = best_exam_file
                    if worst_exam_file:
                        accreditation.worst_exam_file = worst_exam_file

                    accreditation.uploaded_by = teacher
                    accreditation.save()

                    action = "updated"

                else:
                    # Crear nueva acreditación
                    accreditation = ExamAccreditation.objects.create(
                        course_group=course_group,
                        uploaded_by=teacher,
                        exam_number=exam_number,
                        best_exam_file=best_exam_file,
                        worst_exam_file=worst_exam_file,
                    )

            return {
                'success': True,
                'message': 'Acreditación registrada correctamente',
                'accreditation_id': str(accreditation.id),
                'action': action,
                'statistics': {
                    'max': accreditation.max_grade,
                    'min': accreditation.min_grade,
                    'avg': accreditation.average_grade,
                    'total_students': accreditation.total_students
                },
                'exam_info': {
                    'exam_number': exam_number,
                    'best_file': accreditation.best_exam_file.url if accreditation.best_exam_file else None,
                    'worst_file': accreditation.worst_exam_file.url if accreditation.worst_exam_file else None,
                },
                'uploaded_at': accreditation.uploaded_at.isoformat()
            }

        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado.',
                'error_code': 'TEACHER_NOT_FOUND'
            }

        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Curso no encontrado.',
                'error_code': 'COURSE_NOT_FOUND'
            }

        except PermissionDenied as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'PERMISSION_DENIED'
            }

        except Exception as e:
            self.logger.error(f"Error subiendo acreditación: {str(e)}")
            return {
                'success': False,
                'error': f"Error interno: {str(e)}",
                'error_code': 'INTERNAL_ERROR'
            }

    # ============================================================
    #       LISTAR ACREDITACIONES DEL PROFESOR
    # ============================================================

    def get_teacher_accreditations(self, teacher_id: str):
        """Lista todas las acreditaciones subidas por un profesor."""

        try:
            teacher = Teacher.objects.get(id=teacher_id)

            accreditations = ExamAccreditation.objects.filter(
                uploaded_by=teacher
            ).select_related(
                'course_group__course',
                'course_group__academic_period'
            ).order_by('-uploaded_at')

            data = []
            for acc in accreditations:
                data.append({
                    'id': str(acc.id),
                    'course': {
                        'code': acc.course_group.course.code,
                        'name': acc.course_group.course.name,
                        'group': acc.course_group.group_code
                    },
                    'exam_number': acc.exam_number,
                    'statistics': acc.get_statistics_summary(),
                    'files': {
                        'best': acc.best_exam_file.url if acc.best_exam_file else None,
                        'worst': acc.worst_exam_file.url if acc.worst_exam_file else None
                    },
                    'uploaded_at': acc.uploaded_at.isoformat()
                })

            return {
                'success': True,
                'total': len(data),
                'accreditations': data
            }

        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado.'
            }

        except Exception as e:
            self.logger.error(str(e))
            return {
                'success': False,
                'error': f"Error interno: {str(e)}"
            }


# Instancia global
servicio_acreditacion_examenes = ExamAccreditationService()
