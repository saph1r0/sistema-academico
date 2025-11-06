#!/usr/bin/env python
"""
Script de demostración completo para el sistema de asignación automática de cursos

Este script demuestra el proceso completo de asignación de estudiantes a cursos
desde archivos Excel, incluyendo verificación de resultados en la base de datos.

Uso:
    python demo_assign_courses.py

Requisitos:
    - Archivo bdtotall.xlsx con todos los estudiantes
    - Archivos alumnos_*.xlsx con listas de estudiantes por curso
    - Base de datos Django configurada correctamente
"""

import os
import subprocess
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import Student, Course, Enrollment


def main():
    """Ejecuta la demostración completa del sistema de asignación de cursos"""
    
    print("=" * 80)
    print("🚀 DEMOSTRACIÓN COMPLETA: SISTEMA DE ASIGNACIÓN AUTOMÁTICA DE CURSOS")
    print("=" * 80)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto Django")
        sys.exit(1)
    
    # Verificar que existe el directorio EXELS
    excel_dir = 'EXELS'
    if not os.path.exists(excel_dir):
        print(f"❌ Error: Directorio {excel_dir} no encontrado")
        sys.exit(1)
    
    print(f"📁 Directorio de archivos Excel: {os.path.abspath(excel_dir)}")
    
    # Mostrar estado inicial de la base de datos
    show_database_status("ESTADO INICIAL")
    
    # Listar archivos disponibles
    print("\n📋 Archivos Excel disponibles:")
    excel_files = []
    for file in os.listdir(excel_dir):
        if file.endswith('.xlsx'):
            excel_files.append(file)
            print(f"   📄 {file}")
    
    if not excel_files:
        print("   ⚠️  No se encontraron archivos Excel")
        return
    
    # Verificar archivos requeridos
    bdtotall_exists = 'bdtotall.xlsx' in excel_files
    course_files = [f for f in excel_files if f.startswith('alumnos_')]
    
    print(f"\n✅ Archivo principal (bdtotall.xlsx): {'Encontrado' if bdtotall_exists else '❌ No encontrado'}")
    print(f"✅ Archivos de cursos (alumnos_*.xlsx): {len(course_files)} encontrados")
    
    if not bdtotall_exists:
        print("❌ Error: Se requiere el archivo bdtotall.xlsx para continuar")
        return
    
    # Mostrar menú de opciones
    show_demo_menu(excel_dir, course_files)
    
    # Mostrar resumen final
    show_final_summary()


def show_database_status(title: str):
    """Muestra el estado actual de la base de datos"""
    print(f"\n📊 {title}")
    print("-" * 60)
    
    try:
        # Contar estudiantes
        student_count = Student.objects.count()
        print(f"👥 Estudiantes en base de datos: {student_count}")
        
        # Contar cursos
        course_count = Course.objects.count()
        print(f"📚 Cursos en base de datos: {course_count}")
        
        # Contar inscripciones
        enrollment_count = Enrollment.objects.count()
        print(f"📝 Inscripciones totales: {enrollment_count}")
        
        # Mostrar algunos cursos si existen
        if course_count > 0:
            print("\n📖 Cursos existentes:")
            for course in Course.objects.all()[:5]:
                # Usar course_group en lugar de course para las inscripciones
                enrollments = Enrollment.objects.filter(course_group__course=course).count()
                print(f"   • {course.name} (ID: {course.id}) - {enrollments} estudiantes")
            
            if course_count > 5:
                print(f"   ... y {course_count - 5} cursos más")
        
    except Exception as e:
        print(f"❌ Error consultando base de datos: {e}")


