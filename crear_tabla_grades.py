#!/usr/bin/env python3
"""
Script para crear los tipos de evaluación y preparar el sistema de notas
"""
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def crear_tipos_evaluacion():
    """Crea los tipos de evaluación para el course_group existente"""
    
    try:
        with connection.cursor() as cursor:
            print("🔍 Verificando course_groups existentes...")
            
            # Obtener el course_group existente
            cursor.execute("SELECT id, course_id, group_code FROM course_groups LIMIT 1;")
            course_group = cursor.fetchone()
            
            if not course_group:
                print("❌ No hay course_groups disponibles")
                return False
                
            course_group_id = course_group[0]
            print(f"✅ Course group encontrado: {course_group[2]} (ID: {course_group_id})")
            
            # Verificar si ya existen tipos de evaluación
            cursor.execute("SELECT COUNT(*) FROM evaluation_types WHERE course_group_id = %s;", [course_group_id])
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"⚠️  Ya existen {existing_count} tipos de evaluación para este grupo")
                cursor.execute("SELECT name, weight, max_score FROM evaluation_types WHERE course_group_id = %s;", [course_group_id])
                existing = cursor.fetchall()
                for eval_type in existing:
                    print(f"  - {eval_type[0]}: peso {eval_type[1]}, máximo {eval_type[2]}")
                return True
            
            # Crear los tipos de evaluación
            print("📝 Creando tipos de evaluación...")
            
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
                print(f"✅ Creado: {nombre} (peso: {peso}, máximo: {max_score})")
            
            print("🎉 Tipos de evaluación creados exitosamente!")
            
            # Verificar la creación
            cursor.execute("SELECT id, name, weight, max_score FROM evaluation_types WHERE course_group_id = %s;", [course_group_id])
            tipos_creados = cursor.fetchall()
            
            print(f"\n📋 Tipos de evaluación disponibles ({len(tipos_creados)}):")
            for tipo in tipos_creados:
                print(f"  - ID: {tipo[0]}")
                print(f"    Nombre: {tipo[1]}")
                print(f"    Peso: {tipo[2]}")
                print(f"    Máximo: {tipo[3]}")
                print()
            
            return True
            
    except Exception as e:
        print(f"❌ Error al crear tipos de evaluación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verificar_estudiantes_matriculados():
    """Verifica los estudiantes matriculados en el course_group"""
    
    try:
        with connection.cursor() as cursor:
            print("👥 Verificando estudiantes matriculados...")
            
            cursor.execute("""
                SELECT e.id, s.student_code, u.first_name, u.last_name
                FROM enrollments e
                JOIN students s ON e.student_id = s.id
                JOIN users u ON s.user_id = u.id
                ORDER BY s.student_code
                LIMIT 5;
            """)
            
            estudiantes = cursor.fetchall()
            
            if estudiantes:
                print(f"✅ Primeros 5 estudiantes matriculados:")
                for est in estudiantes:
                    print(f"  - {est[1]}: {est[2]} {est[3]}")
                
                # Contar total
                cursor.execute("SELECT COUNT(*) FROM enrollments;")
                total = cursor.fetchone()[0]
                print(f"📊 Total de estudiantes matriculados: {total}")
            else:
                print("❌ No hay estudiantes matriculados")
                
    except Exception as e:
        print(f"❌ Error al verificar estudiantes: {str(e)}")

if __name__ == "__main__":
    print("🚀 Configurando sistema de notas...")
    print("=" * 50)
    
    if crear_tipos_evaluacion():
        verificar_estudiantes_matriculados()
        print("\n✅ Sistema listo para cargar notas!")
    else:
        print("\n❌ Error en la configuración")