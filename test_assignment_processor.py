#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del AssignmentProcessor
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioAssignmentProcessor import AssignmentProcessor, AssignmentResult
from servicios.servicioExcelReader import StudentData
from servicios.servicioCourseMapperSimple import CourseMapping
from django.db import connection
import uuid


def get_or_create_test_course():
    """Obtiene o crea un curso de prueba para las pruebas"""
    try:
        with connection.cursor() as cursor:
            # Buscar un curso existente
            cursor.execute("SELECT id, name, code FROM courses LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                return CourseMapping(
                    course_id=result[0],
                    course_name=result[1],
                    course_code=result[2],
                    created=False
                )
            
            # Si no hay cursos, crear uno de prueba
            course_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO courses (id, code, name, credits, theory_hours, practice_hours, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [course_id, "TEST101", "Curso de Prueba", 3, 2, 2, True])
            
            return CourseMapping(
                course_id=course_id,
                course_name="Curso de Prueba",
                course_code="TEST101",
                created=True
            )
            
    except Exception as e:
        print(f"Error obteniendo curso de prueba: {str(e)}")
        return None


def test_assignment_processor():
    """Prueba básica del AssignmentProcessor"""
    print("=== Prueba del AssignmentProcessor ===")
    
    # Crear instancia del procesador
    processor = AssignmentProcessor()
    
    # Datos de prueba
    student_data = StudentData(
        student_code="TEST001",
        email="test001@universidad.edu",
        first_name="Juan",
        last_name="Pérez"
    )
    
    # Buscar un curso existente en la base de datos o crear uno de prueba
    course_mapping = get_or_create_test_course()
    
    if not course_mapping:
        print("❌ No se pudo obtener un curso de prueba")
        return
    
    print(f"Estudiante de prueba: {student_data.student_code} - {student_data.first_name} {student_data.last_name}")
    print(f"Curso de prueba: {course_mapping.course_name} ({course_mapping.course_code})")
    
    try:
        # Intentar procesar la asignación
        result = processor.process_student_assignment(
            student_data.student_code,
            student_data,
            course_mapping
        )
        
        print(f"\nResultado de la asignación:")
        print(f"  - Éxito: {result.success}")
        print(f"  - Asignado: {result.assigned}")
        print(f"  - Omitido: {result.skipped}")
        
        if result.error_message:
            print(f"  - Error: {result.error_message}")
        
        if result.warning_message:
            print(f"  - Advertencia: {result.warning_message}")
        
        if result.student_id:
            print(f"  - ID Estudiante: {result.student_id}")
        
        if result.enrollment_id:
            print(f"  - ID Matrícula: {result.enrollment_id}")
        
        # Intentar la misma asignación otra vez para probar duplicados
        print(f"\n--- Probando detección de duplicados ---")
        result2 = processor.process_student_assignment(
            student_data.student_code,
            student_data,
            course_mapping
        )
        
        print(f"Segunda asignación:")
        print(f"  - Éxito: {result2.success}")
        print(f"  - Asignado: {result2.assigned}")
        print(f"  - Omitido: {result2.skipped}")
        
        if result2.warning_message:
            print(f"  - Advertencia: {result2.warning_message}")
        
        # Obtener estadísticas
        print(f"\n--- Estadísticas ---")
        stats = processor.get_assignment_statistics()
        
        if stats['success']:
            print(f"  - Total matrículas: {stats['total_enrollments']}")
            print(f"  - Estudiantes únicos: {stats['unique_students']}")
            print(f"  - Cursos únicos: {stats['unique_courses']}")
        else:
            print(f"  - Error obteniendo estadísticas: {stats['error']}")
        
        print(f"\n✅ Prueba completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error en la prueba: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_assignment_processor()