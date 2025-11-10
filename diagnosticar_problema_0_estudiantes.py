#!/usr/bin/env python3
"""
Script para diagnosticar por qué aparecen 0 estudiantes en el dashboard del profesor
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def diagnosticar_problema():
    """Diagnosticar el problema de 0 estudiantes"""
    print("=== DIAGNÓSTICO: ¿POR QUÉ 0 ESTUDIANTES? ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar qué profesor está logueado (simular con el que tiene cursos)
            print("1. IDENTIFICAR PROFESOR CON CURSO 'MATEMATICA APLICADA':")
            cursor.execute("""
                SELECT 
                    u.id as user_id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    t.id as teacher_id,
                    c.code,
                    c.name as course_name
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                JOIN course_groups cg ON t.id = cg.teacher_id
                JOIN courses c ON cg.course_id = c.id
                WHERE c.name ILIKE '%MATEMATICA%APLICADA%'
                ORDER BY u.first_name;
            """)
            
            profesores_matematica = cursor.fetchall()
            
            if not profesores_matematica:
                print("   ❌ NO HAY PROFESORES ASIGNADOS A MATEMÁTICA APLICADA")
                
                # Verificar si existe el curso
                cursor.execute("""
                    SELECT id, code, name FROM courses 
                    WHERE name ILIKE '%MATEMATICA%APLICADA%';
                """)
                curso_existe = cursor.fetchone()
                
                if curso_existe:
                    print(f"   ✅ El curso existe: {curso_existe[1]} - {curso_existe[2]}")
                    
                    # Verificar si tiene grupos
                    cursor.execute("""
                        SELECT cg.id, cg.group_code, cg.teacher_id
                        FROM course_groups cg
                        WHERE cg.course_id = %s;
                    """, [curso_existe[0]])
                    
                    grupos = cursor.fetchall()
                    print(f"   Grupos del curso: {len(grupos)}")
                    
                    for grupo in grupos:
                        cg_id, group_code, teacher_id = grupo
                        if teacher_id:
                            cursor.execute("""
                                SELECT u.first_name, u.last_name
                                FROM teachers t
                                JOIN users u ON t.user_id = u.id
                                WHERE t.id = %s;
                            """, [teacher_id])
                            teacher_info = cursor.fetchone()
                            teacher_name = f"{teacher_info[0]} {teacher_info[1]}" if teacher_info else "Desconocido"
                        else:
                            teacher_name = "Sin asignar"
                        
                        print(f"   - Grupo {group_code}: Profesor {teacher_name}")
                else:
                    print("   ❌ EL CURSO MATEMÁTICA APLICADA NO EXISTE")
                
                return
            
            print(f"   ✅ Encontrados {len(profesores_matematica)} profesor(es) con Matemática Aplicada:")
            
            for prof in profesores_matematica:
                user_id, first_name, last_name, email, teacher_id, course_code, course_name = prof
                print(f"   - {first_name} {last_name} ({email})")
                print(f"     User ID: {user_id}, Teacher ID: {teacher_id}")
                print(f"     Curso: {course_code} - {course_name}")
            
            # 2. Tomar el primer profesor y verificar sus datos
            profesor_test = profesores_matematica[0]
            user_id, first_name, last_name, email, teacher_id, course_code, course_name = profesor_test
            
            print(f"\n2. ANALIZANDO PROFESOR: {first_name} {last_name}")
            print(f"   User ID: {user_id}")
            print(f"   Teacher ID: {teacher_id}")
            
            # 3. Verificar la consulta exacta del dashboard
            print(f"\n3. EJECUTANDO CONSULTA DEL DASHBOARD:")
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
            
            dashboard_results = cursor.fetchall()
            
            if dashboard_results:
                print(f"   ✅ Consulta dashboard devuelve {len(dashboard_results)} resultado(s):")
                for result in dashboard_results:
                    course_id, code, name, credits, student_count, group_code = result
                    print(f"   - {code}: {name} (Grupo {group_code}) - {student_count} estudiantes")
                    
                    if student_count == 0:
                        print(f"     ⚠️  PROBLEMA: 0 estudiantes en {code}")
                        
                        # Verificar si hay enrollments para este course_group
                        cursor.execute("""
                            SELECT cg.id FROM course_groups cg
                            WHERE cg.teacher_id = %s AND cg.course_id = %s;
                        """, [teacher_id, course_id])
                        
                        cg_result = cursor.fetchone()
                        if cg_result:
                            cg_id = cg_result[0]
                            
                            cursor.execute("""
                                SELECT COUNT(*) FROM enrollments
                                WHERE course_group_id = %s;
                            """, [cg_id])
                            
                            enrollment_count = cursor.fetchone()[0]
                            print(f"     - Enrollments en course_group {cg_id}: {enrollment_count}")
                            
                            if enrollment_count > 0:
                                cursor.execute("""
                                    SELECT s.student_code, u.first_name, u.last_name
                                    FROM enrollments e
                                    JOIN students s ON e.student_id = s.id
                                    JOIN users u ON s.user_id = u.id
                                    WHERE e.course_group_id = %s
                                    LIMIT 3;
                                """, [cg_id])
                                
                                sample_students = cursor.fetchall()
                                print(f"     - Estudiantes matriculados (muestra):")
                                for student in sample_students:
                                    print(f"       * {student[0]}: {student[1]} {student[2]}")
            else:
                print(f"   ❌ La consulta del dashboard NO devuelve resultados")
                print(f"   Esto significa que el teacher_id {teacher_id} no tiene cursos asignados")
            
            # 4. Verificar enrollments globales
            print(f"\n4. VERIFICAR ENROLLMENTS GLOBALES:")
            cursor.execute("""
                SELECT 
                    c.code,
                    c.name,
                    cg.group_code,
                    COUNT(e.student_id) as enrolled_count
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LEFT JOIN enrollments e ON cg.id = e.course_group_id
                WHERE c.name ILIKE '%MATEMATICA%APLICADA%'
                GROUP BY c.code, c.name, cg.group_code
                ORDER BY c.code;
            """)
            
            global_enrollments = cursor.fetchall()
            
            if global_enrollments:
                print(f"   Enrollments en Matemática Aplicada:")
                for enrollment in global_enrollments:
                    code, name, group_code, enrolled_count = enrollment
                    print(f"   - {code} (Grupo {group_code}): {enrolled_count} estudiantes")
            else:
                print(f"   ❌ NO HAY ENROLLMENTS EN MATEMÁTICA APLICADA")
            
            # 5. Verificar si el problema es de asignación de profesor
            print(f"\n5. VERIFICAR ASIGNACIÓN DE PROFESORES:")
            cursor.execute("""
                SELECT 
                    cg.id,
                    c.code,
                    c.name,
                    cg.group_code,
                    cg.teacher_id,
                    CASE 
                        WHEN cg.teacher_id IS NULL THEN 'Sin profesor'
                        ELSE u.first_name || ' ' || u.last_name
                    END as profesor_name
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LEFT JOIN teachers t ON cg.teacher_id = t.id
                LEFT JOIN users u ON t.user_id = u.id
                WHERE c.name ILIKE '%MATEMATICA%APLICADA%'
                ORDER BY c.code;
            """)
            
            assignments = cursor.fetchall()
            
            if assignments:
                print(f"   Asignaciones de profesores:")
                for assignment in assignments:
                    cg_id, code, name, group_code, teacher_id, profesor_name = assignment
                    print(f"   - {code} (Grupo {group_code}): {profesor_name}")
                    
                    if teacher_id == teacher_id:  # Es el profesor que estamos probando
                        print(f"     ✅ Este es el grupo del profesor {first_name} {last_name}")
            
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnosticar_problema()