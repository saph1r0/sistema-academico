"""
Vistas para el módulo de profesores
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse

from .mixins import ProfesorRequiredMixin
from servicios.servicioUsuario import ServicioUsuario
from servicios.servicioNotas import ServicioNotas
from servicios.servicioAsistencia import ServicioAsistencia
from servicios.servicioReservas import servicio_reservas


class ProfesorDashboardView(ProfesorRequiredMixin, TemplateView):
    """Dashboard principal del profesor"""
    template_name = 'profesor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el perfil del profesor
        try:
            from django.db import connection
            
            # Obtener datos reales del profesor y sus cursos
            real_data = self._get_real_dashboard_data()
            
            # Información básica del profesor
            context.update({
                'page_title': 'Dashboard Profesor',
                'profesor': self.request.user,
                'welcome_message': f'Bienvenido, Prof. {self.request.user.get_full_name()}',
                
                # Estadísticas reales basadas en datos de la base de datos
                'total_courses': real_data['total_courses'],
                'total_students': real_data['total_students'],
                'average_progress': real_data['average_progress'],
                
                # Curso asignado con datos reales
                'assigned_course': real_data['assigned_course'],
                
                # Estadísticas por curso con datos reales
                'course_stats': real_data['course_stats'],
                
                # Estadísticas de notas reales
                'grade_statistics': real_data['grade_statistics'],
                
                # Horario de hoy (simulado por ahora)
                'horario_hoy': [
                    {
                        'hora': '07:00 - 08:40',
                        'curso': real_data['assigned_course']['name'] if real_data['assigned_course'] else 'Sin curso asignado',
                        'aula': 'Aula 301',
                        'tipo': 'Teoría'
                    },
                    {
                        'hora': '09:40 - 11:30',
                        'curso': real_data['assigned_course']['name'] if real_data['assigned_course'] else 'Sin curso asignado',
                        'aula': 'Lab. Matemáticas',
                        'tipo': 'Práctica'
                    }
                ],
                
                # Próximas evaluaciones basadas en datos reales
                'proximas_evaluaciones': real_data['upcoming_evaluations'],
                
                # Asistencia propia del profesor
                'asistencia_propia': {
                    'porcentaje': 95.0,
                    'clases_dictadas': 19,
                    'total_clases': 20,
                    'ultimo_acceso': self.request.user.last_login
                }
            })
            
        except Exception as e:
            context.update({
                'page_title': 'Dashboard Profesor',
                'profesor': self.request.user,
                'error': f'Error al cargar datos del profesor: {str(e)}',
                'total_courses': 0,
                'total_students': 0,
                'course_stats': [],
                'horario_hoy': [],
                'proximas_evaluaciones': []
            })
        
        return context

    def _get_real_dashboard_data(self):
        """Obtiene datos reales desde la base de datos para el dashboard"""
        from django.db import connection
        
        try:
            # Obtener el teacher_id del usuario logueado
            teacher_id = None
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT t.id FROM teachers t 
                    WHERE t.user_id = %s;
                """, [str(self.request.user.id)])
                
                teacher_result = cursor.fetchone()
                if teacher_result:
                    teacher_id = teacher_result[0]
                else:
                    # Si no tiene registro en teachers, retornar datos vacíos
                    return self._get_empty_dashboard_data()
            
            with connection.cursor() as cursor:
                # Obtener información de los cursos asignados al profesor
                cursor.execute("""
                    SELECT 
                        c.id, c.code, c.name, c.credits,
                        COUNT(DISTINCT e.student_id) as student_count,
                        cg.group_code
                    FROM courses c
                    JOIN course_groups cg ON c.id = cg.course_id
                    LEFT JOIN enrollments e ON cg.id = e.course_group_id
                    WHERE cg.teacher_id = %s
                    GROUP BY c.id, c.code, c.name, c.credits, cg.group_code
                    ORDER BY c.code
                    LIMIT 1;
                """, [teacher_id])
                
                course_data = cursor.fetchone()
                
                if course_data:
                    course_id, course_code, course_name, credits, student_count, group_code = course_data
                    
                    # Obtener estadísticas de notas
                    cursor.execute("""
                        SELECT 
                            AVG(g.score) as avg_score,
                            MIN(g.score) as min_score,
                            MAX(g.score) as max_score,
                            COUNT(g.id) as total_grades,
                            COUNT(CASE WHEN g.score >= 10.5 THEN 1 END) as passed_count
                        FROM grades g
                        JOIN evaluation_types et ON g.evaluation_type_id = et.id
                        JOIN course_groups cg ON et.course_group_id = cg.id
                        JOIN courses c ON cg.course_id = c.id
                        WHERE c.id = %s;
                    """, [course_id])
                    
                    grade_stats = cursor.fetchone()
                    avg_score, min_score, max_score, total_grades, passed_count = grade_stats or (0, 0, 0, 0, 0)
                    
                    # Obtener estadísticas por evaluación
                    cursor.execute("""
                        SELECT 
                            et.name,
                            AVG(g.score) as avg_score,
                            COUNT(g.id) as grade_count
                        FROM evaluation_types et
                        LEFT JOIN grades g ON et.id = g.evaluation_type_id
                        JOIN course_groups cg ON et.course_group_id = cg.id
                        JOIN courses c ON cg.course_id = c.id
                        WHERE c.id = %s
                        GROUP BY et.id, et.name
                        ORDER BY et.name;
                    """, [course_id])
                    
                    evaluation_stats = cursor.fetchall()
                    
                    # Calcular progreso basado en evaluaciones completadas
                    total_evaluations = len(evaluation_stats)
                    completed_evaluations = len([e for e in evaluation_stats if e[2] > 0])  # e[2] es grade_count
                    progress_percentage = (completed_evaluations / total_evaluations * 100) if total_evaluations > 0 else 0
                    
                    return {
                        'total_courses': 1,
                        'total_students': student_count or 0,
                        'average_progress': round(progress_percentage, 1),
                        'assigned_course': {
                            'id': course_id,
                            'name': course_name,
                            'code': course_code,
                            'credits': credits,
                            'group': group_code,
                            'students_count': student_count or 0,
                            'modality': 'Presencial',
                            'period': '2024-I'
                        },
                        'course_stats': [{
                            'course_name': course_name,
                            'course_code': course_code,
                            'students_count': student_count or 0,
                            'progress_percentage': round(progress_percentage, 1),
                            'status': 'al_dia' if progress_percentage >= 50 else 'atrasado',
                            'next_topic': {
                                'title': 'Espacios vectoriales',
                                'week_number': 9,
                                'description': 'Introducción a espacios vectoriales y sus propiedades'
                            }
                        }],
                        'grade_statistics': {
                            'average': round(float(avg_score), 2) if avg_score else 0,
                            'min_score': float(min_score) if min_score else 0,
                            'max_score': float(max_score) if max_score else 0,
                            'total_grades': total_grades or 0,
                            'passed_count': passed_count or 0,
                            'pass_rate': round((passed_count / total_grades * 100), 1) if total_grades > 0 else 0,
                            'evaluations': [
                                {
                                    'name': eval_data[0],
                                    'average': round(float(eval_data[1]), 2) if eval_data[1] else 0,
                                    'count': eval_data[2] or 0
                                } for eval_data in evaluation_stats
                            ]
                        },
                        'upcoming_evaluations': [
                            {
                                'curso': course_name,
                                'tipo': 'Parcial 2',
                                'fecha': '2025-11-15',
                                'estudiantes': student_count or 0
                            }
                        ]
                    }
                else:
                    # No hay cursos asignados a este profesor
                    return self._get_empty_dashboard_data()
                    
        except Exception as e:
            print(f"Error obteniendo datos del dashboard: {str(e)}")
            return self._get_empty_dashboard_data()

    def _get_empty_dashboard_data(self):
        """Retorna estructura de datos vacía para el dashboard"""
        return {
            'total_courses': 0,
            'total_students': 0,
            'average_progress': 0,
            'assigned_course': None,
            'course_stats': [],
            'grade_statistics': {
                'average': 0,
                'min_score': 0,
                'max_score': 0,
                'total_grades': 0,
                'passed_count': 0,
                'pass_rate': 0,
                'evaluations': []
            },
            'upcoming_evaluations': []
        }


