#!/usr/bin/env python3
"""
Script para verificar que la URL de estadísticas funcione correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def verificar_url_estadisticas():
    """Verificar que la URL de estadísticas tenga datos para mostrar"""
    print("=== VERIFICACIÓN URL DE ESTADÍSTICAS ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar si hay course_groups disponibles
            cursor.execute("""
                SELECT cg.id, c.name, cg.group_code
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LIMIT 5;
            """)
            
            course_groups = cursor.fetchall()
            print(f"Course groups disponibles: {len(course_groups)}")
            
            if not course_groups:
                print("❌ No hay course_groups disponibles")
                return
            
            for cg in course_groups:
                cg_id, name, group_code = cg
                print(f"  - {cg_id}: {name} - {group_code}")
            
            # 2. Verificar si hay notas en phase_grades
            cursor.execute("SELECT COUNT(*) FROM phase_grades;")
            total_notas = cursor.fetchone()[0]
            print(f"\nTotal notas en phase_grades: {total_notas}")
            
            if total_notas == 0:
                print("⚠️  No hay notas en phase_grades")
                
                # Crear algunas notas de prueba
                print("\n🔧 Creando notas de prueba...")
                
                # Usar el primer course_group
                test_cg_id = course_groups[0][0]
                
                # Buscar estudiantes
                cursor.execute("SELECT id FROM students LIMIT 3;")
                students = cursor.fetchall()
                
                if students:
                    import random
                    from datetime import datetime
                    
                    for student_row in students:
                        student_id = student_row[0]
                        
                        # Generar notas aleatorias
                        partial_grade = round(random.uniform(10, 18), 1)
                        continuous_grade = round(random.uniform(12, 20), 1)
                        final_grade = round((partial_grade * 0.6) + (continuous_grade * 0.4), 1)
                        
                        cursor.execute("""
                            INSERT INTO phase_grades (
                                student_id, course_group_id, phase, 
                                partial_grade, continuous_grade, final_phase_grade,
                                uploaded_at, uploaded_by_id
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (student_id, course_group_id, phase) 
                            DO UPDATE SET 
                                partial_grade = EXCLUDED.partial_grade,
                                continuous_grade = EXCLUDED.continuous_grade,
                                final_phase_grade = EXCLUDED.final_phase_grade;
                        """, [
                            student_id, test_cg_id, 'primera',
                            partial_grade, continuous_grade, final_grade,
                            datetime.now(), '00000000-0000-0000-0000-000000000000'
                        ])
                    
                    print(f"✅ Creadas {len(students)} notas de prueba")
                else:
                    print("❌ No hay estudiantes disponibles")
            
            # 3. Mostrar course_groups con notas
            cursor.execute("""
                SELECT DISTINCT cg.id, c.name, cg.group_code, COUNT(pg.id) as notas_count
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LEFT JOIN phase_grades pg ON cg.id = pg.course_group_id
                GROUP BY cg.id, c.name, cg.group_code
                ORDER BY notas_count DESC;
            """)
            
            groups_with_grades = cursor.fetchall()
            
            print(f"\n📊 COURSE GROUPS CON NOTAS:")
            for group in groups_with_grades:
                cg_id, name, group_code, notas_count = group
                print(f"  - {name} - {group_code}: {notas_count} notas")
                if notas_count > 0:
                    print(f"    URL: http://127.0.0.1:8000/profesor/notas/estadisticas/?course_id={cg_id}&phase=primera")
            
            # 4. Generar URL de prueba
            if groups_with_grades and groups_with_grades[0][3] > 0:
                test_cg_id = groups_with_grades[0][0]
                test_name = groups_with_grades[0][1]
                test_group = groups_with_grades[0][2]
                
                print(f"\n🎯 URL DE PRUEBA RECOMENDADA:")
                print(f"http://127.0.0.1:8000/profesor/notas/estadisticas/?course_id={test_cg_id}&phase=primera")
                print(f"Curso: {test_name} - {test_group}")
                
                # Verificar que los datos se pueden obtener
                from servicios.servicioEstadisticasNotas import servicio_generador_graficos
                
                stats_result = servicio_generador_graficos.generate_statistics_summary_data(
                    str(test_cg_id), 'primera'
                )
                
                if stats_result['success']:
                    teacher_summary = stats_result['teacher_summary']
                    print(f"\n✅ DATOS DISPONIBLES:")
                    print(f"  - Promedio: {teacher_summary['grade_metrics']['average_grade']}")
                    print(f"  - Estudiantes evaluados: {teacher_summary['key_metrics']['graded_students']}")
                    print(f"  - Tasa de aprobación: {teacher_summary['grade_metrics']['approval_rate']}%")
                else:
                    print(f"❌ Error obteniendo estadísticas: {stats_result.get('error')}")
            
            print(f"\n📝 INSTRUCCIONES:")
            print(f"1. Ve a: http://127.0.0.1:8000/profesor/notas/estadisticas/")
            print(f"2. Selecciona un curso de la lista desplegable")
            print(f"3. Selecciona 'Primera Fase'")
            print(f"4. Los datos deberían aparecer automáticamente")
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_url_estadisticas()