def show_demo_menu(excel_dir: str, course_files: list):
    """Muestra el menú principal de la demostración"""
    print(f"\n🎯 OPCIONES DE DEMOSTRACIÓN")
    print("=" * 60)
    
    options = [
        "1. Ejecutar asignación completa (recomendado)",
        "2. Ejecutar con logging detallado",
        "3. Solo mostrar ayuda del comando",
        "4. Verificar archivos Excel sin procesar",
        "5. Salir"
    ]
    
    for option in options:
        print(f"   {option}")
    
    while True:
        try:
            choice = input(f"\nSelecciona una opción (1-5): ").strip()
            
            if choice == '1':
                run_complete_assignment_demo(excel_dir)
                break
            elif choice == '2':
                run_detailed_logging_demo(excel_dir)
                break
            elif choice == '3':
                show_command_help()
                break
            elif choice == '4':
                verify_excel_files_only(excel_dir, course_files)
                break
            elif choice == '5':
                print("👋 Saliendo de la demostración...")
                return
            else:
                print("❌ Opción inválida. Por favor selecciona 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Saliendo...")
            return


def run_complete_assignment_demo(excel_dir: str):
    """Ejecuta la demostración completa con verificación de resultados"""
    print(f"\n🚀 EJECUTANDO DEMOSTRACIÓN COMPLETA")
    print("=" * 60)
    
    # Ejecutar comando de asignación
    cmd = ['python', 'manage.py', 'assign_courses', '--directory', excel_dir, '--verbose']
    
    print(f"Ejecutando: {' '.join(cmd)}")
    print("-" * 40)
    
    try:
        # Usar poetry si está disponible
        if os.path.exists('pyproject.toml'):
            full_cmd = ['poetry', 'run'] + cmd
        else:
            full_cmd = cmd
        
        result = subprocess.run(full_cmd, capture_output=False, text=True)
        
        print("-" * 40)
        if result.returncode == 0:
            print("✅ Comando ejecutado exitosamente")
            
            # Mostrar estado final de la base de datos
            show_database_status("ESTADO DESPUÉS DE LA ASIGNACIÓN")
            
            # Verificar resultados específicos
            verify_assignment_results()
            
        else:
            print(f"⚠️  Comando terminó con código: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
    
    input("\nPresiona Enter para continuar...")


def run_detailed_logging_demo(excel_dir: str):
    """Ejecuta la demostración con logging detallado"""
    print(f"\n🔍 EJECUTANDO CON LOGGING DETALLADO")
    print("=" * 60)
    
    cmd = ['python', 'manage.py', 'assign_courses', '--directory', excel_dir, '--verbose', '--log-level', 'DEBUG']
    
    print(f"Ejecutando: {' '.join(cmd)}")
    print("-" * 40)
    
    try:
        if os.path.exists('pyproject.toml'):
            full_cmd = ['poetry', 'run'] + cmd
        else:
            full_cmd = cmd
        
        result = subprocess.run(full_cmd, capture_output=False, text=True)
        
        print("-" * 40)
        if result.returncode == 0:
            print("✅ Comando ejecutado exitosamente")
        else:
            print(f"⚠️  Comando terminó con código: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
    
    input("\nPresiona Enter para continuar...")


def show_command_help():
    """Muestra la ayuda del comando"""
    print(f"\n📖 AYUDA DEL COMANDO")
    print("=" * 60)
    
    cmd = ['python', 'manage.py', 'help', 'assign_courses']
    
    try:
        if os.path.exists('pyproject.toml'):
            full_cmd = ['poetry', 'run'] + cmd
        else:
            full_cmd = cmd
        
        subprocess.run(full_cmd, capture_output=False, text=True)
        
    except Exception as e:
        print(f"❌ Error mostrando ayuda: {e}")
    
    input("\nPresiona Enter para continuar...")


def verify_excel_files_only(excel_dir: str, course_files: list):
    """Verifica los archivos Excel sin procesarlos"""
    print(f"\n🔍 VERIFICACIÓN DE ARCHIVOS EXCEL")
    print("=" * 60)
    
    # Verificar bdtotall.xlsx
    bdtotall_path = os.path.join(excel_dir, 'bdtotall.xlsx')
    if os.path.exists(bdtotall_path):
        size = os.path.getsize(bdtotall_path)
        print(f"✅ bdtotall.xlsx: {size:,} bytes")
    else:
        print("❌ bdtotall.xlsx: No encontrado")
    
    # Verificar archivos de cursos
    print(f"\n📚 Archivos de cursos encontrados: {len(course_files)}")
    for course_file in sorted(course_files):
        file_path = os.path.join(excel_dir, course_file)
        size = os.path.getsize(file_path)
        course_name = course_file.replace('alumnos_', '').replace('.xlsx', '').replace('(1)', '').strip()
        print(f"   📄 {course_file}")
        print(f"      Curso extraído: {course_name}")
        print(f"      Tamaño: {size:,} bytes")
    
    if not course_files:
        print("   ⚠️  No se encontraron archivos alumnos_*.xlsx")
    
    input("\nPresiona Enter para continuar...")


def verify_assignment_results():
    """Verifica los resultados de la asignación en la base de datos"""
    print(f"\n🔍 VERIFICACIÓN DE RESULTADOS")
    print("=" * 60)
    
    try:
        # Obtener estadísticas detalladas usando course_group
        courses_with_students = Course.objects.filter(coursegroup__enrollment__isnull=False).distinct()
        
        print(f"📚 Cursos con estudiantes asignados: {courses_with_students.count()}")
        
        for course in courses_with_students:
            # Contar inscripciones a través de course_group
            enrollment_count = Enrollment.objects.filter(course_group__course=course).count()
            print(f"   • {course.name}: {enrollment_count} estudiantes")
            
            # Mostrar algunos estudiantes de ejemplo
            sample_enrollments = Enrollment.objects.filter(course_group__course=course)[:3]
            for enrollment in sample_enrollments:
                student = enrollment.student
                print(f"     - {student.first_name} {student.last_name} ({student.student_code})")
            
            if enrollment_count > 3:
                print(f"     ... y {enrollment_count - 3} estudiantes más")
        
        # Verificar duplicados usando course_group
        from django.db.models import Count
        duplicates = Enrollment.objects.values('student', 'course_group').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            print(f"\n⚠️  Duplicados encontrados: {duplicates.count()}")
        else:
            print(f"\n✅ No se encontraron duplicados")
        
    except Exception as e:
        print(f"❌ Error verificando resultados: {e}")


def show_final_summary():
    """Muestra el resumen final de la demostración"""
    print("\n" + "=" * 80)
    print("📚 RESUMEN DEL SISTEMA DE ASIGNACIÓN AUTOMÁTICA")
    print("=" * 80)
    
    print("""
🎯 FUNCIONALIDADES DEMOSTRADAS:
   ✅ Lectura automática de archivos Excel
   ✅ Extracción de nombres de cursos desde nombres de archivos
   ✅ Creación automática de cursos en base de datos
   ✅ Asignación de estudiantes evitando duplicados
   ✅ Generación de reportes detallados
   ✅ Manejo robusto de errores
   ✅ Verificación de resultados en base de datos

🔍 ESTRUCTURA DE ARCHIVOS REQUERIDA:
   📁 EXELS/
   ├── 📄 bdtotall.xlsx          (archivo principal con todos los estudiantes)
   ├── 📄 alumnos_curso1.xlsx    (estudiantes del curso 1)
   ├── 📄 alumnos_curso2.xlsx    (estudiantes del curso 2)
   └── 📄 alumnos_*.xlsx         (más archivos de cursos)

⚙️  COMANDOS PRINCIPALES:
   # Ejecución básica
   python manage.py assign_courses
   
   # Con directorio específico
   python manage.py assign_courses --directory /path/to/excel
   
   # Con logging detallado
   python manage.py assign_courses --verbose --log-level DEBUG
   
   # Solo errores críticos
   python manage.py assign_courses --log-level ERROR

🚀 INTEGRACIÓN EN PRODUCCIÓN:
   • Agregar al crontab para ejecución automática
   • Usar con scripts de backup antes de procesar
   • Integrar con sistema de notificaciones
   • Configurar logging en archivos para auditoría
    """)


if __name__ == '__main__':
    main()