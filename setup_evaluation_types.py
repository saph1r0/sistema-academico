#!/usr/bin/env python3
"""
Script para configurar completamente el sistema de evaluaciones
"""
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def setup_evaluation_types():
    """Configura completamente el sistema de evaluaciones"""
    
    try:
        with connection.cursor() as cursor:
            print("🔍 Verificando configuración actual...")
            
            # 1. Verificar academic_periods
            cursor.execute("SELECT id, name, is_active FROM academic_periods WHERE is_active = true;")
            period = cursor.fetchone()
            
            if not period:
                print(" No hay período académico activo")
                return False
                
            period_id = period[0]
            print(f" Período académico activo: {period[1]} (ID: {period_id})")
            
            # 2. Verificar courses
            cursor.execute("SELECT id, code, name FROM courses LIMIT 1;")
            course = cursor.fetchone()
            
            if not course:
                print(" No hay cursos disponibles")
                return False
                
            course_id = course[0]
            print(f" Curso disponible: {course[1]} - {course[2]} (ID: {course_id})")
            
            # 3. Verificar teachers
            cursor.execute("SELECT id, teacher_code FROM teachers LIMIT 1;")
            teacher = cursor.fetchone()
            
            if not teacher:
                print(" No hay profesores disponibles")
                return False
                
            teacher_id = teacher[0]
            print(f" Profesor disponible: {teacher[1]} (ID: {teacher_id})")
            
            # 4. Verificar o crear course_group
            cursor.execute("SELECT id, group_code FROM course_groups WHERE course_id = %s AND academic_period_id = %s;", [course_id, period_id])
            course_group = cursor.fetchone()
            
            if not course_group:
                print("📝 Creando course_group...")
                cursor.execute("""
                    INSERT INTO course_groups (course_id, academic_period_id, group_code, teacher_id, capacity)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, group_code;
                """, [course_id, period_id, 'A', teacher_id, 60])
                course_group = cursor.fetchone()
                print(f" Course group creado: {course_group[1]} (ID: {course_group[0]})")
            else:
                print(f" Course group existente: {course_group[1]} (ID: {course_group[0]})")
            
            course_group_id = course_group[0]
            
            # 5. Verificar enrollments
            cursor.execute("SELECT COUNT(*) FROM enrollments WHERE course_group_id = %s;", [course_group_id])
            enrollment_count = cursor.fetchone()[0]
            
            if enrollment_count == 0:
                print(" Creando enrollments para todos los estudiantes...")
                cursor.execute("""
                    INSERT INTO enrollments (student_id, course_group_id, academic_period_id)
                    SELECT s.id, %s, %s
                    FROM students s;
                """, [course_group_id, period_id])
                
                cursor.execute("SELECT COUNT(*) FROM enrollments WHERE course_group_id = %s;", [course_group_id])
                new_count = cursor.fetchone()[0]
                print(f" {new_count} estudiantes matriculados")
            else:
                print(f" {enrollment_count} estudiantes ya matriculados")
            
            # 6. Crear tipos de evaluación
            cursor.execute("SELECT COUNT(*) FROM evaluation_types WHERE course_group_id = %s;", [course_group_id])
            eval_count = cursor.fetchone()[0]
            
            if eval_count == 0:
                print(" Creando tipos de evaluación...")
                
                evaluaciones = [
                    ('Parcial 1', 0.33, 20.00),
                    ('Parcial 2', 0.33, 20.00), 
                    ('Parcial 3', 0.34, 20.00)
                ]
                
                for nombre, peso, max_score in evaluaciones:
                    cursor.execute("""
                        INSERT INTO evaluation_types (course_group_id, name, weight, max_score)
                        VALUES (%s, %s, %s, %s);
                    """, [course_group_id, nombre, peso, max_score])
                    print(f" Creado: {nombre} (peso: {peso}, máximo: {max_score})")
            else:
                print(f" {eval_count} tipos de evaluación ya existen")
            
            # 7. Mostrar resumen final
            print("\n Resumen del sistema configurado:")
            print("=" * 40)
            
            cursor.execute("""
                SELECT et.id, et.name, et.weight, et.max_score
                FROM evaluation_types et
                WHERE et.course_group_id = %s
                ORDER BY et.name;
            """, [course_group_id])
            
            tipos = cursor.fetchall()
            for tipo in tipos:
                print(f"   {tipo[1]}")
                print(f"     ID: {tipo[0]}")
                print(f"     Peso: {tipo[2]} | Máximo: {tipo[3]}")
                print()
            
            cursor.execute("SELECT COUNT(*) FROM enrollments WHERE course_group_id = %s;", [course_group_id])
            total_estudiantes = cursor.fetchone()[0]
            print(f" Estudiantes matriculados: {total_estudiantes}")
            
            cursor.execute("SELECT COUNT(*) FROM grades;")
            total_notas = cursor.fetchone()[0]
            print(f" Notas registradas: {total_notas}")
            
            return True
            
    except Exception as e:
        print(f" Error al configurar tipos de evaluación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(" Configurando tipos de evaluación...")
    print("=" * 50)
    
    if setup_evaluation_types():
        print("\n Sistema configurado exitosamente!")
        print("Ahora puedes cargar las notas desde Excel.")
    else:
        print("\n Error en la configuración")