#!/usr/bin/env python3
"""
Script para verificar por qué el dashboard del profesor no muestra los cursos asignados
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User

def verificar_asignaciones_profesores():
    """Verificar las asignaciones de cursos a profesores"""
    print("=== VERIFICACIÓN DE ASIGNACIONES DE PROFESORES ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar profesores en el sistema
            print("1. PROFESORES EN EL SISTEMA:")
            cursor.execute("""
                SELECT u.id, u.institutional_email, u.first_name, u.last_name, u.role
                FROM users u
                WHERE u.role = 'teacher'
                ORDER BY u.institutional_email;
            """)
            
            profesores = cursor.fetchall()
            print(f"   Total profesores: {len(profesores)}")
            for prof in profesores:
                print(f"   - ID: {prof[0]}, Email: {prof[1]}, Nombre: {prof[2]} {prof[3]}")
            
            # 2. Verificar tabla teachers
            print("\n2. TABLA TEACHERS:")
            cursor.execute("SELECT COUNT(*) FROM teachers;")
            teachers_count = cursor.fetchone()[0]
            print(f"   Total registros en teachers: {teachers_count}")
            
            if teachers_count > 0:
                cursor.execute("""
                    SELECT t.id, t.teacher_code, u.institutional_email, u.first_name, u.last_name
                    FROM teachers t
                    JOIN users u ON t.user_id = u.id
                    ORDER BY t.teacher_code;
                """)
                teachers = cursor.fetchall()
                for teacher in teachers:
                    print(f"   - Teacher ID: {teacher[0]}, Código: {teacher[1]}, Email: {teacher[2]}, Nombre: {teacher[3]} {teacher[4]}")
            
            # 3. Verificar cursos disponibles
            print("\n3. CURSOS DISPONIBLES:")
            cursor.execute("""
                SELECT c.id, c.code, c.name, c.credits
                FROM courses c
                ORDER BY c.code;
            """)
            
            cursos = cursor.fetchall()
            print(f"   Total cursos: {len(cursos)}")
            for curso in cursos[:5]:  # Mostrar solo los primeros 5
                print(f"   - ID: {curso[0]}, Código: {curso[1]}, Nombre: {curso[2]}")
            
            # 4. Verificar course_groups
            print("\n4. GRUPOS DE CURSOS:")
            cursor.execute("""
                SELECT cg.id, cg.group_code, c.code, c.name, cg.teacher_id
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                ORDER BY c.code, cg.group_code;
            """)
            
            course_groups = cursor.fetchall()
            print(f"   Total grupos de cursos: {len(course_groups)}")
            for cg in course_groups:
                teacher_info = "Sin asignar"
                if cg[4]:  # teacher_id
                    cursor.execute("""
                        SELECT u.institutional_email, u.first_name, u.last_name
                        FROM teachers t
                        JOIN users u ON t.user_id = u.id
                        WHERE t.id = %s;
                    """, [cg[4]])
                    teacher_data = cursor.fetchone()
                    if teacher_data:
                        teacher_info = f"{teacher_data[1]} {teacher_data[2]} ({teacher_data[0]})"
                
                print(f"   - Grupo ID: {cg[0]}, Código: {cg[1]}, Curso: {cg[2]} - {cg[3]}")
                print(f"     Profesor: {teacher_info}")
            
            # 5. Verificar enrollments
            print("\n5. MATRICULACIONES:")
            cursor.execute("SELECT COUNT(*) FROM enrollments;")
            enrollments_count = cursor.fetchone()[0]
            print(f"   Total matriculaciones: {enrollments_count}")
            
            if enrollments_count > 0:
                cursor.execute("""
                    SELECT cg.group_code, c.name, COUNT(e.student_id) as student_count
                    FROM enrollments e
                    JOIN course_groups cg ON e.course_group_id = cg.id
                    JOIN courses c ON cg.course_id = c.id
                    GROUP BY cg.id, cg.group_code, c.name
                    ORDER BY c.name, cg.group_code;
                """)
                
                enrollment_stats = cursor.fetchall()
                for stat in enrollment_stats:
                    print(f"   - {stat[1]} - Grupo {stat[0]}: {stat[2]} estudiantes")
            
            # 6. Probar la consulta del dashboard
            print("\n6. PRUEBA DE CONSULTA DEL DASHBOARD:")
            try:
                cursor.execute("""
                    SELECT 
                        c.id, c.code, c.name, c.credits,
                        COUNT(DISTINCT e.student_id) as student_count,
                        cg.group_code,
                        cg.teacher_id
                    FROM courses c
                    JOIN course_groups cg ON c.id = cg.course_id
                    LEFT JOIN enrollments e ON cg.id = e.course_group_id
                    GROUP BY c.id, c.code, c.name, c.credits, cg.group_code, cg.teacher_id
                    ORDER BY c.code;
                """)
                
                dashboard_data = cursor.fetchall()
                print(f"   Resultados de consulta dashboard: {len(dashboard_data)}")
                
                for data in dashboard_data:
                    teacher_info = "Sin profesor"
                    if data[6]:  # teacher_id
                        cursor.execute("""
                            SELECT u.institutional_email, u.first_name, u.last_name
                            FROM teachers t
                            JOIN users u ON t.user_id = u.id
                            WHERE t.id = %s;
                        """, [data[6]])
                        teacher_data = cursor.fetchone()
                        if teacher_data:
                            teacher_info = f"{teacher_data[1]} {teacher_data[2]}"
                    
                    print(f"   - Curso: {data[1]} - {data[2]}")
                    print(f"     Grupo: {data[5]}, Estudiantes: {data[4]}, Profesor: {teacher_info}")
            
            except Exception as e:
                print(f"   Error en consulta dashboard: {str(e)}")
            
            # 7. Verificar si hay un usuario profesor específico logueado
            print("\n7. VERIFICAR USUARIO PROFESOR ESPECÍFICO:")
            
            # Buscar un profesor específico para probar
            cursor.execute("""
                SELECT u.id, u.institutional_email, u.first_name, u.last_name
                FROM users u
                WHERE u.role = 'teacher'
                LIMIT 1;
            """)
            
            profesor_test = cursor.fetchone()
            if profesor_test:
                user_id, email, first_name, last_name = profesor_test
                print(f"   Probando con profesor: {first_name} {last_name} (ID: {user_id}, Email: {email})")
                
                # Verificar si tiene registro en teachers
                cursor.execute("""
                    SELECT t.id, t.teacher_code
                    FROM teachers t
                    WHERE t.user_id = %s;
                """, [user_id])
                
                teacher_record = cursor.fetchone()
                if teacher_record:
                    teacher_id, teacher_code = teacher_record
                    print(f"   Registro en teachers: ID {teacher_id}, Código: {teacher_code}")
                    
                    # Verificar cursos asignados a este profesor
                    cursor.execute("""
                        SELECT c.code, c.name, cg.group_code, COUNT(e.student_id) as students
                        FROM course_groups cg
                        JOIN courses c ON cg.course_id = c.id
                        LEFT JOIN enrollments e ON cg.id = e.course_group_id
                        WHERE cg.teacher_id = %s
                        GROUP BY c.id, c.code, c.name, cg.group_code
                        ORDER BY c.code;
                    """, [teacher_id])
                    
                    assigned_courses = cursor.fetchall()
                    print(f"   Cursos asignados: {len(assigned_courses)}")
                    for course in assigned_courses:
                        print(f"     - {course[0]} - {course[1]} (Grupo {course[2]}): {course[3]} estudiantes")
                else:
                    print(f"   ❌ No tiene registro en la tabla teachers")
            else:
                print("   No se encontraron profesores en el sistema")
            
    except Exception as e:
        print(f"Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()

def verificar_problema_dashboard():
    """Identificar el problema específico del dashboard"""
    print("\n=== DIAGNÓSTICO DEL PROBLEMA DEL DASHBOARD ===\n")
    
    try:
        with connection.cursor() as cursor:
            # Verificar la consulta exacta que usa el dashboard
            print("1. EJECUTANDO CONSULTA DEL DASHBOARD:")
            cursor.execute("""
                SELECT 
                    c.id, c.code, c.name, c.credits,
                    COUNT(DISTINCT e.student_id) as student_count,
                    cg.group_code
                FROM courses c
                JOIN course_groups cg ON c.id = cg.course_id
                LEFT JOIN enrollments e ON cg.id = e.course_group_id
                GROUP BY c.id, c.code, c.name, c.credits, cg.group_code
                LIMIT 1;
            """)
            
            course_data = cursor.fetchone()
            
            if course_data:
                print("   ✅ La consulta devuelve datos:")
                print(f"   - Curso ID: {course_data[0]}")
                print(f"   - Código: {course_data[1]}")
                print(f"   - Nombre: {course_data[2]}")
                print(f"   - Créditos: {course_data[3]}")
                print(f"   - Estudiantes: {course_data[4]}")
                print(f"   - Grupo: {course_data[5]}")
                
                # Verificar si hay notas para este curso
                cursor.execute("""
                    SELECT 
                        AVG(g.score) as avg_score,
                        MIN(g.score) as min_score,
                        MAX(g.score) as max_score,
                        COUNT(g.id) as total_grades
                    FROM grades g
                    JOIN evaluation_types et ON g.evaluation_type_id = et.id
                    JOIN course_groups cg ON et.course_group_id = cg.id
                    JOIN courses c ON cg.course_id = c.id
                    WHERE c.id = %s;
                """, [course_data[0]])
                
                grade_stats = cursor.fetchone()
                if grade_stats and grade_stats[3] > 0:  # total_grades > 0
                    print(f"   ✅ Hay notas: {grade_stats[3]} registros")
                    print(f"   - Promedio: {grade_stats[0]:.2f}")
                    print(f"   - Mínima: {grade_stats[1]}")
                    print(f"   - Máxima: {grade_stats[2]}")
                else:
                    print("   ⚠️  No hay notas registradas para este curso")
                
            else:
                print("   ❌ La consulta no devuelve datos")
                print("   Posibles causas:")
                print("   - No hay cursos en la tabla courses")
                print("   - No hay grupos en course_groups")
                print("   - No hay relación entre courses y course_groups")
            
            # Verificar cada tabla individualmente
            print("\n2. VERIFICACIÓN INDIVIDUAL DE TABLAS:")
            
            cursor.execute("SELECT COUNT(*) FROM courses;")
            courses_count = cursor.fetchone()[0]
            print(f"   - Tabla courses: {courses_count} registros")
            
            cursor.execute("SELECT COUNT(*) FROM course_groups;")
            groups_count = cursor.fetchone()[0]
            print(f"   - Tabla course_groups: {groups_count} registros")
            
            cursor.execute("SELECT COUNT(*) FROM enrollments;")
            enrollments_count = cursor.fetchone()[0]
            print(f"   - Tabla enrollments: {enrollments_count} registros")
            
            cursor.execute("SELECT COUNT(*) FROM evaluation_types;")
            eval_types_count = cursor.fetchone()[0]
            print(f"   - Tabla evaluation_types: {eval_types_count} registros")
            
            cursor.execute("SELECT COUNT(*) FROM grades;")
            grades_count = cursor.fetchone()[0]
            print(f"   - Tabla grades: {grades_count} registros")
            
            # Verificar relaciones
            print("\n3. VERIFICACIÓN DE RELACIONES:")
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM courses c
                JOIN course_groups cg ON c.id = cg.course_id;
            """)
            course_group_relations = cursor.fetchone()[0]
            print(f"   - Relación courses -> course_groups: {course_group_relations} registros")
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM course_groups cg
                LEFT JOIN enrollments e ON cg.id = e.course_group_id;
            """)
            group_enrollment_relations = cursor.fetchone()[0]
            print(f"   - Relación course_groups -> enrollments: {group_enrollment_relations} registros")
            
    except Exception as e:
        print(f"Error en diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Iniciando verificación del dashboard del profesor...\n")
    verificar_asignaciones_profesores()
    verificar_problema_dashboard()
    print("\n=== VERIFICACIÓN COMPLETADA ===")