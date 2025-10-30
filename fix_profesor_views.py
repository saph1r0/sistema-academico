#!/usr/bin/env python3
"""
Script para arreglar la vista de notas del profesor
"""

# Contenido limpio para la vista de notas
notas_view_content = '''
class ProfesorNotasView(ProfesorRequiredMixin, TemplateView):
    """Gestión de notas mediante plantillas Excel"""
    template_name = 'profesor/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            from django.db import connection
            
            # Obtener notas reales de la base de datos
            with connection.cursor() as cursor:
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
                    LEFT JOIN enrollments e ON s.id = e.student_id
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
                
                context.update({
                    'page_title': 'Gestión de Notas',
                    'courses': [{
                        'id': 1,
                        'name': 'MATEMATICA APLICADA A LA COMPUTACION',
                        'code': '1703241'
                    }],
                    'selected_course': 1,
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
        try:
            if 'archivo_notas' in request.FILES:
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
        
        return redirect('profesor:notas')
'''

print("Vista de notas limpia creada")
print("Contenido:")
print(notas_view_content)