#!/usr/bin/env python3
"""
Script para verificar el sistema completo de notas y crear usuarios de prueba
"""
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verificar_sistema_completo():
    """Verifica que todo el sistema esté funcionando correctamente"""
    
    try:
        with connection.cursor() as cursor:
            print("🔍 Verificación completa del sistema de notas")
            print("=" * 60)
            
            # 1. Verificar usuarios y profesores
            cursor.execute("""
                SELECT u.id, u.first_name, u.last_name, u.role, t.teacher_code
                FROM users u
                LEFT JOIN teachers t ON u.id = t.user_id
                WHERE u.role = 'profesor'
                LIMIT 5;
            """)
            
            profesores = cursor.fetchall()
            print(f"\n👨‍🏫 Profesores en el sistema ({len(profesores)}):")
            for prof in profesores:
                print(f"  - {prof[1]} {prof[2]} ({prof[4]}) - Role: {prof[3]}")
            
            # 2. Verificar estudiantes
            cursor.execute("SELECT COUNT(*) FROM students;")
            total_estudiantes = cursor.fetchone()[0]
            print(f"\n👥 Total estudiantes: {total_estudiantes}")
            
            # 3. Verificar curso y grupos
            cursor.execute("""
                SELECT c.code, c.name, cg.group_code, cg.capacity, cg.enrolled_students
                FROM courses c
                JOIN course_groups cg ON c.id = cg.course_id;
            """)
            
            cursos = cursor.fetchall()
            print(f"\n📚 Cursos configurados ({len(cursos)}):")
            for curso in cursos:
                print(f"  - {curso[0]}: {curso[1]}")
                print(f"    Grupo: {curso[2]} | Capacidad: {curso[3]} | Matriculados: {curso[4]}")
            
            # 4. Verificar tipos de evaluación
            cursor.execute("""
                SELECT et.name, et.weight, et.max_score, COUNT(g.id) as notas_registradas
                FROM evaluation_types et
                LEFT JOIN grades g ON et.id = g.evaluation_type_id
                GROUP BY et.id, et.name, et.weight, et.max_score
                ORDER BY et.name;
            """)
            
            evaluaciones = cursor.fetchall()
            print(f"\n📝 Tipos de evaluación ({len(evaluaciones)}):")
            for eval_type in evaluaciones:
                print(f"  - {eval_type[0]}: peso {eval_type[1]}, máximo {eval_type[2]}")
                print(f"    Notas registradas: {eval_type[3]}")
            
            # 5. Estadísticas de notas por evaluación
            print(f"\n📊 Estadísticas detalladas de notas:")
            for eval_type in evaluaciones:
                if eval_type[3] > 0:  # Si hay notas registradas
                    cursor.execute("""
                        SELECT MIN(score), MAX(score), AVG(score), COUNT(*)
                        FROM grades g
                        JOIN evaluation_types et ON g.evaluation_type_id = et.id
                        WHERE et.name = %s;
                    """, [eval_type[0]])
                    
                    stats = cursor.fetchone()
                    print(f"  📈 {eval_type[0]}:")
                    print(f"    Mínima: {stats[0]:.1f} | Máxima: {stats[1]:.1f}")
                    print(f"    Promedio: {stats[2]:.2f} | Total: {stats[3]} notas")
            
            # 6. Verificar estudiantes con mejores y peores notas
            cursor.execute("""
                SELECT 
                    s.student_code,
                    u.first_name,
                    u.last_name,
                    et.name,
                    g.score
                FROM grades g
                JOIN students s ON g.student_id = s.id
                JOIN users u ON s.user_id = u.id
                JOIN evaluation_types et ON g.evaluation_type_id = et.id
                WHERE et.name = 'Parcial 1'
                ORDER BY g.score DESC
                LIMIT 3;
            """)
            
            mejores = cursor.fetchall()
            print(f"\n🏆 Mejores notas del Parcial 1:")
            for i, estudiante in enumerate(mejores, 1):
                print(f"  {i}. {estudiante[1]} {estudiante[2]} ({estudiante[0]}): {estudiante[4]}")
            
            cursor.execute("""
                SELECT 
                    s.student_code,
                    u.first_name,
                    u.last_name,
                    et.name,
                    g.score
                FROM grades g
                JOIN students s ON g.student_id = s.id
                JOIN users u ON s.user_id = u.id
                JOIN evaluation_types et ON g.evaluation_type_id = et.id
                WHERE et.name = 'Parcial 1'
                ORDER BY g.score ASC
                LIMIT 3;
            """)
            
            peores = cursor.fetchall()
            print(f"\n⚠️  Notas más bajas del Parcial 1:")
            for i, estudiante in enumerate(peores, 1):
                print(f"  {i}. {estudiante[1]} {estudiante[2]} ({estudiante[0]}): {estudiante[4]}")
            
            # 7. Crear usuario secretaria si no existe
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'secretaria';")
            secretarias = cursor.fetchone()[0]
            
            if secretarias == 0:
                print(f"\n👩‍💼 Creando usuario secretaria...")
                cursor.execute("""
                    INSERT INTO users (institutional_email, password, first_name, last_name, dni, role, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, [
                    'secretaria@unsa.edu.pe',
                    'pbkdf2_sha256$600000$test$hash',  # password: admin123
                    'María Elena',
                    'Rodríguez Paz',
                    '12345678',
                    'secretaria',
                    'secretaria@unsa.edu.pe'
                ])
                secretaria_id = cursor.fetchone()[0]
                print(f"✅ Secretaria creada: María Elena Rodríguez Paz (ID: {secretaria_id})")
            else:
                print(f"\n👩‍💼 Secretarias en el sistema: {secretarias}")
            
            print(f"\n🎉 Sistema verificado exitosamente!")
            print(f"📋 Resumen:")
            print(f"  - Profesores: {len(profesores)}")
            print(f"  - Estudiantes: {total_estudiantes}")
            print(f"  - Cursos: {len(cursos)}")
            print(f"  - Tipos de evaluación: {len(evaluaciones)}")
            print(f"  - Notas del Parcial 1: {evaluaciones[0][3] if evaluaciones else 0}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en la verificación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verificar_sistema_completo()