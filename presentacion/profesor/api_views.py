"""
APIs para datos de gráficos del módulo de profesores
"""
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .mixins import ProfesorRequiredMixin
import json
from decimal import Decimal


class GradeStatisticsAPI(ProfesorRequiredMixin, View):
    """API para estadísticas de notas en formato JSON para gráficos"""
    
    def get(self, request):
        try:
            # Obtener parámetros
            evaluation_type = request.GET.get('evaluation_type', 'all')
            course_group_id = request.GET.get('course_group_id')
            
            with connection.cursor() as cursor:
                # Obtener distribución de notas por rangos
                distribution_data = self._get_grade_distribution(cursor, evaluation_type, course_group_id)
                
                # Obtener evolución de promedios
                evolution_data = self._get_grade_evolution(cursor, course_group_id)
                
                # Obtener comparación entre evaluaciones
                comparison_data = self._get_evaluation_comparison(cursor, course_group_id)
                
                return JsonResponse({
                    'success': True,
                    'distribution': distribution_data,
                    'evolution': evolution_data,
                    'comparison': comparison_data,
                    'metadata': {
                        'evaluation_type': evaluation_type,
                        'course_group_id': course_group_id,
                        'generated_at': str(timezone.now()) if 'timezone' in globals() else None
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Error al obtener estadísticas de notas'
            }, status=500)
    
    def _get_grade_distribution(self, cursor, evaluation_type='all', course_group_id=None):
        """Obtiene la distribución de notas por rangos"""
        
        # Construir query base - simplificada para funcionar con datos existentes
        base_query = """
            SELECT g.score
            FROM grades g
            JOIN evaluation_types et ON g.evaluation_type_id = et.id
            WHERE 1=1
        """
        
        params = []
        
        # Filtrar por tipo de evaluación específico
        if evaluation_type != 'all':
            base_query += " AND et.name = %s"
            params.append(evaluation_type)
        
        # Filtrar por course_group si se especifica
        if course_group_id:
            base_query += " AND cg.id = %s"
            params.append(course_group_id)
        
        cursor.execute(base_query, params)
        scores = [row[0] for row in cursor.fetchall()]
        
        # Calcular distribución por rangos
        ranges = {
            '0-5': 0,
            '6-10': 0,
            '11-15': 0,
            '16-20': 0
        }
        
        for score in scores:
            score_float = float(score) if score else 0
            if 0 <= score_float <= 5:
                ranges['0-5'] += 1
            elif 6 <= score_float <= 10:
                ranges['6-10'] += 1
            elif 11 <= score_float <= 15:
                ranges['11-15'] += 1
            elif 16 <= score_float <= 20:
                ranges['16-20'] += 1
        
        return {
            'ranges': ranges,
            'total_students': len(scores),
            'average': round(sum(scores) / len(scores), 2) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0
        }
    
    def _get_grade_evolution(self, cursor, course_group_id=None):
        """Obtiene la evolución de promedios por evaluación"""
        
        query = """
            SELECT 
                et.name,
                AVG(g.score) as average_score,
                COUNT(g.id) as student_count
            FROM evaluation_types et
            LEFT JOIN grades g ON et.id = g.evaluation_type_id
            WHERE 1=1
            GROUP BY et.id, et.name ORDER BY et.name
        """
        
        params = []
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        averages = {}
        counts = {}
        
        for row in results:
            eval_name, avg_score, count = row
            # Normalizar nombres de evaluación
            if 'Parcial 1' in eval_name:
                key = 'parcial1'
            elif 'Parcial 2' in eval_name:
                key = 'parcial2'
            elif 'Parcial 3' in eval_name:
                key = 'parcial3'
            else:
                key = eval_name.lower().replace(' ', '_')
            
            averages[key] = round(float(avg_score), 2) if avg_score else 0
            counts[key] = count or 0
        
        return {
            'averages': averages,
            'counts': counts
        }
    
    def _get_evaluation_comparison(self, cursor, course_group_id=None):
        """Obtiene comparación detallada entre evaluaciones"""
        
        query = """
            SELECT 
                et.name,
                et.weight,
                et.max_score,
                AVG(g.score) as avg_score,
                MIN(g.score) as min_score,
                MAX(g.score) as max_score,
                COUNT(g.id) as total_grades,
                COUNT(CASE WHEN g.score >= 10.5 THEN 1 END) as passed_count
            FROM evaluation_types et
            LEFT JOIN grades g ON et.id = g.evaluation_type_id
            LEFT JOIN course_groups cg ON et.course_group_id = cg.id
            WHERE 1=1
        """
        
        params = []
        if course_group_id:
            query += " AND cg.id = %s"
            params.append(course_group_id)
        
        query += " GROUP BY et.id, et.name, et.weight, et.max_score ORDER BY et.name"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        evaluations = []
        for row in results:
            name, weight, max_score, avg_score, min_score, max_score_actual, total_grades, passed_count = row
            
            evaluations.append({
                'name': name,
                'weight': float(weight) if weight else 0,
                'max_score': float(max_score) if max_score else 20,
                'average': round(float(avg_score), 2) if avg_score else 0,
                'min_score': float(min_score) if min_score else 0,
                'max_score_actual': float(max_score_actual) if max_score_actual else 0,
                'total_grades': total_grades or 0,
                'passed_count': passed_count or 0,
                'pass_rate': round((passed_count / total_grades * 100), 1) if total_grades > 0 else 0
            })
        
        return {
            'evaluations': evaluations,
            'total_evaluations': len(evaluations)
        }


class AttendanceStatisticsAPI(ProfesorRequiredMixin, View):
    """API para estadísticas de asistencia"""
    
    def get(self, request):
        try:
            course_group_id = request.GET.get('course_group_id')
            period = request.GET.get('period', 'current')  # current, week, month
            
            with connection.cursor() as cursor:
                # Por ahora, generar datos simulados ya que no tenemos registros reales de asistencia
                # TODO: Reemplazar con datos reales cuando se implemente el sistema de asistencia
                
                student_attendance = self._get_simulated_student_attendance(cursor, course_group_id)
                weekly_trends = self._get_simulated_weekly_trends()
                class_summary = self._get_simulated_class_summary()
                
                return JsonResponse({
                    'success': True,
                    'student_attendance': student_attendance,
                    'weekly_trends': weekly_trends,
                    'class_summary': class_summary,
                    'metadata': {
                        'course_group_id': course_group_id,
                        'period': period,
                        'note': 'Datos simulados - se actualizarán con registros reales'
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Error al obtener estadísticas de asistencia'
            }, status=500)
    
    def _get_simulated_student_attendance(self, cursor, course_group_id=None):
        """Genera datos simulados de asistencia por estudiante"""
        
        # Obtener estudiantes reales
        cursor.execute("""
            SELECT s.id, s.student_code, u.first_name, u.last_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.student_code
            LIMIT 15
        """)
        
        students = []
        import random
        
        for row in cursor.fetchall():
            student_id, code, first_name, last_name = row
            percentage = round(random.uniform(65, 98), 1)
            
            students.append({
                'id': str(student_id),
                'name': f"{first_name} {last_name}",
                'code': code,
                'percentage': percentage,
                'present': int(16 * percentage / 100),
                'absent': int(16 * (100 - percentage) / 100),
                'total_classes': 16
            })
        
        return {
            'students': students,
            'total_students': len(students)
        }
    
    def _get_simulated_weekly_trends(self):
        """Genera tendencias semanales simuladas"""
        import random
        
        weeks = []
        for i in range(1, 9):  # 8 semanas
            attendance_rate = round(random.uniform(75, 95), 1)
            weeks.append({
                'week': i,
                'attendance_rate': attendance_rate,
                'present_count': int(53 * attendance_rate / 100),
                'absent_count': int(53 * (100 - attendance_rate) / 100)
            })
        
        return {
            'weeks': weeks,
            'average_attendance': round(sum(w['attendance_rate'] for w in weeks) / len(weeks), 1)
        }
    
    def _get_simulated_class_summary(self):
        """Genera resumen general simulado"""
        import random
        
        total_students = 53
        present = random.randint(45, 52)
        absent = total_students - present
        
        return {
            'total_students': total_students,
            'present': present,
            'absent': absent,
            'late': random.randint(0, 3),
            'attendance_rate': round((present / total_students) * 100, 1)
        }