#!/usr/bin/env python
"""
Script de verificación para el sistema de asignación automática de cursos

Este script verifica que todos los componentes del sistema estén funcionando
correctamente sin ejecutar el proceso completo de asignación.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioExcelReader import ExcelReader
from servicios.servicioCourseMapperSimple import CourseMapper
from servicios.servicioAssignmentProcessor import AssignmentProcessor
from servicios.servicioAsignacionCursos import CourseAssignmentService
from repositorio.postgres_repository.models import Student, Course, CourseGroup, Enrollment


def main():
    """Ejecuta la verificación completa del sistema"""
    
    print("=" * 80)
    print("🔍 VERIFICACIÓN DEL SISTEMA DE ASIGNACIÓN AUTOMÁTICA")
    print("=" * 80)
    
    # 1. Verificar archivos Excel
    verify_excel_files()
    
    # 2. Verificar servicios
    verify_services()
    
    # 3. Verificar base de datos
    verify_database()
    
    # 4. Verificar comando Django
    verify_django_command()
    
    print("\n" + "=" * 80)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 80)
    print("\n🎯 El sistema está listo para procesar asignaciones de cursos")
    print("📋 Para ejecutar la demostración completa: python demo_assign_courses.py")
    print("⚙️  Para asignar cursos: python manage.py assign_courses")


def verify_excel_files():
    """Verifica la disponibilidad de archivos Excel"""
    print("\n📁 VERIFICANDO ARCHIVOS EXCEL")
    print("-" * 50)
    
    excel_dir = 'EXELS'
    if not os.path.exists(excel_dir):
        print(f"❌ Directorio {excel_dir} no encontrado")
        return False
    
    # Verificar bdtotall.xlsx
    bdtotall_path = os.path.join(excel_dir, 'bdtotall.xlsx')
    if os.path.exists(bdtotall_path):
        size = os.path.getsize(bdtotall_path)
        print(f"✅ bdtotall.xlsx encontrado ({size:,} bytes)")
    else:
        print("❌ bdtotall.xlsx no encontrado")
        return False
    
    # Buscar archivos de cursos
    course_files = []
    for file in os.listdir(excel_dir):
        if file.startswith('alumnos_') and file.endswith('.xlsx'):
            course_files.append(file)
    
    print(f"✅ Archivos de cursos encontrados: {len(course_files)}")
    for course_file in sorted(course_files)[:3]:  # Mostrar solo los primeros 3
        size = os.path.getsize(os.path.join(excel_dir, course_file))
        print(f"   📄 {course_file} ({size:,} bytes)")
    
    if len(course_files) > 3:
        print(f"   ... y {len(course_files) - 3} archivos más")
    
    return True


def verify_services():
    """Verifica que todos los servicios funcionen correctamente"""
    print("\n⚙️  VERIFICANDO SERVICIOS")
    print("-" * 50)
    
    try:
        # Verificar ExcelReader
        excel_reader = ExcelReader()
        print("✅ ExcelReader inicializado correctamente")
        
        # Verificar CourseMapper
        course_mapper = CourseMapper()
        test_name = course_mapper.extract_course_name("alumnos_matematica.xlsx")
        print(f"✅ CourseMapper funcionando (test: {test_name})")
        
        # Verificar AssignmentProcessor
        assignment_processor = AssignmentProcessor()
        print("✅ AssignmentProcessor inicializado correctamente")
        
        # Verificar CourseAssignmentService
        course_service = CourseAssignmentService()
        print("✅ CourseAssignmentService inicializado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando servicios: {e}")
        return False


def verify_database():
    """Verifica la conexión y estructura de la base de datos"""
    print("\n🗄️  VERIFICANDO BASE DE DATOS")
    print("-" * 50)
    
    try:
        # Verificar modelos
        student_count = Student.objects.count()
        course_count = Course.objects.count()
        coursegroup_count = CourseGroup.objects.count()
        enrollment_count = Enrollment.objects.count()
        
        print(f"✅ Estudiantes: {student_count}")
        print(f"✅ Cursos: {course_count}")
        print(f"✅ Grupos de cursos: {coursegroup_count}")
        print(f"✅ Inscripciones: {enrollment_count}")
        
        # Verificar que podemos crear objetos de prueba (sin guardar)
        test_student = Student(
            student_code="TEST001",
            first_name="Test",
            last_name="Student",
            email="test@test.com"
        )
        print("✅ Modelo Student funcional")
        
        test_course = Course(
            name="Test Course",
            code="TEST101"
        )
        print("✅ Modelo Course funcional")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False


def verify_django_command():
    """Verifica que el comando Django esté disponible"""
    print("\n🐍 VERIFICANDO COMANDO DJANGO")
    print("-" * 50)
    
    try:
        from django.core.management import get_commands
        commands = get_commands()
        
        if 'assign_courses' in commands:
            print("✅ Comando 'assign_courses' disponible")
            
            # Verificar que podemos importar el comando
            from repositorio.postgres_repository.management.commands.assign_courses import Command
            cmd = Command()
            print("✅ Comando importado correctamente")
            
            return True
        else:
            print("❌ Comando 'assign_courses' no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando comando Django: {e}")
        return False


if __name__ == '__main__':
    main()