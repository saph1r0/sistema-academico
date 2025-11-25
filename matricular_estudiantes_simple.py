#!/usr/bin/env python3
"""
Script simple para matricular estudiantes usando SQL directo
"""

import psycopg2
import random

def conectar_db():
    """Conectar a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="sistema_academico",
            user="postgres",
            password="admin"
        )
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def matricular_estudiantes():
    """Matricular estudiantes en cursos"""
    print("=== MATRICULANDO ESTUDIANTES ===\n")
    
    conn = conectar_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. Verificar estudiantes disponibles
        cursor.execute("SELECT COUNT(*) FROM students;")
        total_students = cursor.fetchone()[0]
        print(f"Total estudiantes: {total_students}")
        
        if total_students == 0:
            print("❌ No hay estudiantes en el sistema")
            return
        
        # 2. Obtener grupos de cursos sin estudiantes
        cursor.execute("""
            SELECT cg.id, c.code, c.name, cg.group_code, COUNT(e.student_id) as enrolled_count
            FROM course_groups cg
            JOIN courses c ON cg.course_id = c.id
            LEFT JOIN enrollments e ON cg.id = e.course_group_id
            GROUP BY cg.id, c.code, c.name, cg.group_code
            ORDER BY c.code;
        """)
        
        groups = cursor.fetchall()
        grupos_vacios = [g for g in groups if g[4] == 0]  # enrolled_count == 0
        
        print(f"Grupos de cursos encontrados: {len(groups)}")
        print(f"Grupos sin estudiantes: {len(grupos_vacios)}")
        
        # 3. Obtener lista de estudiantes
        cursor.execute("""
            SELECT s.id, s.student_code, u.first_name, u.last_name
            FROM students s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.student_code;
        """)
        
        students = cursor.fetchall()
        print(f"Estudiantes disponibles: {len(students)}")
        
        # 4. Matricular estudiantes en grupos vacíos
        matriculados_total = 0
        
        for group in grupos_vacios[:10]:  # Solo los primeros 10 grupos
            cg_id, code, name, group_code, enrolled_count = group
            print(f"\nMatriculando en {code} - {name} (Grupo {group_code}):")
            
            # Matricular entre 3-12 estudiantes por grupo
            num_to_enroll = min(random.randint(3, 12), len(students))
            selected_students = random.sample(students, num_to_enroll)
            
            matriculados_grupo = 0
            for student in selected_students:
                student_id, student_code, first_name, last_name = student
                
                try:
                    # Verificar si ya está matriculado
                    cursor.execute("""
                        SELECT COUNT(*) FROM enrollments 
                        WHERE student_id = %s AND course_group_id = %s;
                    """, (student_id, cg_id))
                    
                    if cursor.fetchone()[0] == 0:
                        # Matricular estudiante
                        cursor.execute("""
                            INSERT INTO enrollments (student_id, course_group_id, enrollment_date, status)
                            VALUES (%s, %s, CURRENT_DATE, 'active');
                        """, (student_id, cg_id))
                        
                        matriculados_grupo += 1
                        print(f"  ✅ {student_code}: {first_name} {last_name}")
                    
                except Exception as e:
                    print(f"  ❌ Error matriculando {student_code}: {str(e)}")
            
            matriculados_total += matriculados_grupo
            print(f"  Total matriculados en {code}: {matriculados_grupo}")
        
        # Confirmar cambios
        conn.commit()
        print(f"\n✅ TOTAL MATRICULACIONES REALIZADAS: {matriculados_total}")
        
        # 5. Verificar resultado final
        print(f"\n=== VERIFICACIÓN FINAL ===")
        cursor.execute("""
            SELECT c.code, c.name, cg.group_code, COUNT(e.student_id) as enrolled_count
            FROM course_groups cg
            JOIN courses c ON cg.course_id = c.id
            LEFT JOIN enrollments e ON cg.id = e.course_group_id
            GROUP BY c.code, c.name, cg.group_code
            HAVING COUNT(e.student_id) > 0
            ORDER BY c.code;
        """)
        
        final_stats = cursor.fetchall()
        print(f"Grupos con estudiantes matriculados: {len(final_stats)}")
        
        for stat in final_stats:
            code, name, group_code, enrolled_count = stat
            print(f"✅ {code} ({group_code}): {enrolled_count} estudiantes")
        
    except Exception as e:
        print(f"❌ Error durante el proceso: {str(e)}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    matricular_estudiantes()