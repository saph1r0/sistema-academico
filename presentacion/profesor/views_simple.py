"""
Vistas simplificadas para el módulo de profesores
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.db import connection
from .mixins import ProfesorRequiredMixin


class ProfesorNotasViewSimple(ProfesorRequiredMixin, TemplateView):
    """Vista simplificada de gestión de notas"""
    template_name = 'profesor/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Datos básicos para la página
            context.update({
                'page_title': 'Gestión de Notas',
                'courses': [{
                    'id': 1,
                    'name': 'MATEMATICA APLICADA A LA COMPUTACION',
                    'code': '1703241'
                }],
                'selected_course': 1,
                'students': [],
                'grade_stats': {
                    'average': 0,
                    'approved': 0,
                    'total': 0,
                    'at_risk': 0,
                    'parcial1_count': 0,
                    'parcial2_count': 0,
                    'parcial3_count': 0,
                    'parcial1_avg': 0,
                    'parcial2_avg': 0,
                    'parcial3_avg': 0
                },
                'best_student': {'name': 'N/A', 'grade': 0},
                'worst_student': {'name': 'N/A', 'grade': 0}
            })
            
            # Obtener datos reales de estudiantes y notas
            with connection.cursor() as cursor:
                # Obtener estudiantes con sus notas
                cursor.execute("""
                    SELECT 
                        s.id,
                        s.student_code,
                        u.first_name,
                        u.last_name,
                        et.name as evaluation_type,
                        g.score
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    LEFT JOIN grades g ON s.id = g.student_id
                    LEFT JOIN evaluation_types et ON g.evaluation_type_id = et.id
                    ORDER BY s.student_code, et.name;
                """)
                
                rows = cursor.fetchall()
                
                # Organizar datos por estudiante
                students_dict = {}
                for row in rows:
                    student_id, student_code, first_name, last_name, eval_type, score = row
                    
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
                all_averages = []
                best_student = {'name': 'N/A', 'grade': 0}
                worst_student = {'name': 'N/A', 'grade': 20}
                
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
                        all_averages.append(promedio)
                        
                        # Determinar mejor y peor estudiante
                        if promedio > best_student['grade']:
                            best_student = {
                                'name': student_data['full_name'],
                                'grade': promedio
                            }
                        if promedio < worst_student['grade']:
                            worst_student = {
                                'name': student_data['full_name'],
                                'grade': promedio
                            }
                    else:
                        grades['promedio'] = None
                    
                    students_with_grades.append(student_data)
                
                # Ordenar por código de estudiante
                students_with_grades.sort(key=lambda x: x['student_code'])
                
                # Calcular estadísticas
                promedios_validos = [avg for avg in all_averages if avg is not None]
                aprobados = len([p for p in promedios_validos if p >= 10.5])
                en_riesgo = len([p for p in promedios_validos if p < 10.5])
                
                # Estadísticas por evaluación
                parcial1_notas = [s['grades']['parcial1'] for s in students_with_grades if s['grades']['parcial1'] is not None]
                parcial2_notas = [s['grades']['parcial2'] for s in students_with_grades if s['grades']['parcial2'] is not None]
                parcial3_notas = [s['grades']['parcial3'] for s in students_with_grades if s['grades']['parcial3'] is not None]
                
                # Actualizar contexto con datos reales
                context.update({
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
                    },
                    'best_student': best_student,
                    'worst_student': worst_student,
                    'debug_info': {
                        'students_count': len(students_with_grades),
                        'grades_count': len(parcial1_notas) + len(parcial2_notas) + len(parcial3_notas)
                    }
                })
            
        except Exception as e:
            context['error'] = f'Error al cargar datos: {str(e)}'
        
        return context

    def post(self, request, *args, **kwargs):
        """Procesar subida de archivos Excel y guardado de notas manuales"""
        try:
            action = request.POST.get('action', '')
            
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
                messages.info(request, 'No se especificó una acción válida.')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('profesor:notas')


class DebugDataViewSimple(ProfesorRequiredMixin, TemplateView):
    """Vista simple para debug de datos"""
    template_name = 'profesor/debug/data.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
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
                
                # Test de API real
                try:
                    cursor.execute("""
                        SELECT g.score
                        FROM grades g
                        JOIN evaluation_types et ON g.evaluation_type_id = et.id
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
                        'error': str(e),
                        'scores_count': 0
                    }
            
            context['debug_info'] = debug_info
            
        except Exception as e:
            context['error'] = f'Error: {str(e)}'
        
        return context


class DebugProcessExcelViewSimple(ProfesorRequiredMixin, TemplateView):
    """Vista simple para procesar Excel"""
    template_name = 'profesor/debug/process_excel.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['excel_file'] = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar Excel manualmente"""
        try:
            messages.info(request, 'Procesamiento de Excel en desarrollo.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('profesor:debug_process_excel')