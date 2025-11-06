#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para cálculos estadísticos de notas por fases
Implementa estadísticas básicas y generación de datos para gráficos
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db import models
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone

from repositorio.postgres_repository.models import (
    PhaseGrade, Student, CourseGroup, Course, Teacher
)

logger = logging.getLogger(__name__)


class ServicioEstadisticasNotas:
    """
    Servicio para cálculos estadísticos de notas por fases académicas
    Implementa Requirements: 3.1, 3.2, 3.3, 6.1, 6.2
    """
    
    PHASE_CHOICES = ['primera', 'segunda', 'tercera']
    GRADE_RANGES = {
        '0-5': (0, 5.99),
        '6-10': (6, 10.99),
        '11-15': (11, 15.99),
        '16-20': (16, 20)
    }
    
    def __init__(self):
        self.logger = logger
    
    def calculate_basic_statistics(self, course_group_id: str, phase: str) -> Dict:
        """
        Calcula estadísticas básicas (max, min, promedio) para Primera fase
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica ('primera', 'segunda', 'tercera')
            
        Returns:
            Dict con estadísticas básicas
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            if phase not in self.PHASE_CHOICES:
                return {
                    'success': False,
                    'error': f'Fase inválida: {phase}. Debe ser una de: {self.PHASE_CHOICES}',
                    'error_code': 'INVALID_PHASE'
                }
            
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener todas las notas de la fase
            phase_grades = PhaseGrade.objects.filter(
                course_group=course_group,
                phase=phase
            ).select_related('student__user')
            
            if not phase_grades.exists():
                return {
                    'success': True,
                    'course_group_name': f"{course_group.course.name} - {course_group.group_code}",
                    'phase': phase,
                    'statistics': {
                        'max_grade': 0,
                        'min_grade': 0,
                        'average_grade': 0,
                        'total_students': 0,
                        'graded_students': 0
                    },
                    'message': 'No hay notas registradas para esta fase'
                }
            
            # Calcular estadísticas usando final_phase_grade
            stats = phase_grades.aggregate(
                max_grade=Max('final_phase_grade'),
                min_grade=Min('final_phase_grade'),
                avg_grade=Avg('final_phase_grade'),
                total_grades=Count('id')
            )
            
            # Contar estudiantes matriculados vs estudiantes con notas
            total_enrolled = course_group.enrolled_students
            graded_students = stats['total_grades']
            
            return {
                'success': True,
                'course_group_name': f"{course_group.course.name} - {course_group.group_code}",
                'phase': phase,
                'statistics': {
                    'max_grade': float(stats['max_grade'] or 0),
                    'min_grade': float(stats['min_grade'] or 0),
                    'average_grade': round(float(stats['avg_grade'] or 0), 2),
                    'total_students': total_enrolled,
                    'graded_students': graded_students,
                    'pending_students': total_enrolled - graded_students
                },
                'calculated_at': timezone.now().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error calculando estadísticas básicas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def calculate_grade_distribution(self, course_group_id: str, phase: str) -> Dict:
        """
        Calcula distribución de notas por rangos (0-5, 6-10, 11-15, 16-20)
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con distribución por rangos y porcentajes
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener todas las notas de la fase
            phase_grades = PhaseGrade.objects.filter(
                course_group=course_group,
                phase=phase
            )
            
            total_grades = phase_grades.count()
            
            if total_grades == 0:
                return {
                    'success': True,
                    'course_group_name': f"{course_group.course.name} - {course_group.group_code}",
                    'phase': phase,
                    'distribution': {range_name: {'count': 0, 'percentage': 0} for range_name in self.GRADE_RANGES.keys()},
                    'total_graded': 0,
                    'message': 'No hay notas para calcular distribución'
                }
            
            # Calcular distribución por rangos
            distribution = {}
            
            for range_name, (min_val, max_val) in self.GRADE_RANGES.items():
                if range_name == '16-20':
                    # Para el rango más alto, incluir el valor máximo
                    count = phase_grades.filter(
                        final_phase_grade__gte=min_val,
                        final_phase_grade__lte=max_val
                    ).count()
                else:
                    count = phase_grades.filter(
                        final_phase_grade__gte=min_val,
                        final_phase_grade__lt=max_val
                    ).count()
                
                percentage = round((count / total_grades) * 100, 1) if total_grades > 0 else 0
                
                distribution[range_name] = {
                    'count': count,
                    'percentage': percentage,
                    'range': f"{min_val}-{max_val if range_name != '16-20' else '20'}"
                }
            
            return {
                'success': True,
                'course_group_name': f"{course_group.course.name} - {course_group.group_code}",
                'phase': phase,
                'distribution': distribution,
                'total_graded': total_grades,
                'calculated_at': timezone.now().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error calculando distribución de notas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def calculate_student_count_and_percentages(self, course_group_id: str, phase: str) -> Dict:
        """
        Implementa conteo de estudiantes y cálculos de porcentajes
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con conteos y porcentajes detallados
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener estadísticas básicas y distribución
            basic_stats = self.calculate_basic_statistics(course_group_id, phase)
            distribution = self.calculate_grade_distribution(course_group_id, phase)
            
            if not basic_stats['success'] or not distribution['success']:
                return {
                    'success': False,
                    'error': 'Error obteniendo datos base para cálculos',
                    'error_code': 'BASE_DATA_ERROR'
                }
            
            stats = basic_stats['statistics']
            dist = distribution['distribution']
            
            # Calcular porcentajes adicionales
            total_enrolled = stats['total_students']
            graded_students = stats['graded_students']
            
            # Porcentaje de estudiantes evaluados
            evaluation_percentage = round((graded_students / total_enrolled) * 100, 1) if total_enrolled > 0 else 0
            
            # Estudiantes aprobados (nota >= 11)
            approved_count = dist['11-15']['count'] + dist['16-20']['count']
            failed_count = dist['0-5']['count'] + dist['6-10']['count']
            
            approval_rate = round((approved_count / graded_students) * 100, 1) if graded_students > 0 else 0
            failure_rate = round((failed_count / graded_students) * 100, 1) if graded_students > 0 else 0
            
            return {
                'success': True,
                'course_group_name': f"{course_group.course.name} - {course_group.group_code}",
                'phase': phase,
                'student_counts': {
                    'total_enrolled': total_enrolled,
                    'graded_students': graded_students,
                    'pending_students': total_enrolled - graded_students,
                    'approved_students': approved_count,
                    'failed_students': failed_count
                },
                'percentages': {
                    'evaluation_percentage': evaluation_percentage,
                    'approval_rate': approval_rate,
                    'failure_rate': failure_rate,
                    'pending_percentage': round(((total_enrolled - graded_students) / total_enrolled) * 100, 1) if total_enrolled > 0 else 0
                },
                'grade_distribution': dist,
                'basic_statistics': stats,
                'calculated_at': timezone.now().isoformat()
            }
            
        except CourseGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Grupo de curso no encontrado',
                'error_code': 'COURSE_GROUP_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error calculando conteos y porcentajes: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def get_comprehensive_statistics(self, course_group_id: str, phase: str) -> Dict:
        """
        Obtiene estadísticas completas combinando todos los cálculos
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con todas las estadísticas combinadas
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            # Obtener todos los cálculos
            student_stats = self.calculate_student_count_and_percentages(course_group_id, phase)
            
            if not student_stats['success']:
                return student_stats
            
            # Agregar información adicional del curso
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Obtener lista de estudiantes con sus notas
            phase_grades = PhaseGrade.objects.filter(
                course_group=course_group,
                phase=phase
            ).select_related('student__user').order_by('-final_phase_grade')
            
            student_details = []
            for grade in phase_grades:
                student_details.append({
                    'student_id': str(grade.student.id),
                    'student_code': grade.student.student_code,
                    'student_name': grade.student.user.get_full_name(),
                    'partial_grade': float(grade.partial_grade),
                    'continuous_grade': float(grade.continuous_grade),
                    'final_grade': float(grade.final_phase_grade),
                    'uploaded_at': grade.uploaded_at.isoformat()
                })
            
            return {
                'success': True,
                'course_info': {
                    'course_group_id': course_group_id,
                    'course_name': course_group.course.name,
                    'course_code': course_group.course.code,
                    'group_code': course_group.group_code,
                    'teacher_name': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar',
                    'academic_period': course_group.academic_period.name
                },
                'phase': phase,
                'statistics': student_stats,
                'student_details': student_details,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas completas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }


# Instancia global del servicio
servicio_estadisticas_notas = ServicioEstadisticasNotas()


class ServicioGeneradorGraficos:
    """
    Servicio para generar datos compatibles con Chart.js
    Implementa Requirements: 3.2, 6.1, 6.2
    """
    
    def __init__(self):
        self.logger = logger
        self.estadisticas_service = ServicioEstadisticasNotas()
    
    def generate_grade_distribution_chart_data(self, course_group_id: str, phase: str) -> Dict:
        """
        Genera datos compatibles con Chart.js para distribución de notas
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con estructura de datos para Chart.js
            
        Requirements: 3.2, 6.1, 6.2
        """
        try:
            # Obtener distribución de notas
            distribution_data = self.estadisticas_service.calculate_grade_distribution(course_group_id, phase)
            
            if not distribution_data['success']:
                return distribution_data
            
            distribution = distribution_data['distribution']
            
            # Preparar datos para Chart.js - Gráfico de barras
            labels = []
            data_counts = []
            data_percentages = []
            background_colors = []
            
            # Colores para cada rango
            colors = {
                '0-5': '#ff6384',    # Rojo para notas bajas
                '6-10': '#ff9f40',   # Naranja para notas regulares
                '11-15': '#ffcd56',  # Amarillo para notas buenas
                '16-20': '#4bc0c0'   # Verde para notas excelentes
            }
            
            for range_name in ['0-5', '6-10', '11-15', '16-20']:
                range_data = distribution[range_name]
                labels.append(range_data['range'])
                data_counts.append(range_data['count'])
                data_percentages.append(range_data['percentage'])
                background_colors.append(colors[range_name])
            
            # Estructura para Chart.js
            chart_data = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': 'Número de Estudiantes',
                            'data': data_counts,
                            'backgroundColor': background_colors,
                            'borderColor': background_colors,
                            'borderWidth': 1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': f'Distribución de Notas - {phase.title()} Fase'
                        },
                        'legend': {
                            'display': False
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Número de Estudiantes'
                            }
                        },
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Rangos de Notas'
                            }
                        }
                    }
                }
            }
            
            # Datos adicionales para mostrar en la interfaz
            summary_data = {
                'total_students': distribution_data['total_graded'],
                'course_name': distribution_data['course_group_name'],
                'phase': phase,
                'percentages': data_percentages
            }
            
            return {
                'success': True,
                'chart_data': chart_data,
                'summary': summary_data,
                'raw_distribution': distribution,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando datos de gráfico de distribución: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'CHART_GENERATION_ERROR'
            }
    
    def generate_statistics_summary_data(self, course_group_id: str, phase: str) -> Dict:
        """
        Genera datos de resumen estadístico para interfaces de profesor y estudiante
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con datos de resumen para mostrar en interfaces
            
        Requirements: 3.2, 6.1, 6.2
        """
        try:
            # Obtener estadísticas completas
            comprehensive_stats = self.estadisticas_service.get_comprehensive_statistics(course_group_id, phase)
            
            if not comprehensive_stats['success']:
                return comprehensive_stats
            
            stats = comprehensive_stats['statistics']
            course_info = comprehensive_stats['course_info']
            
            # Preparar datos de resumen para la interfaz del profesor
            teacher_summary = {
                'course_info': course_info,
                'phase': phase,
                'key_metrics': {
                    'total_enrolled': stats['student_counts']['total_enrolled'],
                    'graded_students': stats['student_counts']['graded_students'],
                    'pending_students': stats['student_counts']['pending_students'],
                    'evaluation_percentage': stats['percentages']['evaluation_percentage']
                },
                'grade_metrics': {
                    'average_grade': stats['basic_statistics']['average_grade'],
                    'max_grade': stats['basic_statistics']['max_grade'],
                    'min_grade': stats['basic_statistics']['min_grade'],
                    'approval_rate': stats['percentages']['approval_rate'],
                    'failure_rate': stats['percentages']['failure_rate']
                },
                'distribution_summary': {
                    'excellent': stats['grade_distribution']['16-20'],
                    'good': stats['grade_distribution']['11-15'],
                    'regular': stats['grade_distribution']['6-10'],
                    'poor': stats['grade_distribution']['0-5']
                }
            }
            
            # Preparar datos de resumen para la interfaz del estudiante
            student_summary = {
                'course_info': {
                    'course_name': course_info['course_name'],
                    'group_code': course_info['group_code'],
                    'teacher_name': course_info['teacher_name']
                },
                'phase': phase,
                'class_statistics': {
                    'class_average': stats['basic_statistics']['average_grade'],
                    'highest_grade': stats['basic_statistics']['max_grade'],
                    'lowest_grade': stats['basic_statistics']['min_grade'],
                    'total_graded': stats['student_counts']['graded_students']
                },
                'performance_context': {
                    'approval_rate': stats['percentages']['approval_rate'],
                    'class_performance': self._get_performance_level(stats['basic_statistics']['average_grade'])
                }
            }
            
            return {
                'success': True,
                'teacher_summary': teacher_summary,
                'student_summary': student_summary,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando datos de resumen estadístico: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'SUMMARY_GENERATION_ERROR'
            }
    
    def generate_pie_chart_data(self, course_group_id: str, phase: str) -> Dict:
        """
        Genera datos para gráfico de torta de distribución de notas
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con estructura de datos para gráfico de torta Chart.js
            
        Requirements: 3.2, 6.1, 6.2
        """
        try:
            # Obtener distribución de notas
            distribution_data = self.estadisticas_service.calculate_grade_distribution(course_group_id, phase)
            
            if not distribution_data['success']:
                return distribution_data
            
            distribution = distribution_data['distribution']
            
            # Preparar datos para Chart.js - Gráfico de torta
            labels = []
            data = []
            background_colors = []
            
            colors = {
                '0-5': '#ff6384',
                '6-10': '#ff9f40', 
                '11-15': '#ffcd56',
                '16-20': '#4bc0c0'
            }
            
            for range_name in ['0-5', '6-10', '11-15', '16-20']:
                range_data = distribution[range_name]
                if range_data['count'] > 0:  # Solo incluir rangos con datos
                    labels.append(f"{range_data['range']} ({range_data['count']} estudiantes)")
                    data.append(range_data['percentage'])
                    background_colors.append(colors[range_name])
            
            chart_data = {
                'type': 'pie',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'data': data,
                            'backgroundColor': background_colors,
                            'borderWidth': 2,
                            'borderColor': '#ffffff'
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': f'Distribución Porcentual - {phase.title()} Fase'
                        },
                        'legend': {
                            'position': 'bottom'
                        }
                    }
                }
            }
            
            return {
                'success': True,
                'chart_data': chart_data,
                'total_students': distribution_data['total_graded'],
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando gráfico de torta: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'PIE_CHART_ERROR'
            }
    
    def generate_combined_chart_data(self, course_group_id: str, phase: str) -> Dict:
        """
        Genera datos combinados para múltiples tipos de gráficos
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con datos para múltiples tipos de gráficos
            
        Requirements: 3.2, 6.1, 6.2
        """
        try:
            # Generar todos los tipos de gráficos
            bar_chart = self.generate_grade_distribution_chart_data(course_group_id, phase)
            pie_chart = self.generate_pie_chart_data(course_group_id, phase)
            summary = self.generate_statistics_summary_data(course_group_id, phase)
            
            if not all([bar_chart['success'], pie_chart['success'], summary['success']]):
                return {
                    'success': False,
                    'error': 'Error generando uno o más gráficos',
                    'error_code': 'COMBINED_CHART_ERROR'
                }
            
            return {
                'success': True,
                'charts': {
                    'bar_chart': bar_chart['chart_data'],
                    'pie_chart': pie_chart['chart_data']
                },
                'summary': summary,
                'course_group_id': course_group_id,
                'phase': phase,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generando datos combinados de gráficos: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'COMBINED_GENERATION_ERROR'
            }
    
    def _get_performance_level(self, average_grade: float) -> str:
        """
        Determina el nivel de rendimiento basado en el promedio
        
        Args:
            average_grade: Promedio de notas
            
        Returns:
            Nivel de rendimiento como string
        """
        if average_grade >= 16:
            return 'Excelente'
        elif average_grade >= 14:
            return 'Muy Bueno'
        elif average_grade >= 11:
            return 'Bueno'
        elif average_grade >= 8:
            return 'Regular'
        else:
            return 'Deficiente'


