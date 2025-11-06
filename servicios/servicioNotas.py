#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de notas por fases
Maneja notas de primera, segunda y tercera fase
Incluye estadísticas y gráficos
"""

import logging
from typing import Dict, List, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count

from repositorio.postgres_repository.models import (
    Student, Teacher, Course, CourseGroup, Grade, User
)

logger = logging.getLogger(__name__)


class ServicioNotas:
    """
    Servicio para manejo de notas por fases
    """
    
    FASES = {
        'primera': 'Primera Fase',
        'segunda': 'Segunda Fase', 
        'tercera': 'Tercera Fase'
    }
    
    def __init__(self):
        self.logger = logger
    
    def obtener_notas_estudiante(self, student_id: str, course_id: str = None) -> Dict:
        """
        Obtener todas las notas de un estudiante organizadas por fases
        
        Args:
            student_id: ID del estudiante
            course_id: ID del curso (opcional, si no se proporciona obtiene todos)
            
        Returns:
            Dict con notas organizadas por fases
        """
        try:
            student = Student.objects.get(id=student_id)
            
            # Filtrar por curso si se proporciona
            grades_query = Grade.objects.filter(student=student)
            if course_id:
                grades_query = grades_query.filter(course_id=course_id)
            
            grades = grades_query.select_related('course').order_by('course__name', 'exam_type')
            
            # Organizar notas por curso y fase
            notas_por_curso = {}
            
            for grade in grades:
                course_name = grade.course.name
                
                if course_name not in notas_por_curso:
                    notas_por_curso[course_name] = {
                        'course_id': str(grade.course.id),
                        'course_name': course_name,
                        'primera': [],
                        'segunda': [],
                        'tercera': [],
                        'promedio_final': None
                    }
                
                # Clasificar por fase según el tipo de examen
                if grade.exam_type in ['parcial_1', 'tarea']:
                    fase = 'primera'
                elif grade.exam_type in ['parcial_2']:
                    fase = 'segunda'
                elif grade.exam_type in ['parcial_3', 'final']:
                    fase = 'tercera'
                else:
                    continue
                
                notas_por_curso[course_name][fase].append({
                    'id': str(grade.id),
                    'exam_type': grade.exam_type,
                    'grade_component': grade.grade_component,
                    'grade': float(grade.grade),
                    'created_at': grade.created_at.isoformat()
                })
            
            # Calcular promedios por fase y final
            for course_name, course_data in notas_por_curso.items():
                # Calcular promedio de cada fase
                for fase in ['primera', 'segunda', 'tercera']:
                    if course_data[fase]:
                        promedio_fase = sum(nota['grade'] for nota in course_data[fase]) / len(course_data[fase])
                        course_data[f'promedio_{fase}'] = round(promedio_fase, 2)
                    else:
                        course_data[f'promedio_{fase}'] = None
                
                # Calcular promedio final (si tiene al menos primera fase)
                if course_data['promedio_primera'] is not None:
                    promedios_disponibles = [
                        p for p in [
                            course_data['promedio_primera'],
                            course_data['promedio_segunda'],
                            course_data['promedio_tercera']
                        ] if p is not None
                    ]
                    
                    if promedios_disponibles:
                        course_data['promedio_final'] = round(sum(promedios_disponibles) / len(promedios_disponibles), 2)
            
            return {
                'success': True,
                'student_name': student.user.get_full_name(),
                'student_code': student.student_code,
                'notas_por_curso': notas_por_curso,
                'total_cursos': len(notas_por_curso),
                'fecha_consulta': timezone.now().isoformat()
            }
            
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Estudiante no encontrado',
                'error_code': 'STUDENT_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo notas del estudiante: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def registrar_notas_excel(self, teacher_id: str, course_id: str, excel_data: List[Dict], fase: str) -> Dict:
        """
        Registrar notas desde Excel para una fase específica
        
        Args:
            teacher_id: ID del profesor
            course_id: ID del curso
            excel_data: Lista de diccionarios con datos del Excel
            fase: Fase de las notas ('primera', 'segunda', 'tercera')
            
        Returns:
            Dict con resultado del registro
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            course = Course.objects.get(id=course_id)
            
            # Verificar que el profesor puede enseñar este curso
            course_group = CourseGroup.objects.filter(
                teacher=teacher,
                course=course
            ).first()
            
            if not course_group:
                return {
                    'success': False,
                    'error': 'El profesor no está asignado a este curso',
                    'error_code': 'TEACHER_NOT_ASSIGNED'
                }
            
            # Verificar que la fecha esté habilitada (implementar después)
            # if not self._fecha_habilitada_para_notas():
            #     return {'success': False, 'error': 'Fecha no habilitada para subir notas'}
            
            registros_exitosos = 0
            errores = []
            
            with transaction.atomic():
                for row_data in excel_data:
                    try:
                        # Obtener estudiante por código
                        student_code = str(row_data.get('codigo_estudiante', '')).strip()
                        parcial_nota = row_data.get('nota_parcial')
                        continua_nota = row_data.get('nota_continua')
                        
                        if not student_code:
                            errores.append(f"Código de estudiante vacío en fila")
                            continue
                        
                        student = Student.objects.filter(student_code=student_code).first()
                        if not student:
                            errores.append(f"Estudiante no encontrado: {student_code}")
                            continue
                        
                        # Determinar tipos de examen según la fase
                        if fase == 'primera':
                            exam_types = [('parcial_1', parcial_nota), ('tarea', continua_nota)]
                        elif fase == 'segunda':
                            exam_types = [('parcial_2', parcial_nota), ('tarea', continua_nota)]
                        elif fase == 'tercera':
                            exam_types = [('parcial_3', parcial_nota), ('final', continua_nota)]
                        else:
                            errores.append(f"Fase inválida: {fase}")
                            continue
                        
                        # Registrar las notas
                        for exam_type, nota_valor in exam_types:
                            if nota_valor is not None and str(nota_valor).strip():
                                try:
                                    nota_decimal = Decimal(str(nota_valor))
                                    
                                    # Crear o actualizar la nota
                                    grade, created = Grade.objects.update_or_create(
                                        student=student,
                                        course=course,
                                        exam_type=exam_type,
                                        grade_component=f'{fase.title()} - {exam_type}',
                                        defaults={'grade': nota_decimal}
                                    )
                                    
                                    if created:
                                        registros_exitosos += 1
                                
                                except (ValueError, TypeError) as e:
                                    errores.append(f"Nota inválida para {student_code} - {exam_type}: {nota_valor}")
                        
                    except Exception as e:
                        errores.append(f"Error procesando estudiante {student_code}: {str(e)}")
            
            return {
                'success': True,
                'registros_exitosos': registros_exitosos,
                'total_errores': len(errores),
                'errores': errores[:10],  # Mostrar solo los primeros 10 errores
                'fase': fase,
                'course_name': course.name,
                'teacher_name': teacher.user.get_full_name()
            }
            
        except (Teacher.DoesNotExist, Course.DoesNotExist) as e:
            return {
                'success': False,
                'error': 'Profesor o curso no encontrado',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error registrando notas desde Excel: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def obtener_estadisticas_curso(self, course_id: str, fase: str = None) -> Dict:
        """
        Obtener estadísticas de notas de un curso
        
        Args:
            course_id: ID del curso
            fase: Fase específica (opcional)
            
        Returns:
            Dict con estadísticas del curso
        """
        try:
            course = Course.objects.get(id=course_id)
            
            # Filtrar notas por fase si se especifica
            grades_query = Grade.objects.filter(course=course)
            
            if fase:
                if fase == 'primera':
                    grades_query = grades_query.filter(exam_type__in=['parcial_1', 'tarea'])
                elif fase == 'segunda':
                    grades_query = grades_query.filter(exam_type__in=['parcial_2'])
                elif fase == 'tercera':
                    grades_query = grades_query.filter(exam_type__in=['parcial_3', 'final'])
            
            # Calcular estadísticas
            stats = grades_query.aggregate(
                promedio=Avg('grade'),
                nota_maxima=Max('grade'),
                nota_minima=Min('grade'),
                total_notas=Count('id')
            )
            
            # Obtener distribución de notas
            notas_por_rango = {
                '0-5': grades_query.filter(grade__lt=6).count(),
                '6-10': grades_query.filter(grade__gte=6, grade__lt=11).count(),
                '11-15': grades_query.filter(grade__gte=11, grade__lt=16).count(),
                '16-20': grades_query.filter(grade__gte=16).count()
            }
            
            # Obtener notas por estudiante para gráficos
            notas_detalle = []
            for grade in grades_query.select_related('student__user'):
                notas_detalle.append({
                    'student_name': grade.student.user.get_full_name(),
                    'student_code': grade.student.student_code,
                    'exam_type': grade.exam_type,
                    'grade': float(grade.grade)
                })
            
            return {
                'success': True,
                'course_name': course.name,
                'fase': fase or 'Todas las fases',
                'estadisticas': {
                    'promedio': round(float(stats['promedio'] or 0), 2),
                    'nota_maxima': float(stats['nota_maxima'] or 0),
                    'nota_minima': float(stats['nota_minima'] or 0),
                    'total_notas': stats['total_notas']
                },
                'distribucion': notas_por_rango,
                'notas_detalle': notas_detalle,
                'fecha_calculo': timezone.now().isoformat()
            }
            
        except Course.DoesNotExist:
            return {
                'success': False,
                'error': 'Curso no encontrado',
                'error_code': 'COURSE_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error calculando estadísticas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def obtener_cursos_profesor(self, teacher_id: str) -> List[Dict]:
        """
        Obtener todos los cursos asignados a un profesor
        
        Args:
            teacher_id: ID del profesor
            
        Returns:
            Lista de cursos del profesor
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            course_groups = CourseGroup.objects.filter(
                teacher=teacher
            ).select_related('course', 'academic_period')
            
            cursos = []
            for cg in course_groups:
                # Contar estudiantes matriculados
                total_estudiantes = cg.enrolled_students
                
                # Contar notas registradas
                total_notas = Grade.objects.filter(course=cg.course).count()
                
                cursos.append({
                    'course_id': str(cg.course.id),
                    'course_group_id': str(cg.id),
                    'course_name': cg.course.name,
                    'course_code': cg.course.code,
                    'group_code': cg.group_code,
                    'total_estudiantes': total_estudiantes,
                    'total_notas': total_notas,
                    'academic_period': cg.academic_period.name,
                    'progress_percentage': cg.course_progress_percentage
                })
            
            return cursos
            
        except Teacher.DoesNotExist:
            self.logger.error(f"Profesor con ID {teacher_id} no encontrado")
            return []
        except Exception as e:
            self.logger.error(f"Error obteniendo cursos del profesor: {str(e)}")
            return []


# Instancia global del servicio
servicio_notas = ServicioNotas()