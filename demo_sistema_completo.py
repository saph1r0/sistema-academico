#!/usr/bin/env python3
"""
Demostración completa del sistema de importación de Excel
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def demo_sistema_completo():
    """Demostración paso a paso del sistema completo"""
    
    print("🎯 DEMOSTRACIÓN DEL SISTEMA DE IMPORTACIÓN DE EXCEL")
    print("=" * 60)
    
    print("\n📋 PASO 1: Cargar estudiantes desde bdtotall.xlsx")
    print("-" * 50)
    print("Comando: poetry run python manage.py load_students")
    print("Descripción: Carga todos los estudiantes del archivo Excel global")
    print("Resultado esperado: Creación de usuarios y registros de estudiantes")
    
    print("\n📚 PASO 2: Asignar estudiantes a cursos")
    print("-" * 50)
    print("Comando: poetry run python manage.py assign_courses")
    print("Descripción: Procesa archivos Excel individuales y crea matrículas")
    print("Resultado esperado: Estudiantes asignados a sus respectivos cursos")
    
    print("\n📖 PASO 3: Acceder al sílabo del profesor")
    print("-" * 50)
    print("URL: http://localhost:8000/profesor/silabo/")
    print("Descripción: Vista mejorada del sílabo con datos reales")
    print("Funcionalidades:")
    print("  • Ver progreso de unidades del curso")
    print("  • Marcar temas como completados")
    print("  • Estadísticas automáticas de avance")
    print("  • Cronograma del período académico")
    
    print("\n🔧 COMANDOS DISPONIBLES:")
    print("=" * 60)
    
    comandos = [
        {
            'comando': 'poetry run python manage.py load_students',
            'descripcion': 'Carga estudiantes desde bdtotall.xlsx',
            'opciones': [
                '--file RUTA: Especificar archivo diferente',
                '--dry-run: Validar sin hacer cambios'
            ]
        },
        {
            'comando': 'poetry run python manage.py assign_courses',
            'descripcion': 'Asigna estudiantes a cursos desde archivos Excel',
            'opciones': [
                '--folder CARPETA: Especificar carpeta diferente',
                '--file ARCHIVO: Procesar archivo específico',
                '--dry-run: Validar sin hacer cambios'
            ]
        }
    ]
    
    for cmd in comandos:
        print(f"\n📌 {cmd['comando']}")
        print(f"   {cmd['descripcion']}")
        for opcion in cmd['opciones']:
            print(f"   • {opcion}")
    
    print("\n📊 ESTADÍSTICAS ACTUALES DEL SISTEMA:")
    print("=" * 60)
    mostrar_estadisticas()
    
    print("\n🎯 PRÓXIMOS PASOS RECOMENDADOS:")
    print("=" * 60)
    print("1. Ejecutar carga de estudiantes si no se ha hecho:")
    print("   poetry run python manage.py load_students --dry-run")
    print("   poetry run python manage.py load_students")
    print()
    print("2. Asignar estudiantes a cursos:")
    print("   poetry run python manage.py assign_courses --dry-run")
    print("   poetry run python manage.py assign_courses")
    print()
    print("3. Iniciar servidor Django y probar sílabo:")
    print("   poetry run python manage.py runserver")
    print("   Visitar: http://localhost:8000/profesor/silabo/")
    print()
    print("4. Crear usuario profesor si es necesario:")
    print("   poetry run python manage.py createsuperuser")

def mostrar_estadisticas():
    """Muestra estadísticas actuales del sistema"""
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Contar usuarios por rol
            cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role;")
            users_by_role = dict(cursor.fetchall())
            
            # Contar estudiantes
            cursor.execute("SELECT COUNT(*) FROM students;")
            total_students = cursor.fetchone()[0]
            
            # Contar cursos
            cursor.execute("SELECT COUNT(*) FROM courses;")
            total_courses = cursor.fetchone()[0]
            
            # Contar matrículas
            cursor.execute("SELECT COUNT(*) FROM enrollments;")
            total_enrollments = cursor.fetchone()[0]
            
            # Contar sílabos
            cursor.execute("SELECT COUNT(*) FROM syllabi;")
            total_syllabi = cursor.fetchone()[0]
            
            print(f"👥 Usuarios por rol:")
            for role, count in users_by_role.items():
                print(f"   • {role}: {count}")
            
            print(f"\n📊 Resumen:")
            print(f"   • Estudiantes: {total_students}")
            print(f"   • Cursos: {total_courses}")
            print(f"   • Matrículas: {total_enrollments}")
            print(f"   • Sílabos: {total_syllabi}")
            
            # Verificar si hay datos para procesar
            if total_students > 0 and total_courses > 0:
                print(f"\n✅ Sistema listo para usar")
            elif total_students == 0:
                print(f"\n⚠️  Ejecutar carga de estudiantes primero")
            elif total_courses == 0:
                print(f"\n⚠️  Ejecutar asignación de cursos primero")
    
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")

if __name__ == "__main__":
    demo_sistema_completo()