# Instancia global del servicio de gráficos
servicio_generador_graficos = ServicioGeneradorGraficos()


class ServicioActualizacionTiempoReal:
    """
    Servicio para actualizaciones en tiempo real de estadísticas
    Implementa Requirements: 3.1, 3.2, 3.3
    """
    
    def __init__(self):
        self.logger = logger
        self.estadisticas_service = ServicioEstadisticasNotas()
        self.graficos_service = ServicioGeneradorGraficos()
    
    def update_statistics_on_grade_submission(self, course_group_id: str, phase: str) -> Dict:
        """
        Actualiza estadísticas cuando se suben nuevas notas
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con estadísticas actualizadas
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            # Recalcular estadísticas completas
            updated_stats = self.estadisticas_service.get_comprehensive_statistics(course_group_id, phase)
            
            if not updated_stats['success']:
                return updated_stats
            
            # Generar datos de gráficos actualizados
            updated_charts = self.graficos_service.generate_combined_chart_data(course_group_id, phase)
            
            if not updated_charts['success']:
                return updated_charts
            
            # Preparar respuesta con datos actualizados
            return {
                'success': True,
                'updated_statistics': updated_stats,
                'updated_charts': updated_charts,
                'update_timestamp': timezone.now().isoformat(),
                'message': 'Estadísticas actualizadas exitosamente'
            }
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas en tiempo real: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'REALTIME_UPDATE_ERROR'
            }
    
    def get_real_time_statistics_data(self, course_group_id: str, phase: str) -> Dict:
        """
        Obtiene datos estadísticos para actualizaciones en tiempo real
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con datos optimizados para actualizaciones en tiempo real
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            # Obtener estadísticas básicas
            basic_stats = self.estadisticas_service.calculate_basic_statistics(course_group_id, phase)
            
            if not basic_stats['success']:
                return basic_stats
            
            # Obtener distribución
            distribution = self.estadisticas_service.calculate_grade_distribution(course_group_id, phase)
            
            if not distribution['success']:
                return distribution
            
            # Preparar datos optimizados para tiempo real
            real_time_data = {
                'course_group_id': course_group_id,
                'phase': phase,
                'quick_stats': {
                    'average': basic_stats['statistics']['average_grade'],
                    'max': basic_stats['statistics']['max_grade'],
                    'min': basic_stats['statistics']['min_grade'],
                    'total_graded': basic_stats['statistics']['graded_students'],
                    'total_enrolled': basic_stats['statistics']['total_students']
                },
                'distribution_counts': {
                    range_name: data['count'] 
                    for range_name, data in distribution['distribution'].items()
                },
                'last_updated': timezone.now().isoformat()
            }
            
            return {
                'success': True,
                'real_time_data': real_time_data,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de tiempo real: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'REALTIME_DATA_ERROR'
            }
    
    def trigger_statistics_refresh(self, course_group_id: str, phase: str) -> Dict:
        """
        Dispara una actualización completa de estadísticas
        
        Args:
            course_group_id: ID del grupo de curso
            phase: Fase académica
            
        Returns:
            Dict con resultado de la actualización
            
        Requirements: 3.1, 3.2, 3.3
        """
        try:
            self.logger.info(f"Disparando actualización de estadísticas para curso {course_group_id}, fase {phase}")
            
            # Actualizar estadísticas
            update_result = self.update_statistics_on_grade_submission(course_group_id, phase)
            
            if update_result['success']:
                self.logger.info(f"Estadísticas actualizadas exitosamente para curso {course_group_id}, fase {phase}")
            else:
                self.logger.error(f"Error actualizando estadísticas para curso {course_group_id}, fase {phase}: {update_result.get('error')}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error disparando actualización de estadísticas: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'REFRESH_TRIGGER_ERROR'
            }


