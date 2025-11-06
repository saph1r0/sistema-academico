#!/usr/bin/env python3
"""
Script para verificar que los datos están correctos y el dashboard debería funcionar
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def verificar_datos_completos():
    """Verificar que todos los datos están correctos"""
    print("=== VERIFICACIÓN FINAL DE DATOS ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar profesores reales (no nombres de cursos)
            print("1. PROFESORES REALES:")
            cursor.execute("""
                SELECT u.id, u.first_name, u.last_name, u.email, t.id as teacher_id
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                WHERE u.role = 'profesor' 
                AND NOT (u.first_name ILIKE '%FUNDAMENTOS%' OR u.first_name ILIKE '%MATEMATICA%' 
                         OR u.first_name ILIKE '%COMPUTACION%' OR u.first_name ILIKE '%ALGORITMOS%')
                ORDER BY u.first_name, u.last_name;
            """)
            
            profesores_reales = cursor.fetchall()
            print(f"   Total profesores reales: {len(profesores_reales)}")
            
            for prof in profesores_reales:
                user_id, first_name, last_name, email, teacher_id = prof
                print(f"   ✅ {first_name} {last_name} ({email}) - Teacher ID: {teacher_id}")
                
                # Verificar cursos asignados a este profesor
                cursor.execute("""
                    SELECT c.code, c.name, cg.group_code, COUNT(e.student_id) as students
                    FROM course_groups cg
                    JOIN courses c ON cg.course_id = c.id
                    LEFT JOIN enrollments e ON cg.id = e.course_group_id
                    WHERE cg.teacher_id = %s
                    GROUP BY c.code, c.name, cg.group_code
                    ORDER BY c.code;
                """, [teacher_id])
                
                cursos = cursor.fetchall()
                if cursos:
                    print(f"      Cursos asignados: {len(cursos)}")
                    for curso in cursos:
                        code, name, group_code, students = curso
                        print(f"      - {code}: {name} (Grupo {group_code}) - {students} estudiantes")
                else:
                    print(f"      ⚠️  Sin cursos asignados")
                print()
            
            # 2. Verificar que hay estudiantes matriculados
            print("2. RESUMEN DE MATRICULACIONES:")
            cursor.execute("""
                SELECT 
                    c.code, 
                    c.name, 
                    cg.group_code,
                    COUNT(e.student_id) as enrolled_students,
                    u.first_name || ' ' || u.last_name as profesor
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LEFT JOIN enrollments e ON cg.id = e.course_group_id
                LEFT JOIN teachers t ON cg.teacher_id = t.id
                LEFT JOIN users u ON t.user_id = u.id
                GROUP BY c.code, c.name, cg.group_code, u.first_name, u.last_name
                HAVING COUNT(e.student_id) > 0
                ORDER BY c.code;
            """)
            
            matriculaciones = cursor.fetchall()
            print(f"   Cursos con estudiantes matriculados: {len(matriculaciones)}")
            
            total_estudiantes = 0
            for mat in matriculaciones:
                code, name, group_code, enrolled_students, profesor = mat
                total_estudiantes += enrolled_students
                print(f"   ✅ {code} ({group_code}): {enrolled_students} estudiantes - Prof: {profesor}")
            
            print(f"\n   📊 TOTAL ESTUDIANTES MATRICULADOS: {total_estudiantes}")
            
            # 3. Verificar que el dashboard funcionará
            print(f"\n3. SIMULACIÓN DEL DASHBOARD:")
            
            if profesores_reales:
                # Tomar el primer profesor real
                primer_profesor = profesores_reales[0]
                user_id, first_name, last_name, email, teacher_id = primer_profesor
                
                print(f"   Simulando dashboard para: {first_name} {last_name}")
                
                # Simular la consulta del dashboard
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
                
                dashboard_data = cursor.fetchone()
                
                if dashboard_data:
                    course_id, code, name, credits, student_count, group_code = dashboard_data
                    print(f"   ✅ Dashboard mostrará:")
                    print(f"      - Curso: {code} - {name}")
                    print(f"      - Grupo: {group_code}")
                    print(f"      - Estudiantes: {student_count}")
                    print(f"      - Créditos: {credits}")
                    
                    # Verificar notas para este curso
                    cursor.execute("""
                        SELECT 
                            AVG(g.score) as avg_score,
                            COUNT(g.id) as total_grades
                        FROM grades g
                        JOIN evaluation_types et ON g.evaluation_type_id = et.id
                        JOIN course_groups cg ON et.course_group_id = cg.id
                        WHERE cg.course_id = %s;
                    """, [course_id])
                    
                    grade_stats = cursor.fetchone()
                    if grade_stats and grade_stats[1] > 0:
                        avg_score, total_grades = grade_stats
                        print(f"      - Promedio de notas: {avg_score:.2f}")
                        print(f"      - Total notas: {total_grades}")
                    else:
                        print(f"      - Sin notas registradas")
                    
                    print(f"\n   ✅ EL DASHBOARD FUNCIONARÁ CORRECTAMENTE")
                else:
                    print(f"   ❌ Este profesor no tiene cursos asignados")
            
            # 4. Verificar vista de asistencia
            print(f"\n4. SIMULACIÓN DE VISTA DE ASISTENCIA:")
            
            if profesores_reales:
                primer_profesor = profesores_reales[0]
                teacher_id = primer_profesor[4]
                
                cursor.execute("""
                    SELECT DISTINCT
                        s.id,
                        s.student_code,
                        u.first_name,
                        u.last_name,
                        c.name as course_name
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    JOIN enrollments e ON s.id = e.student_id
                    JOIN course_groups cg ON e.course_group_id = cg.id
                    JOIN courses c ON cg.course_id = c.id
                    WHERE cg.teacher_id = %s
                    ORDER BY s.student_code
                    LIMIT 5;
                """, [teacher_id])
                
                estudiantes_asistencia = cursor.fetchall()
                
                if estudiantes_asistencia:
                    print(f"   ✅ Vista de asistencia mostrará {len(estudiantes_asistencia)} estudiantes:")
                    for est in estudiantes_asistencia:
                        student_id, student_code, first_name, last_name, course_name = est
                        print(f"      - {student_code}: {first_name} {last_name} ({course_name})")
                else:
                    print(f"   ❌ No hay estudiantes para mostrar en asistencia")
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_datos_completos()