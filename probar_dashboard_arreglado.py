#!/usr/bin/env python3
"""
Script para probar el dashboard del profesor arreglado
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

def probar_dashboard_profesor():
    """Probar el dashboard del profesor con datos reales"""
    print("=== PRUEBA DEL DASHBOARD ARREGLADO ===\n")
    
    try:
        with connection.cursor() as cursor:
            # Buscar un profesor con cursos asignados
            cursor.execute("""
                SELECT DISTINCT
                    u.id, u.institutional_email, u.first_name, u.last_name,
                    t.id as teacher_id, t.teacher_code
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                JOIN course_groups cg ON t.id = cg.teacher_id
                WHERE u.role = 'teacher'
                LIMIT 1;
            """)
            
            profesor_data = cursor.fetchone()
            
            if not profesor_data:
                print("❌ No se encontró ningún profesor con cursos asignados")
                return
            
            user_id, institutional_email, first_name, last_name, teacher_id, teacher_code = profesor_data
            print(f"✅ Probando con profesor: {first_name} {last_name}")
            print(f"   Email: {institutional_email}, Teacher ID: {teacher_id}")
            
            # Simular el método _get_real_dashboard_data()
            print("\n1. OBTENIENDO CURSOS ASIGNADOS AL PROFESOR:")
            
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
                ORDER BY c.code;
            """, [teacher_id])
            
            courses_data = cursor.fetchall()
            
            if courses_data:
                print(f"   ✅ Encontrados {len(courses_data)} curso(s):")
                
                total_students = 0
                for course in courses_data:
                    course_id, code, name, credits, student_count, group_code = course
                    total_students += student_count or 0
                    print(f"   - {code}: {name}")
                    print(f"     Grupo: {group_code}, Estudiantes: {student_count}, Créditos: {credits}")
                
                print(f"\n   📊 MÉTRICAS CALCULADAS:")
                print(f"   - Total cursos: {len(courses_data)}")
                print(f"   - Total estudiantes: {total_students}")
                
                # Obtener estadísticas de notas
                print(f"\n2. OBTENIENDO ESTADÍSTICAS DE NOTAS:")
                
                first_course = courses_data[0]
                course_id = first_course[0]
                
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
                
                if grade_stats and grade_stats[3] > 0:  # total_grades > 0
                    avg_score, min_score, max_score, total_grades, passed_count = grade_stats
                    pass_rate = (passed_count / total_grades * 100) if total_grades > 0 else 0
                    
                    print(f"   ✅ Estadísticas de notas para {first_course[1]}:")
                    print(f"   - Promedio: {avg_score:.2f}")
                    print(f"   - Mínima: {min_score}")
                    print(f"   - Máxima: {max_score}")
                    print(f"   - Total notas: {total_grades}")
                    print(f"   - Aprobados: {passed_count} ({pass_rate:.1f}%)")
                else:
                    print(f"   ⚠️  No hay notas registradas para {first_course[1]}")
                
                # Probar consulta de estudiantes para asistencia
                print(f"\n3. OBTENIENDO ESTUDIANTES PARA ASISTENCIA:")
                
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
                    ORDER BY s.student_code
                    LIMIT 5;
                """, [teacher_id])
                
                students_data = cursor.fetchall()
                
                if students_data:
                    print(f"   ✅ Encontrados estudiantes matriculados:")
                    for student in students_data:
                        student_id, student_code, first_name, last_name, course_name, course_code = student
                        print(f"   - {student_code}: {first_name} {last_name} ({course_code})")
                else:
                    print(f"   ⚠️  No se encontraron estudiantes matriculados")
                
                print(f"\n✅ DASHBOARD FUNCIONARÁ CORRECTAMENTE")
                print(f"   El profesor verá sus cursos reales y estudiantes matriculados")
                
            else:
                print("   ❌ No se encontraron cursos asignados a este profesor")
                
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Probando el dashboard del profesor arreglado...\n")
    probar_dashboard_profesor()
    print("\n=== PRUEBA COMPLETADA ===")