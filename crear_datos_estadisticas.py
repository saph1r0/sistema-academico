#!/usr/bin/env python3
"""
Script para crear datos de prueba para las estadísticas
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
import random
from datetime import datetime

def crear_datos_estadisticas():
    """Crear datos de prueba para las estadísticas"""
    print("=== CREANDO DATOS PARA ESTADÍSTICAS ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Buscar un course_group
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
            print(f"ID: {course_group_id}")
            
            # 2. Buscar estudiantes
            cursor.execute("SELECT id FROM students LIMIT 10;")
            students = cursor.fetchall()
            
            if not students:
                print("❌ No hay estudiantes disponibles")
                return
            
            print(f"Estudiantes disponibles: {len(students)}")
            
            # 3. Crear notas de prueba variadas
            created_count = 0
            
            for i, student_row in enumerate(students):
                student_id = student_row[0]
                
                # Crear diferentes tipos de notas para tener buena distribución
                if i < 2:  # Notas excelentes
                    partial_grade = round(random.uniform(16, 20), 1)
                    continuous_grade = round(random.uniform(17, 20), 1)
                elif i < 5:  # Notas buenas
                    partial_grade = round(random.uniform(11, 15), 1)
                    continuous_grade = round(random.uniform(12, 16), 1)
                elif i < 8:  # Notas regulares
                    partial_grade = round(random.uniform(6, 10), 1)
                    continuous_grade = round(random.uniform(7, 11), 1)
                else:  # Notas deficientes
                    partial_grade = round(random.uniform(0, 5), 1)
                    continuous_grade = round(random.uniform(1, 6), 1)
                
                final_grade = round((partial_grade * 0.6) + (continuous_grade * 0.4), 1)
                
                try:
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
                        datetime.now(), '00000000-0000-0000-0000-000000000000'
                    ])
                    created_count += 1
                    print(f"  ✅ Nota creada: Parcial {partial_grade}, Continua {continuous_grade}, Final {final_grade}")
                except Exception as e:
                    print(f"  ❌ Error creando nota: {str(e)}")
            
            print(f"\n✅ CREADAS {created_count} NOTAS DE PRUEBA")
            
            # 4. Verificar las estadísticas
            cursor.execute("""
                SELECT 
                    AVG(final_phase_grade) as promedio,
                    MIN(final_phase_grade) as minima,
                    MAX(final_phase_grade) as maxima,
                    COUNT(*) as total
                FROM phase_grades 
                WHERE course_group_id = %s AND phase = 'primera';
            """, [course_group_id])
            
            stats = cursor.fetchone()
            if stats:
                promedio, minima, maxima, total = stats
                print(f"\n📊 ESTADÍSTICAS GENERADAS:")
                print(f"  - Promedio: {promedio:.1f}")
                print(f"  - Nota mínima: {minima}")
                print(f"  - Nota máxima: {maxima}")
                print(f"  - Total notas: {total}")
            
            # 5. Mostrar URL para acceder
            print(f"\n🎯 ACCEDE A LAS ESTADÍSTICAS EN:")
            print(f"http://127.0.0.1:8000/profesor/notas/estadisticas/?course_id={course_group_id}&phase=primera")
            
            print(f"\n📝 PASOS:")
            print(f"1. Ve a: http://127.0.0.1:8000/profesor/notas/estadisticas/")
            print(f"2. Selecciona el curso: {course_name} - {group_code}")
            print(f"3. Selecciona 'Primera Fase'")
            print(f"4. ¡Los datos deberían aparecer!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    crear_datos_estadisticas()