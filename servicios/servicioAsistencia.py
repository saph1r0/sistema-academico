#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de asistencia (COMPLETO Y CORREGIDO)
Maneja tanto la vista del Profesor como la del Estudiante
Usando el modelo: SimpleAttendanceRecord
"""

import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from datetime import date

# Importamos SOLO los modelos que realmente existen y se usan
from repositorio.postgres_repository.models import (
    Student, Teacher, CourseGroup, SimpleAttendanceRecord, Enrollment
)

logger = logging.getLogger(__name__)

class ServicioAsistencia:
    
    # Mapeo simple para la vista
    ESTADOS_ASISTENCIA = {
        'PRESENTE': 'Presente',
        'FALTA': 'Falta',
    }
    
    def __init__(self):
        self.logger = logger


    def registrar_asistencia_clase(self, teacher_id: str, course_group_id: str, 
                                 fecha: date, asistencias: List[Dict]) -> Dict:
        """
        Registra la asistencia delegando la lógica al modelo SimpleAttendanceRecord
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            # Usamos el método inteligente que ya escribiste en models.py
            created, updated, errors = SimpleAttendanceRecord.record_bulk_attendance(
                teacher=teacher,
                course_group=course_group,
                class_date=fecha,
                attendance_data=asistencias
            )
            
            return {
                'success': True,
                'registros_exitosos': created + updated,
                'created': created,
                'updated': updated,
                'total_errores': len(errors),
                'errores': errors,
                'fecha': fecha.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error registrando asistencia: {str(e)}")
            return {'success': False, 'error': str(e)}

    def obtener_reporte_asistencia(self, course_group_id: str, 
                                 fecha_inicio: date = None, fecha_fin: date = None) -> Dict:
        """
        Reporte mensual/semestral para el PROFESOR (Vista de lista de alumnos)
        Adaptado para leer SimpleAttendanceRecord
        """
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            
            if not fecha_inicio:
                fecha_inicio = timezone.now().date().replace(day=1)
            if not fecha_fin:
                fecha_fin = timezone.now().date()
            
            # 1. Obtener todos los registros del rango
            records = SimpleAttendanceRecord.objects.filter(
                course_group=course_group,
                class_date__range=[fecha_inicio, fecha_fin]
            ).select_related('student__user')
            
            # 2. Agrupar por estudiante
            reporte_por_estudiante = {}
            
            # Inicializamos con todos los matriculados para que aparezcan aunque no tengan asistencia
            matriculados = Enrollment.objects.filter(course_group=course_group, status='active')
            for matricula in matriculados:
                std_code = matricula.student.student_code
                reporte_por_estudiante[std_code] = {
                    'student_name': matricula.student.user.get_full_name(),
                    'student_code': std_code,
                    'total_clases': 0,
                    'presentes': 0,
                    'faltas': 0,
                    'porcentaje_asistencia': 0,
                    'detalle_por_fecha': {}
                }

            # 3. Llenar con datos reales
            for record in records:
                code = record.student.student_code
                if code in reporte_por_estudiante:
                    data = reporte_por_estudiante[code]
                    data['total_clases'] += 1
                    
                    if record.status == 'PRESENTE':
                        data['presentes'] += 1
                    else:
                        data['faltas'] += 1
                        
                    # Guardar detalle por fecha (útil para calendarios)
                    data['detalle_por_fecha'][record.class_date.isoformat()] = record.status

            # 4. Calcular porcentajes finales
            lista_final = []
            suma_porcentajes = 0
            count_students = 0

            for data in reporte_por_estudiante.values():
                if data['total_clases'] > 0:
                    data['porcentaje_asistencia'] = round(
                        (data['presentes'] / data['total_clases']) * 100, 1
                    )
                lista_final.append(data)
                suma_porcentajes += data['porcentaje_asistencia']
                count_students += 1

            promedio_curso = round(suma_porcentajes / count_students, 1) if count_students > 0 else 0

            return {
                'success': True,
                'course_name': course_group.course.name,
                'group_code': course_group.group_code,
                'periodo': {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                },
                'estadisticas_generales': {
                    'total_estudiantes': count_students,
                    'promedio_asistencia': promedio_curso
                },
                'reporte_por_estudiante': lista_final
            }

        except Exception as e:
            self.logger.error(f"Error en reporte profesor: {str(e)}")
            return {'success': False, 'error': str(e)}


    def obtener_reporte_asistencia_estudiante(self, student_id: str) -> Dict:
        """
        Reporte para el Dashboard del ESTUDIANTE.
        Muestra todos sus cursos y su % de asistencia en cada uno.
        """
        try:
            student = Student.objects.get(id=student_id)
            
            # Obtener cursos donde está matriculado activamente
            enrollments = Enrollment.objects.filter(
                student=student,
                status='active'
            ).select_related('course_group__course')
            
            reporte_cursos = []
            
            for enrollment in enrollments:
                cg = enrollment.course_group
                
                # Consultar tabla SimpleAttendanceRecord
                records = SimpleAttendanceRecord.objects.filter(
                    student=student,
                    course_group=cg
                ).order_by('-class_date')
                
                total = records.count()
                presentes = records.filter(status='PRESENTE').count()
                faltas = records.filter(status='FALTA').count()
                
                porcentaje = (presentes / total * 100) if total > 0 else 0
                
                # Tomar las últimas 5 asistencias para mostrar detalle rápido
                ultimos = records[:5]
                detalle_ultimos = [{
                    'fecha': r.class_date,
                    'estado': r.status
                } for r in ultimos]
                
                reporte_cursos.append({
                    'curso': cg.course.name,
                    'codigo_curso': cg.course.code,
                    'grupo': cg.group_code,
                    'total_clases': total,
                    'presentes': presentes,
                    'faltas': faltas,
                    'porcentaje': round(porcentaje, 1),
                    'ultimos_registros': detalle_ultimos
                })
                
            return {
                'success': True,
                'student_name': student.user.get_full_name(),
                'cursos': reporte_cursos
            }
            
        except Exception as e:
            self.logger.error(f"Error reporte estudiante: {str(e)}")
            return {'success': False, 'error': str(e)}

# Instancia global
servicio_asistencia = ServicioAsistencia()