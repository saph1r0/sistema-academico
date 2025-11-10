#!/usr/bin/env python3
"""
Script para probar que las estadísticas de notas funcionen correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from servicios.servicioEstadisticasNotas import servicio_estadisticas_notas, servicio_generador_graficos

def test_estadisticas_notas():
    """Probar el servicio de estadísticas de notas"""
    print("=== PROBANDO ESTADÍSTICAS DE NOTAS ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar si hay notas en el sistema
            cursor.execute("SELECT COUNT(*) FROM phase_grades;")
            total_notas = cursor.fetchone()[0]
            print(f"Total notas en sistema: {total_notas}")
            
            if total_notas == 0:
                print("❌ No hay notas en el sistema para probar")
                
                # Crear algunas notas de prueba
                print("\n🔧 Creando notas de prueba...")
                
                # Buscar un course_group
                cursor.execute("""
                    SELECT cg.id, c.name, cg.group_code
                    FROM course_groups cg
                    JOIN courses c ON cg.course_id = c.id
                    LIMIT 1;
                """)
                
                cg_result = cursor.fetchone()
                if not cg_result:
                    print("❌ No hay course_groups disponibles")
                    return
                
                course_group_id, course_name, group_code = cg_result
                print(f"Usando course_group: {course_name} - {group_code}")
                
                # Buscar estudiantes
                cursor.execute("SELECT id FROM students LIMIT 5;")
                students = cursor.fetchall()
                
                if not students:
                    print("❌ No hay estudiantes disponibles")
                    return
                
                # Crear notas de prueba
                import random
                from datetime import datetime
                
                for student_row in students:
                    student_id = student_row[0]
                    
                    # Generar notas aleatorias
                    partial_grade = round(random.uniform(8, 18), 1)
                    continuous_grade = round(random.uniform(10, 20), 1)
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
                        student_id, course_group_id, 'primera',
                        partial_grade, continuous_grade, final_grade,
                        datetime.now(), '00000000-0000-0000-0000-000000000000'  # UUID dummy
                    ])
                
                print(f"✅ Creadas {len(students)} notas de prueba")
            
            # 2. Buscar un course_group con notas
            cursor.execute("""
                SELECT DISTINCT cg.id, c.name, cg.group_code
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                JOIN phase_grades pg ON cg.id = pg.course_group_id
                LIMIT 1;
            """)
            
            test_course = cursor.fetchone()
            if not test_course:
                print("❌ No se encontró course_group con notas")
                return
            
            course_group_id, course_name, group_code = test_course
            print(f"\n📊 Probando estadísticas para: {course_name} - {group_code}")
            print(f"Course Group ID: {course_group_id}")
            
            # 3. Probar estadísticas básicas
            print(f"\n1. ESTADÍSTICAS BÁSICAS:")
            basic_stats = servicio_estadisticas_notas.calculate_basic_statistics(
                str(course_group_id), 'primera'
            )
            
            if basic_stats['success']:
                stats = basic_stats['statistics']
                print(f"   ✅ Promedio: {stats['average_grade']}")
                print(f"   ✅ Nota máxima: {stats['max_grade']}")
                print(f"   ✅ Nota mínima: {stats['min_grade']}")
                print(f"   ✅ Estudiantes evaluados: {stats['graded_students']}")
                print(f"   ✅ Total estudiantes: {stats['total_students']}")
            else:
                print(f"   ❌ Error: {basic_stats['error']}")
                return
            
            # 4. Probar distribución de notas
            print(f"\n2. DISTRIBUCIÓN DE NOTAS:")
            distribution = servicio_estadisticas_notas.calculate_grade_distribution(
                str(course_group_id), 'primera'
            )
            
            if distribution['success']:
                dist = distribution['distribution']
                print(f"   ✅ 0-5 (Deficiente): {dist['0-5']['count']} estudiantes ({dist['0-5']['percentage']}%)")
                print(f"   ✅ 6-10 (Regular): {dist['6-10']['count']} estudiantes ({dist['6-10']['percentage']}%)")
                print(f"   ✅ 11-15 (Bueno): {dist['11-15']['count']} estudiantes ({dist['11-15']['percentage']}%)")
                print(f"   ✅ 16-20 (Excelente): {dist['16-20']['count']} estudiantes ({dist['16-20']['percentage']}%)")
            else:
                print(f"   ❌ Error: {distribution['error']}")
            
            # 5. Probar generación de datos para gráficos
            print(f"\n3. DATOS PARA GRÁFICOS:")
            chart_data = servicio_generador_graficos.generate_statistics_summary_data(
                str(course_group_id), 'primera'
            )
            
            if chart_data['success']:
                teacher_summary = chart_data['teacher_summary']
                print(f"   ✅ Datos del profesor generados correctamente")
                print(f"   - Promedio: {teacher_summary['grade_metrics']['average_grade']}")
                print(f"   - Tasa de aprobación: {teacher_summary['grade_metrics']['approval_rate']}%")
                print(f"   - Estudiantes evaluados: {teacher_summary['key_metrics']['graded_students']}")
                
                # Mostrar estructura de datos para el template
                print(f"\n   📋 ESTRUCTURA DE DATOS PARA TEMPLATE:")
                print(f"   statistics_data.grade_metrics.average_grade = {teacher_summary['grade_metrics']['average_grade']}")
                print(f"   statistics_data.grade_metrics.max_grade = {teacher_summary['grade_metrics']['max_grade']}")
                print(f"   statistics_data.grade_metrics.min_grade = {teacher_summary['grade_metrics']['min_grade']}")
                print(f"   statistics_data.grade_metrics.approval_rate = {teacher_summary['grade_metrics']['approval_rate']}")
                print(f"   statistics_data.distribution_summary.poor.count = {teacher_summary['distribution_summary']['poor']['count']}")
                print(f"   statistics_data.distribution_summary.regular.count = {teacher_summary['distribution_summary']['regular']['count']}")
                print(f"   statistics_data.distribution_summary.good.count = {teacher_summary['distribution_summary']['good']['count']}")
                print(f"   statistics_data.distribution_summary.excellent.count = {teacher_summary['distribution_summary']['excellent']['count']}")
                
            else:
                print(f"   ❌ Error: {chart_data['error']}")
            
            # 6. Probar datos combinados para gráficos
            print(f"\n4. DATOS COMBINADOS PARA GRÁFICOS:")
            combined_data = servicio_generador_graficos.generate_combined_chart_data(
                str(course_group_id), 'primera'
            )
            
            if combined_data['success']:
                print(f"   ✅ Datos combinados generados correctamente")
                print(f"   - Gráfico de barras: Disponible")
                print(f"   - Gráfico de torta: Disponible")
                print(f"   - Resumen estadístico: Disponible")
            else:
                print(f"   ❌ Error: {combined_data['error']}")
            
            print(f"\n✅ TODAS LAS PRUEBAS COMPLETADAS")
            print(f"🎯 El template debería mostrar los datos correctamente ahora")
            
    except Exception as e:
        print(f"❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_estadisticas_notas()