# Instancia global del servicio de actualizaciones en tiempo real
servicio_actualizacion_tiempo_real = ServicioActualizacionTiempoReal()


# Funciones de utilidad para integración con otros servicios

def calculate_statistics_for_phase(course_group_id: str, phase: str) -> Dict:
    """
    Función de utilidad para calcular estadísticas de una fase
    
    Args:
        course_group_id: ID del grupo de curso
        phase: Fase académica
        
    Returns:
        Dict con estadísticas calculadas
    """
    return servicio_estadisticas_notas.get_comprehensive_statistics(course_group_id, phase)


def generate_charts_for_phase(course_group_id: str, phase: str) -> Dict:
    """
    Función de utilidad para generar gráficos de una fase
    
    Args:
        course_group_id: ID del grupo de curso
        phase: Fase académica
        
    Returns:
        Dict con datos de gráficos
    """
    return servicio_generador_graficos.generate_combined_chart_data(course_group_id, phase)


def update_statistics_after_grade_upload(course_group_id: str, phase: str) -> Dict:
    """
    Función de utilidad para actualizar estadísticas después de subir notas
    
    Args:
        course_group_id: ID del grupo de curso
        phase: Fase académica
        
    Returns:
        Dict con estadísticas actualizadas
    """
    return servicio_actualizacion_tiempo_real.update_statistics_on_grade_submission(course_group_id, phase)