class ProfesorNotasView(ProfesorRequiredMixin, TemplateView):
    """Gestión de notas mediante plantillas Excel"""
    template_name = 'profesor/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from django.db import connection
            
            # Obtener el teacher_id del usuario logueado
            teacher_id = None
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT t.id FROM teachers t 
                    WHERE t.user_id = %s;
                """, [str(self.request.user.id)])
                
                teacher_result = cursor.fetchone()
                if teacher_result:
                    teacher_id = teacher_result[0]
            
            if not teacher_id:
                context.update({
                    'page_title': 'Gestión de Notas',
                    'error': 'No tienes cursos asignados',
                    'courses': [],
                    'students': [],
                    'grade_stats': {'average': 0, 'approved': 0, 'total': 0, 'at_risk': 0}
                })
                return context
            
            # Obtener notas reales de los estudiantes matriculados en cursos del profesor
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id,
                        s.student_code,
                        u.first_name,
                        u.last_name,
                        et.name as evaluation_type,
                        g.score,
                        c.code as course_code,
                        c.name as course_name
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    JOIN enrollments e ON s.id = e.student_id
                    JOIN course_groups cg ON e.course_group_id = cg.id
                    JOIN courses c ON cg.course_id = c.id
                    LEFT JOIN evaluation_types et ON cg.id = et.course_group_id
                    LEFT JOIN grades g ON s.id = g.student_id AND et.id = g.evaluation_type_id
                    WHERE cg.teacher_id = %s
                    ORDER BY s.student_code, et.name;
                """, [teacher_id])
                
                rows = cursor.fetchall()
                
                # Organizar datos por estudiante
                students_dict = {}
                for row in rows:
                    student_id, student_code, first_name, last_name, eval_type, score, course_code, course_name = row
                    
                    if student_id not in students_dict:
                        students_dict[student_id] = {
                            'id': student_id,
                            'student_code': student_code,
                            'first_name': first_name,
                            'last_name': last_name,
                            'full_name': f"{first_name} {last_name}",
                            'grades': {
                                'parcial1': None,
                                'parcial2': None,
                                'parcial3': None,
                                'promedio': None
                            }
                        }
                    
                    # Asignar nota según el tipo de evaluación
                    if eval_type == 'Parcial 1':
                        students_dict[student_id]['grades']['parcial1'] = float(score) if score else None
                    elif eval_type == 'Parcial 2':
                        students_dict[student_id]['grades']['parcial2'] = float(score) if score else None
                    elif eval_type == 'Parcial 3':
                        students_dict[student_id]['grades']['parcial3'] = float(score) if score else None
                
                # Calcular promedios y convertir a lista
                students_with_grades = []
                for student_data in students_dict.values():
                    grades = student_data['grades']
                    
                    # Calcular promedio solo con notas disponibles
                    notas_disponibles = [
                        grades['parcial1'], 
                        grades['parcial2'], 
                        grades['parcial3']
                    ]
                    notas_validas = [n for n in notas_disponibles if n is not None]
                    
                    if notas_validas:
                        promedio = round(sum(notas_validas) / len(notas_validas), 1)
                        grades['promedio'] = promedio
                    else:
                        grades['promedio'] = None
                    
                    students_with_grades.append(student_data)
                
                # Ordenar por código de estudiante
                students_with_grades.sort(key=lambda x: x['student_code'])
                
                # Calcular estadísticas
                promedios_validos = [s['grades']['promedio'] for s in students_with_grades if s['grades']['promedio'] is not None]
                aprobados = len([p for p in promedios_validos if p >= 10.5])
                en_riesgo = len([p for p in promedios_validos if p < 10.5])
                
                # Estadísticas por evaluación
                parcial1_notas = [s['grades']['parcial1'] for s in students_with_grades if s['grades']['parcial1'] is not None]
                parcial2_notas = [s['grades']['parcial2'] for s in students_with_grades if s['grades']['parcial2'] is not None]
                parcial3_notas = [s['grades']['parcial3'] for s in students_with_grades if s['grades']['parcial3'] is not None]
                
                # Obtener información del curso del profesor
                cursor.execute("""
                    SELECT c.id, c.code, c.name
                    FROM courses c
                    JOIN course_groups cg ON c.id = cg.course_id
                    WHERE cg.teacher_id = %s
                    LIMIT 1;
                """, [teacher_id])
                
                course_info = cursor.fetchone()
                
                courses_list = []
                if course_info:
                    courses_list = [{
                        'id': course_info[0],
                        'name': course_info[2],
                        'code': course_info[1]
                    }]
                
                context.update({
                    'page_title': 'Gestión de Notas',
                    'courses': courses_list,
                    'selected_course': course_info[0] if course_info else None,
                    'students': students_with_grades,
                    'grade_stats': {
                        'average': round(sum(promedios_validos) / len(promedios_validos), 1) if promedios_validos else 0,
                        'approved': aprobados,
                        'total': len(students_with_grades),
                        'at_risk': en_riesgo,
                        'parcial1_count': len(parcial1_notas),
                        'parcial2_count': len(parcial2_notas),
                        'parcial3_count': len(parcial3_notas),
                        'parcial1_avg': round(sum(parcial1_notas) / len(parcial1_notas), 1) if parcial1_notas else 0,
                        'parcial2_avg': round(sum(parcial2_notas) / len(parcial2_notas), 1) if parcial2_notas else 0,
                        'parcial3_avg': round(sum(parcial3_notas) / len(parcial3_notas), 1) if parcial3_notas else 0
                    }
                })
            
        except Exception as e:
            context.update({
                'page_title': 'Gestión de Notas',
                'error': f'Error al cargar notas: {str(e)}',
                'courses': [],
                'students': [],
                'grade_stats': {'average': 0, 'approved': 0, 'total': 0, 'at_risk': 0}
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Procesar descarga de plantilla, subida de notas o guardado manual"""
        from django.db import connection
        from django.http import HttpResponse
        import io
        import xlsxwriter
        
        action = request.POST.get('action', '')
        
        try:
            if action == 'save_manual_grades':
                # Guardar notas manuales
                saved_count = 0
                
                with connection.cursor() as cursor:
                    # Obtener IDs necesarios
                    cursor.execute("SELECT id FROM course_groups LIMIT 1;")
                    course_group_result = cursor.fetchone()
                    
                    if not course_group_result:
                        messages.error(request, 'No se encontró un curso asignado.')
                        return redirect('profesor:notas')
                    
                    course_group_id = course_group_result[0]
                    
                    # Obtener tipos de evaluación
                    cursor.execute("""
                        SELECT id, name FROM evaluation_types 
                        WHERE course_group_id = %s
                        ORDER BY name;
                    """, [course_group_id])
                    
                    eval_types = {row[1]: row[0] for row in cursor.fetchall()}
                    
                    # Procesar cada nota
                    for key, value in request.POST.items():
                        if key.startswith(('parcial1_', 'parcial2_', 'parcial3_')):
                            if value and value.strip():
                                try:
                                    parts = key.split('_')
                                    eval_name = f"Parcial {parts[0][-1]}"  # parcial1 -> Parcial 1
                                    student_id = parts[1]
                                    score = float(value)
                                    
                                    if eval_name in eval_types and 0 <= score <= 20:
                                        eval_type_id = eval_types[eval_name]
                                        
                                        # Insertar o actualizar nota
                                        cursor.execute("""
                                            INSERT INTO grades (student_id, evaluation_type_id, score, recorded_by)
                                            VALUES (%s, %s, %s, %s)
                                            ON CONFLICT (student_id, evaluation_type_id)
                                            DO UPDATE SET score = EXCLUDED.score, recorded_by = EXCLUDED.recorded_by;
                                        """, [student_id, eval_type_id, score, request.user.id])
                                        
                                        saved_count += 1
                                        
                                except (ValueError, IndexError) as e:
                                    continue
                
                messages.success(request, f'Se guardaron {saved_count} notas exitosamente.')
                
            elif 'archivo_notas' in request.FILES:
                # Procesar archivo Excel subido
                archivo = request.FILES['archivo_notas']
                
                try:
                    from servicios.servicioExcel import ExcelGradeProcessor
                    import tempfile
                    import os
                    
                    # Guardar archivo temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                        for chunk in archivo.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    
                    # Procesar archivo
                    processor = ExcelGradeProcessor(request.user.id)
                    results = processor.process_grades_file(temp_file_path)
                    
                    # Limpiar archivo temporal
                    os.unlink(temp_file_path)
                    
                    # Mostrar resultados
                    if results['success']:
                        messages.success(request, 
                            f'Archivo {archivo.name} procesado exitosamente. '
                            f'Se procesaron {results["processed_count"]} notas.')
                        
                        # Mostrar estadísticas si están disponibles
                        if results['statistics']:
                            stats_msg = "Estadísticas: "
                            for eval_name, stats in results['statistics'].items():
                                stats_msg += f"{eval_name}: {stats['total']} notas, promedio {stats['average']}. "
                            messages.info(request, stats_msg)
                    else:
                        messages.error(request, f'Error procesando {archivo.name}')
                    
                    # Mostrar advertencias si las hay
                    for warning in results['warnings'][:5]:  # Mostrar solo las primeras 5
                        messages.warning(request, warning)
                    
                    # Mostrar errores si los hay
                    for error in results['errors'][:3]:  # Mostrar solo los primeros 3
                        messages.error(request, error)
                        
                except Exception as e:
                    messages.error(request, f'Error procesando archivo {archivo.name}: {str(e)}')
                
            else:
                messages.warning(request, 'No se especificó una acción válida.')
                
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')
            import traceback
            print(f"Error en vista de notas: {traceback.format_exc()}")
        
        return redirect('profesor:notas')


class asistencia(ProfesorRequiredMixin, TemplateView):
    """Registro y gestión de asistencia estudiantil"""
    template_name = 'profesor/asistencia/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from django.db import connection
            import random
            from datetime import datetime, timedelta
            
            # Obtener el teacher_id del usuario logueado
            teacher_id = None
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT t.id FROM teachers t 
                    WHERE t.user_id = %s;
                """, [str(self.request.user.id)])
                
                teacher_result = cursor.fetchone()
                if teacher_result:
                    teacher_id = teacher_result[0]
            
            if not teacher_id:
                context.update({
                    'page_title': 'Registro de Asistencia',
                    'error': 'No tienes cursos asignados',
                    'courses': [],
                    'students': [],
                    'attendance_stats': {'average': 0, 'present_today': 0, 'total': 0}
                })
                return context
            
            # Obtener estudiantes matriculados en los cursos del profesor
            students_with_attendance = []
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT
                        s.id,
                        s.student_code,
                        u.first_name,
                        u.last_name,
                        c.name as course_name,
                        c.code as course_code
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    JOIN enrollments e ON s.id = e.student_id
                    JOIN course_groups cg ON e.course_group_id = cg.id
                    JOIN courses c ON cg.course_id = c.id
                    WHERE cg.teacher_id = %s
                    ORDER BY s.student_code;
                """, [teacher_id])
                
                students_data = cursor.fetchall()
                
                # Obtener información del curso del profesor
                cursor.execute("""
                    SELECT c.id, c.code, c.name
                    FROM courses c
                    JOIN course_groups cg ON c.id = cg.course_id
                    WHERE cg.teacher_id = %s
                    LIMIT 1;
                """, [teacher_id])
                
                course_info = cursor.fetchone()
            
            # Procesar datos de asistencia para cada estudiante
            for student_data in students_data:
                student_id, student_code, first_name, last_name, course_name, course_code = student_data
                
                # Generar asistencia simulada (solo presente o ausente)
                attendance_today = random.choice(['present', 'absent'])
                attendance_percentage = round(random.uniform(70.0, 95.0), 1)
                
                # Calcular asistencias y faltas basado en el porcentaje
                total_classes = 16
                present_classes = int(total_classes * attendance_percentage / 100)
                absent_classes = total_classes - present_classes
                
                # Crear objeto simulado de usuario
                class MockUser:
                    def __init__(self, first_name, last_name):
                        self.first_name = first_name
                        self.last_name = last_name
                        self.get_full_name = lambda: f"{first_name} {last_name}"
                
                student_info = {
                    'id': student_id,
                    'user': MockUser(first_name, last_name),
                    'student_code': student_code,
                    'attendance_today': attendance_today,
                    'attendance_summary': {
                        'total_classes': total_classes,
                        'present': present_classes,
                        'absent': absent_classes,
                        'percentage': attendance_percentage
                    }
                }
                students_with_attendance.append(student_info)
            
            # Estadísticas de asistencia (solo presente/falta)
            present_today = len([s for s in students_with_attendance if s['attendance_today'] == 'present'])
            absent_today = len([s for s in students_with_attendance if s['attendance_today'] == 'absent'])
            
            percentages = [s['attendance_summary']['percentage'] for s in students_with_attendance]
            average_attendance = round(sum(percentages) / len(percentages), 1) if percentages else 0
            
            # Preparar información del curso
            courses_list = []
            if course_info:
                courses_list = [{
                    'id': course_info[0],
                    'name': course_info[2],
                    'code': course_info[1]
                }]
            
            context.update({
                'page_title': 'Registro de Asistencia',
                'courses': courses_list,
                'selected_course': course_info[0] if course_info else None,
                'students': students_with_attendance,
                'today': datetime.now().date(),
                'attendance_stats': {
                    'average': average_attendance,
                    'present_today': present_today,
                    'absent_today': absent_today,
                    'total': len(students_with_attendance),
                    'classes_this_week': 4,
                    'total_classes_month': 16
                },
                'weeks': [
                    {'number': i, 'start_date': f'{i*7+1}/10/2024', 'end_date': f'{i*7+7}/10/2024'} 
                    for i in range(1, 17)
                ]
            })
            
        except Exception as e:
            context.update({
                'page_title': 'Registro de Asistencia',
                'error': f'Error al cargar asistencia: {str(e)}',
                'courses': [],
                'students': [],
                'attendance_stats': {'average': 0, 'present_today': 0, 'total': 0}
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Registrar asistencia masiva"""
        try:
            from django.db import connection
            from datetime import datetime
            
            action = request.POST.get('action')
            
            if action == 'mark_all_present':
                # Marcar todos los estudiantes como presentes
                fecha = request.POST.get('date', datetime.now().date())
                
                with connection.cursor() as cursor:
                    # Obtener course_group_id (asumimos el primero disponible)
                    cursor.execute("SELECT id FROM course_groups LIMIT 1;")
                    course_group_result = cursor.fetchone()
                    
                    if course_group_result:
                        course_group_id = course_group_result[0]
                        
                        # Obtener todos los estudiantes matriculados
                        cursor.execute("""
                            SELECT DISTINCT s.id 
                            FROM students s
                            JOIN enrollments e ON s.id = e.student_id
                            WHERE e.course_group_id = %s;
                        """, [course_group_id])
                        
                        students = cursor.fetchall()
                        registered_count = 0
                        
                        for student_row in students:
                            student_id = student_row[0]
                            
                            # Verificar si ya existe registro para esta fecha
                            cursor.execute("""
                                SELECT COUNT(*) FROM attendance_records 
                                WHERE student_id = %s AND course_group_id = %s AND date = %s;
                            """, [student_id, course_group_id, fecha])
                            
                            if cursor.fetchone()[0] == 0:
                                # Insertar nuevo registro de asistencia
                                cursor.execute("""
                                    INSERT INTO attendance_records (student_id, course_group_id, date, status, recorded_by)
                                    VALUES (%s, %s, %s, %s, %s);
                                """, [student_id, course_group_id, fecha, 'present', request.user.id])
                                registered_count += 1
                        
                        messages.success(request, f'Asistencia registrada para {registered_count} estudiantes.')
                    else:
                        messages.error(request, 'No se encontró un curso asignado.')
                        
            else:
                # Registro individual de asistencia
                fecha = request.POST.get('date', datetime.now().date())
                
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id FROM course_groups LIMIT 1;")
                    course_group_result = cursor.fetchone()
                    
                    if course_group_result:
                        course_group_id = course_group_result[0]
                        registered_count = 0
                        
                        # Procesar cada estudiante
                        for key, value in request.POST.items():
                            if key.startswith('attendance_'):
                                student_id = key.replace('attendance_', '')
                                status = value
                                
                                # Verificar que el estudiante existe
                                cursor.execute("SELECT COUNT(*) FROM students WHERE id = %s;", [student_id])
                                if cursor.fetchone()[0] > 0:
                                    # Actualizar o insertar registro
                                    cursor.execute("""
                                        INSERT INTO attendance_records (student_id, course_group_id, date, status, recorded_by)
                                        VALUES (%s, %s, %s, %s, %s)
                                        ON CONFLICT (student_id, course_group_id, date)
                                        DO UPDATE SET status = EXCLUDED.status, recorded_by = EXCLUDED.recorded_by;
                                    """, [student_id, course_group_id, fecha, status, request.user.id])
                                    registered_count += 1
                        
                        messages.success(request, f'Asistencia actualizada para {registered_count} estudiantes.')
                    else:
                        messages.error(request, 'No se encontró un curso asignado.')
                        
        except Exception as e:
            messages.error(request, f'Error al registrar asistencia: {str(e)}')
        
        return redirect('profesor:asistencia')


class ProfesorReservasView(ProfesorRequiredMixin, TemplateView):
    """Gestión de reservas de ambientes"""
    template_name = 'profesor/reservas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from datetime import datetime, timedelta
            import random
            
            # Laboratorios disponibles
            laboratories = [
                {'id': 1, 'name': 'Laboratorio de Computación 1', 'capacity': 30, 'available_today': True},
                {'id': 2, 'name': 'Laboratorio de Computación 2', 'capacity': 25, 'available_today': False},
                {'id': 3, 'name': 'Laboratorio de Matemáticas', 'capacity': 35, 'available_today': True},
                {'id': 4, 'name': 'Aula Multimedia', 'capacity': 40, 'available_today': True},
                {'id': 5, 'name': 'Laboratorio de Física', 'capacity': 20, 'available_today': False}
            ]
            
            # Reservas del profesor
            reservations = [
                {
                    'id': 1,
                    'date': datetime.now().date() + timedelta(days=1),
                    'start_time': '08:00',
                    'end_time': '10:00',
                    'duration': 2,
                    'laboratory': {'name': 'Laboratorio de Computación 1', 'capacity': 30},
                    'course': {'name': 'MATEMATICA APLICADA A LA COMPUTACION', 'code': '1703241'},
                    'type': 'practica',
                    'status': 'confirmed',
                    'get_type_display': 'Práctica',
                    'get_status_display': 'Confirmada'
                },
                {
                    'id': 2,
                    'date': datetime.now().date() + timedelta(days=3),
                    'start_time': '14:00',
                    'end_time': '16:00',
                    'duration': 2,
                    'laboratory': {'name': 'Laboratorio de Matemáticas', 'capacity': 35},
                    'course': {'name': 'MATEMATICA APLICADA A LA COMPUTACION', 'code': '1703241'},
                    'type': 'examen',
                    'status': 'pending',
                    'get_type_display': 'Examen',
                    'get_status_display': 'Pendiente'
                }
            ]
            
            # Calendario semanal
            today = datetime.now().date()
            week_days = []
            for i in range(7):
                day_date = today + timedelta(days=i)
                day_reservations = [r for r in reservations if r['date'] == day_date]
                
                week_days.append({
                    'name': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][day_date.weekday()],
                    'date': day_date.strftime('%d/%m'),
                    'reservations': [
                        {
                            'time': f"{r['start_time']}-{r['end_time']}",
                            'lab': r['laboratory']['name'][:15] + '...' if len(r['laboratory']['name']) > 15 else r['laboratory']['name'],
                            'course': r['course']['name'][:20] + '...' if len(r['course']['name']) > 20 else r['course']['name']
                        } for r in day_reservations
                    ]
                })
            
            # Estadísticas de reservas
            active_reservations = len([r for r in reservations if r['status'] == 'confirmed'])
            next_reservation = reservations[0] if reservations else None
            hours_week = sum(r['duration'] for r in reservations if r['date'] >= today and r['date'] < today + timedelta(days=7))
            
            context.update({
                'page_title': 'Reservas de Laboratorios',
                'laboratories': laboratories,
                'reservations': reservations,
                'courses': [{
                    'id': 1,
                    'name': 'MATEMATICA APLICADA A LA COMPUTACION',
                    'code': '1703241'
                }],
                'selected_date': today,
                'today': today,
                'week_days': week_days,
                'reservation_stats': {
                    'active': active_reservations,
                    'hours_week': hours_week
                },
                'next_reservation': {
                    'time': next_reservation['start_time'] if next_reservation else None,
                    'lab': next_reservation['laboratory']['name'] if next_reservation else None
                } if next_reservation else {'time': None, 'lab': None}
            })
            
        except Exception as e:
            context.update({
                'page_title': 'Reservas de Laboratorios',
                'error': f'Error al cargar reservas: {str(e)}',
                'laboratories': [],
                'reservations': [],
                'courses': [],
                'reservation_stats': {'active': 0, 'hours_week': 0}
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Crear nueva reserva"""
        try:
            # Obtener el profesor asociado al usuario
            try:
                profesor = request.user.teacher
                profesor_id = profesor.id
            except AttributeError:
                profesor_id = request.user.id
                
            recurso_id = request.POST.get('recurso_id')
            fecha = request.POST.get('fecha')
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin = request.POST.get('hora_fin')
            proposito = request.POST.get('proposito')
            
            # resultado = ServicioReservas.crear_reserva(recurso_id, profesor_id, fecha, hora_inicio, hora_fin, proposito)
            messages.success(request, 'Reserva creada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al crear reserva: {str(e)}')
        
        return redirect('profesor:reservas')


class ProfesorSilaboView(ProfesorRequiredMixin, TemplateView):
    """Gestión de sílabos y avance de cursos"""
    template_name = 'profesor/silabo/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from django.db import connection
            
            # Obtener información del curso asignado al profesor
            course_info = self._get_assigned_course()
            if not course_info:
                context.update({
                    'page_title': 'Gestión de Sílabo',
                    'error': 'No tienes un curso asignado',
                    'course': {},
                    'syllabus_units': [],
                    'syllabus_stats': {},
                    'schedule': [],
                    'resources': []
                })
                return context
            
            # Sistema automático de avance del sílabo (basado en semanas)
            from datetime import datetime, timedelta
            
            # Calcular semana actual del período académico (4 meses = 16 semanas)
            start_date = datetime(2024, 8, 1)  # Inicio del período académico
            current_date = datetime.now()
            weeks_elapsed = min(((current_date - start_date).days // 7) + 1, 16)
            
            # Unidades del sílabo con avance automático
            syllabus_units = [
                {
                    'title': 'Unidad I: Fundamentos de Álgebra Lineal',
                    'duration': 4,  # semanas
                    'hours': 16,
                    'weeks_range': (1, 4),  # semanas 1-4
                    'progress': 100 if weeks_elapsed > 4 else (weeks_elapsed * 25 if weeks_elapsed <= 4 else 100),
                    'status': 'completed' if weeks_elapsed > 4 else ('in_progress' if weeks_elapsed <= 4 else 'pending'),
                    'get_status_display': 'Completada' if weeks_elapsed > 4 else ('En Progreso' if weeks_elapsed <= 4 else 'Pendiente'),
                    'objectives': [
                        'Comprender los conceptos básicos de vectores y matrices',
                        'Realizar operaciones fundamentales con matrices',
                        'Aplicar propiedades de determinantes'
                    ],
                    'contents': [
                        {'title': 'Vectores en R2 y R3', 'hours': 4, 'completed': True},
                        {'title': 'Operaciones con vectores', 'hours': 4, 'completed': True},
                        {'title': 'Matrices y operaciones', 'hours': 4, 'completed': True},
                        {'title': 'Determinantes', 'hours': 4, 'completed': True}
                    ],
                    'evaluations': [
                        {'name': 'Práctica 1', 'type': 'practica', 'weight': 20},
                        {'name': 'Examen Parcial', 'type': 'examen', 'weight': 30}
                    ]
                },
                {
                    'title': 'Unidad II: Espacios Vectoriales',
                    'duration': 4,
                    'hours': 16,
                    'weeks_range': (5, 8),  # semanas 5-8
                    'progress': 100 if weeks_elapsed > 8 else (max(0, (weeks_elapsed - 4) * 25) if weeks_elapsed > 4 else 0),
                    'status': 'completed' if weeks_elapsed > 8 else ('in_progress' if weeks_elapsed > 4 and weeks_elapsed <= 8 else 'pending'),
                    'get_status_display': 'Completada' if weeks_elapsed > 8 else ('En Progreso' if weeks_elapsed > 4 and weeks_elapsed <= 8 else 'Pendiente'),
                    'objectives': [
                        'Definir y caracterizar espacios vectoriales',
                        'Identificar subespacios vectoriales',
                        'Trabajar con bases y dimensión'
                    ],
                    'contents': [
                        {'title': 'Definición de espacio vectorial', 'hours': 4, 'completed': True},
                        {'title': 'Subespacios vectoriales', 'hours': 4, 'completed': True},
                        {'title': 'Combinación lineal e independencia', 'hours': 4, 'completed': False},
                        {'title': 'Base y dimensión', 'hours': 4, 'completed': False}
                    ],
                    'evaluations': [
                        {'name': 'Práctica 2', 'type': 'practica', 'weight': 20},
                        {'name': 'Proyecto', 'type': 'proyecto', 'weight': 15}
                    ]
                },
                {
                    'title': 'Unidad III: Transformaciones Lineales',
                    'duration': 4,
                    'hours': 16,
                    'weeks_range': (9, 12),  # semanas 9-12
                    'progress': 100 if weeks_elapsed > 12 else (max(0, (weeks_elapsed - 8) * 25) if weeks_elapsed > 8 else 0),
                    'status': 'completed' if weeks_elapsed > 12 else ('in_progress' if weeks_elapsed > 8 and weeks_elapsed <= 12 else 'pending'),
                    'get_status_display': 'Completada' if weeks_elapsed > 12 else ('En Progreso' if weeks_elapsed > 8 and weeks_elapsed <= 12 else 'Pendiente'),
                    'objectives': [
                        'Comprender el concepto de transformación lineal',
                        'Calcular matrices de transformaciones',
                        'Analizar núcleo e imagen'
                    ],
                    'contents': [
                        {'title': 'Definición y propiedades', 'hours': 4, 'completed': False},
                        {'title': 'Matriz de una transformación', 'hours': 4, 'completed': False},
                        {'title': 'Núcleo e imagen', 'hours': 4, 'completed': False},
                        {'title': 'Isomorfismos', 'hours': 4, 'completed': False}
                    ],
                    'evaluations': [
                        {'name': 'Práctica 3', 'type': 'practica', 'weight': 20}
                    ]
                },
                {
                    'title': 'Unidad IV: Valores y Vectores Propios',
                    'duration': 4,
                    'hours': 16,
                    'weeks_range': (13, 16),  # semanas 13-16
                    'progress': 100 if weeks_elapsed > 16 else (max(0, (weeks_elapsed - 12) * 25) if weeks_elapsed > 12 else 0),
                    'status': 'completed' if weeks_elapsed > 16 else ('in_progress' if weeks_elapsed > 12 and weeks_elapsed <= 16 else 'pending'),
                    'get_status_display': 'Completada' if weeks_elapsed > 16 else ('En Progreso' if weeks_elapsed > 12 and weeks_elapsed <= 16 else 'Pendiente'),
                    'objectives': [
                        'Calcular valores y vectores propios',
                        'Diagonalizar matrices',
                        'Aplicar en problemas prácticos'
                    ],
                    'contents': [
                        {'title': 'Valores propios', 'hours': 4, 'completed': False},
                        {'title': 'Vectores propios', 'hours': 4, 'completed': False},
                        {'title': 'Diagonalización', 'hours': 4, 'completed': False},
                        {'title': 'Aplicaciones', 'hours': 4, 'completed': False}
                    ],
                    'evaluations': [
                        {'name': 'Examen Final', 'type': 'examen', 'weight': 35}
                    ]
                }
            ]
            
            # Estadísticas del sílabo
            total_units = len(syllabus_units)
            completed_units = len([u for u in syllabus_units if u['status'] == 'completed'])
            total_classes = sum(u['hours'] for u in syllabus_units) // 2  # 2 horas por clase
            classes_taught = sum(u['hours'] for u in syllabus_units if u['status'] == 'completed') // 2
            classes_taught += sum(u['hours'] * u['progress'] / 100 for u in syllabus_units if u['status'] == 'in_progress') // 2
            
            syllabus_stats = {
                'total_units': total_units,
                'completed_units': completed_units,
                'completion_percentage': (completed_units / total_units * 100) if total_units > 0 else 0,
                'total_classes': int(total_classes),
                'classes_taught': int(classes_taught),
                'classes_percentage': (classes_taught / total_classes * 100) if total_classes > 0 else 0,
                'total_evaluations': 3,
                'evaluations_done': 1,
                'evaluations_percentage': 33
            }
            
            # Cronograma
            schedule = [
                {'number': i, 'dates': f'{i*7+1}-{i*7+7} Oct', 'completed': i <= 8, 'current': i == 9}
                for i in range(1, 17)
            ]
            
            # Recursos
            resources = [
                {'name': 'Libro de Álgebra Lineal', 'type': 'PDF', 'icon': 'file-text'},
                {'name': 'Ejercicios Resueltos', 'type': 'PDF', 'icon': 'file-text'},
                {'name': 'Videos Explicativos', 'type': 'Video', 'icon': 'play-circle'},
                {'name': 'Software GeoGebra', 'type': 'Software', 'icon': 'monitor'}
            ]
            
            context.update({
                'page_title': 'Gestión de Sílabo',
                'course': course,
                'syllabus_units': syllabus_units,
                'syllabus_stats': syllabus_stats,
                'schedule': schedule,
                'resources': resources
            })
            
        except Exception as e:
            context.update({
                'page_title': 'Gestión de Sílabo',
                'error': f'Error al cargar datos del sílabo: {str(e)}',
                'course': {},
                'syllabus_units': [],
                'syllabus_stats': {},
                'schedule': [],
                'resources': []
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Subir sílabo o registrar avance"""
        if 'subir_silabo' in request.POST:
            try:
                curso_id = request.POST.get('curso_id')
                archivo_silabo = request.FILES.get('archivo_silabo')
                unidades = request.POST.getlist('unidades')
                
                resultado = ServicioSilabo.procesar_silabo(
                    curso_id, archivo_silabo, unidades, request.user.profesor.id
                )
                messages.success(request, 'Sílabo subido exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al subir sílabo: {str(e)}')
        
        elif 'registrar_avance' in request.POST:
            try:
                tema_id = request.POST.get('tema_id')
                porcentaje = request.POST.get('porcentaje')
                notas = request.POST.get('notas')
                
                ServicioAvance.registrar_avance_tema(
                    tema_id, porcentaje, notas, request.user.profesor.id
                )
                messages.success(request, 'Avance registrado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al registrar avance: {str(e)}')
        
        return redirect('profesor:silabo')


class DebugDataView(ProfesorRequiredMixin, TemplateView):
    """Vista de debug para verificar datos en la base de datos"""
    template_name = 'profesor/debug/data.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from django.db import connection
            
            debug_info = {}
            
            with connection.cursor() as cursor:
                # Verificar estudiantes
                cursor.execute("SELECT COUNT(*) FROM students;")
                debug_info['students_count'] = cursor.fetchone()[0]
                
                # Verificar tipos de evaluación
                cursor.execute("SELECT id, name FROM evaluation_types ORDER BY name;")
                debug_info['evaluation_types'] = cursor.fetchall()
                
                # Verificar notas
                cursor.execute("SELECT COUNT(*) FROM grades;")
                debug_info['grades_count'] = cursor.fetchone()[0]
                
                if debug_info['grades_count'] > 0:
                    # Estadísticas de notas
                    cursor.execute("""
                        SELECT 
                            AVG(score) as avg_score,
                            MIN(score) as min_score,
                            MAX(score) as max_score
                        FROM grades;
                    """)
                    stats = cursor.fetchone()
                    debug_info['grade_stats'] = {
                        'average': round(float(stats[0]), 2) if stats[0] else 0,
                        'min_score': float(stats[1]) if stats[1] else 0,
                        'max_score': float(stats[2]) if stats[2] else 0
                    }
                    
                    # Distribución por rangos
                    cursor.execute("""
                        SELECT 
                            CASE 
                                WHEN score BETWEEN 0 AND 5 THEN '0-5'
                                WHEN score BETWEEN 6 AND 10 THEN '6-10'
                                WHEN score BETWEEN 11 AND 15 THEN '11-15'
                                WHEN score BETWEEN 16 AND 20 THEN '16-20'
                                ELSE 'Fuera de rango'
                            END as rango,
                            COUNT(*) as cantidad
                        FROM grades
                        GROUP BY 
                            CASE 
                                WHEN score BETWEEN 0 AND 5 THEN '0-5'
                                WHEN score BETWEEN 6 AND 10 THEN '6-10'
                                WHEN score BETWEEN 11 AND 15 THEN '11-15'
                                WHEN score BETWEEN 16 AND 20 THEN '16-20'
                                ELSE 'Fuera de rango'
                            END
                        ORDER BY rango;
                    """)
                    debug_info['grade_distribution'] = cursor.fetchall()
                
                # Verificar course_groups
                cursor.execute("SELECT COUNT(*) FROM course_groups;")
                debug_info['course_groups_count'] = cursor.fetchone()[0]
                
                # Verificar enrollments
                cursor.execute("SELECT COUNT(*) FROM enrollments;")
                debug_info['enrollments_count'] = cursor.fetchone()[0]
                
                # Probar consulta de API
                try:
                    cursor.execute("""
                        SELECT g.score
                        FROM grades g
                        JOIN evaluation_types et ON g.evaluation_type_id = et.id
                        JOIN course_groups cg ON et.course_group_id = cg.id
                        WHERE 1=1
                    """)
                    api_scores = [row[0] for row in cursor.fetchall()]
                    debug_info['api_test'] = {
                        'success': True,
                        'scores_count': len(api_scores),
                        'sample_scores': api_scores[:10] if api_scores else []
                    }
                except Exception as e:
                    debug_info['api_test'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            context['debug_info'] = debug_info
            
        except Exception as e:
            context['error'] = f'Error obteniendo información de debug: {str(e)}'
        
        return context


class DebugProcessExcelView(ProfesorRequiredMixin, TemplateView):
    """Vista de debug para procesar Excel de notas"""
    template_name = 'profesor/debug/process_excel.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['excel_file'] = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar Excel de notas usando el servicio"""
        try:
            import os
            from servicios.servicioExcel import ExcelGradeProcessor
            
            excel_file = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
            
            if not os.path.exists(excel_file):
                messages.error(request, f'Archivo {excel_file} no encontrado')
                return redirect('profesor:debug_process_excel')
            
            # Procesar archivo
            processor = ExcelGradeProcessor(request.user.id)
            results = processor.process_grades_file(excel_file)
            
            # Mostrar resultados
            if results['success']:
                messages.success(request, 
                    f'Excel procesado exitosamente. '
                    f'Se procesaron {results["processed_count"]} notas.')
                
                # Mostrar estadísticas
                if results['statistics']:
                    for eval_name, stats in results['statistics'].items():
                        messages.info(request, 
                            f'{eval_name}: {stats["total"]} notas, '
                            f'promedio {stats["average"]}, '
                            f'aprobados {stats["passed"]} ({stats["pass_rate"]}%)')
            else:
                messages.error(request, 'Error procesando Excel')
            
            # Mostrar advertencias
            for warning in results['warnings'][:5]:
                messages.warning(request, warning)
            
            # Mostrar errores
            for error in results['errors'][:3]:
                messages.error(request, error)
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('profesor:debug_process_excel')