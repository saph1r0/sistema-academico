#!/usr/bin/env python3
"""
Script para arreglar las matriculaciones y asegurar que los estudiantes estén matriculados en los cursos correctos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def verificar_y_arreglar_matriculaciones():
    """Verificar y arreglar las matriculaciones de estudiantes"""
    print("=== VERIFICANDO Y ARREGLANDO MATRICULACIONES ===\n")
    
    try:
        with connection.cursor() as cursor:
            # 1. Verificar profesores reales vs nombres de cursos
            print("1. VERIFICANDO PROFESORES:")
            cursor.execute("""
                SELECT u.id, u.email, u.first_name, u.last_name
                FROM users u
                WHERE u.role = 'profesor'
                ORDER BY u.first_name, u.last_name;
            """)
            
            profesores = cursor.fetchall()
            print(f"   Total profesores: {len(profesores)}")
            
            profesores_reales = []
            for prof in profesores:
                user_id, email, first_name, last_name = prof
                # Filtrar profesores que parecen ser nombres de cursos
                if not any(word in first_name.upper() for word in ['FUNDAMENTOS', 'MATEMATICA', 'COMPUTACION', 'ALGORITMOS']):
                    profesores_reales.append(prof)
                    print(f"   ✅ Profesor real: {first_name} {last_name} ({email})")
                else:
                    print(f"   ⚠️  Posible curso como profesor: {first_name} {last_name}")
            
            # 2. Verificar estudiantes disponibles
            print(f"\n2. VERIFICANDO ESTUDIANTES:")
            cursor.execute("SELECT COUNT(*) FROM students;")
            total_students = cursor.fetchone()[0]
            print(f"   Total estudiantes en sistema: {total_students}")
            
            if total_students == 0:
                print("   ❌ No hay estudiantes en el sistema")
                return
            
            # 3. Verificar course_groups disponibles
            print(f"\n3. VERIFICANDO GRUPOS DE CURSOS:")
            cursor.execute("""
                SELECT cg.id, cg.group_code, c.code, c.name, cg.teacher_id
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                ORDER BY c.code;
            """)
            
            course_groups = cursor.fetchall()
            print(f"   Total grupos de cursos: {len(course_groups)}")
            
            # 4. Verificar matriculaciones actuales
            print(f"\n4. VERIFICANDO MATRICULACIONES ACTUALES:")
            cursor.execute("""
                SELECT cg.id, c.code, c.name, cg.group_code, COUNT(e.student_id) as enrolled_count
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LEFT JOIN enrollments e ON cg.id = e.course_group_id
                GROUP BY cg.id, c.code, c.name, cg.group_code
                ORDER BY c.code;
            """)
            
            enrollment_stats = cursor.fetchall()
            
            grupos_sin_estudiantes = []
            for stat in enrollment_stats:
                cg_id, code, name, group_code, enrolled_count = stat
                print(f"   - {code} ({group_code}): {enrolled_count} estudiantes")
                if enrolled_count == 0:
                    grupos_sin_estudiantes.append((cg_id, code, name, group_code))
            
            # 5. Matricular estudiantes en grupos vacíos
            if grupos_sin_estudiantes and total_students > 0:
                print(f"\n5. MATRICULANDO ESTUDIANTES EN GRUPOS VACÍOS:")
                
                # Obtener lista de estudiantes
                cursor.execute("""
                    SELECT s.id, s.student_code, u.first_name, u.last_name
                    FROM students s
                    JOIN users u ON s.user_id = u.id
                    ORDER BY s.student_code
                    LIMIT 50;
                """)
                
                students = cursor.fetchall()
                print(f"   Estudiantes disponibles: {len(students)}")
                
                matriculados_total = 0
                
                for cg_id, code, name, group_code in grupos_sin_estudiantes[:5]:  # Solo los primeros 5 grupos
                    print(f"\n   Matriculando en {code} - {name} (Grupo {group_code}):")
                    
                    # Matricular entre 5-15 estudiantes por grupo
                    import random
                    num_to_enroll = min(random.randint(5, 15), len(students))
                    selected_students = random.sample(students, num_to_enroll)
                    
                    matriculados_grupo = 0
                    for student in selected_students:
                        student_id, student_code, first_name, last_name = student
                        
                        try:
                            # Verificar si ya está matriculado
                            cursor.execute("""
                                SELECT COUNT(*) FROM enrollments 
                                WHERE student_id = %s AND course_group_id = %s;
                            """, [student_id, cg_id])
                            
                            if cursor.fetchone()[0] == 0:
                                # Matricular estudiante
                                cursor.execute("""
                                    INSERT INTO enrollments (student_id, course_group_id, enrollment_date, status)
                                    VALUES (%s, %s, CURRENT_DATE, 'active');
                                """, [student_id, cg_id])
                                
                                matriculados_grupo += 1
                                print(f"     ✅ {student_code}: {first_name} {last_name}")
                            
                        except Exception as e:
                            print(f"     ❌ Error matriculando {student_code}: {str(e)}")
                    
                    matriculados_total += matriculados_grupo
                    print(f"   Total matriculados en {code}: {matriculados_grupo}")
                
                print(f"\n   ✅ TOTAL MATRICULACIONES REALIZADAS: {matriculados_total}")
            
            # 6. Verificar resultado final
            print(f"\n6. VERIFICACIÓN FINAL:")
            cursor.execute("""
                SELECT cg.id, c.code, c.name, cg.group_code, COUNT(e.student_id) as enrolled_count
                FROM course_groups cg
                JOIN courses c ON cg.course_id = c.id
                LEFT JOIN enrollments e ON cg.id = e.course_group_id
                GROUP BY cg.id, c.code, c.name, cg.group_code
                HAVING COUNT(e.student_id) > 0
                ORDER BY c.code;
            """)
            
            final_stats = cursor.fetchall()
            print(f"   Grupos con estudiantes matriculados: {len(final_stats)}")
            
            for stat in final_stats:
                cg_id, code, name, group_code, enrolled_count = stat
                print(f"   ✅ {code} ({group_code}): {enrolled_count} estudiantes")
            
    except Exception as e:
        print(f"❌ Error durante el proceso: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Iniciando arreglo de matriculaciones...\n")
    verificar_y_arreglar_matriculaciones()
    print("\n=== PROCESO COMPLETADO ===")