#!/usr/bin/env python
"""
Test script para verificar el funcionamiento del servicio de cálculo de progreso
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioCalculadorProgreso import ProgressCalculator
from repositorio.postgres_repository.models import (
    CourseGroup, Teacher, TeacherAttendance, CourseTopicContent, Course, User
)
from django.utils import timezone


def test_progress_calculator():
    """Test completo del calculador de progreso"""
    
    print("=== Test del Calculador de Progreso ===\n")
    
    calculator = ProgressCalculator()
    
    # 1. Buscar un curso existente para testing
    print("1. Buscando cursos disponibles...")
    course_groups = CourseGroup.objects.filter(teacher__isnull=False)[:3]
    
    if not course_groups.exists():
        print("❌ No se encontraron cursos con profesores asignados")
        return False
    
    print(f"✅ Encontrados {course_groups.count()} cursos para testing\n")
    
    # 2. Test de cálculo de progreso para cada curso
    for course_group in course_groups:
        print(f"--- Testing curso: {course_group.course.name} - Grupo {course_group.group_code} ---")
        
        # Mostrar estado inicial
        print(f"Estado inicial:")
        print(f"  - Profesor: {course_group.teacher.user.get_full_name()}")
        print(f"  - Clases programadas: {course_group.total_planned_classes}")
        print(f"  - Clases asistidas: {course_group.classes_attended_by_teacher}")
        print(f"  - Progreso actual: {course_group.course_progress_percentage}%")
        
        # Contar temas existentes
        topics_count = CourseTopicContent.objects.filter(course_group=course_group).count()
        completed_topics = CourseTopicContent.objects.filter(
            course_group=course_group, 
            is_completed=True
        ).count()
        print(f"  - Temas: {completed_topics}/{topics_count} completados")
        
        # Test del cálculo de progreso
        print("\n🔄 Calculando progreso...")
        result = calculator.calculate_course_progress(str(course_group.id))
        
        if result['success']:
            print("✅ Cálculo exitoso:")
            print(f"  - Clases asistidas: {result['classes_attended']}")
            print(f"  - Progreso calculado: {result['progress_percentage']}%")
            print(f"  - Temas actualizados: {result['topics_updated']}")
        else:
            print(f"❌ Error en cálculo: {result['error']}")
        
        print()
    
    # 3. Test de estadísticas de progreso
    print("--- Test de Estadísticas de Progreso ---")
    first_course = course_groups.first()
    
    print(f"Obteniendo estadísticas para: {first_course.course.name}")
    stats_result = calculator.get_progress_statistics(str(first_course.id))
    
    if stats_result['success']:
        print("✅ Estadísticas obtenidas:")
        print(f"  - Progreso: {stats_result['progress_percentage']}%")
        print(f"  - Tasa de asistencia: {stats_result['attendance_statistics']['attendance_rate']}%")
        print(f"  - Tasa de completado de temas: {stats_result['topic_statistics']['completion_rate']}%")
    else:
        print(f"❌ Error obteniendo estadísticas: {stats_result['error']}")
    
    print()
    
    # 4. Test de progreso esperado vs real
    print("--- Test de Progreso Esperado vs Real ---")
    
    comparison_result = calculator.get_expected_vs_actual_progress(str(first_course.id))
    
    if comparison_result['success']:
        print("✅ Comparación obtenida:")
        print(f"  - Progreso esperado: {comparison_result['expected_progress']}%")
        print(f"  - Progreso real: {comparison_result['actual_progress']}%")
        print(f"  - Diferencia: {comparison_result['progress_difference']}%")
        print(f"  - Estado: {comparison_result['status']} - {comparison_result['status_message']}")
    else:
        print(f"❌ Error en comparación: {comparison_result['error']}")
    
    print()
    
    # 5. Test de cálculo masivo
    print("--- Test de Cálculo Masivo ---")
    
    if first_course.teacher:
        print(f"Calculando progreso para todos los cursos del profesor: {first_course.teacher.user.get_full_name()}")
        
        mass_results = calculator.calculate_all_courses_progress(str(first_course.teacher.id))
        
        successful = sum(1 for r in mass_results if r.get('success', False))
        total = len(mass_results)
        
        print(f"✅ Cálculo masivo completado: {successful}/{total} cursos procesados exitosamente")
        
        for result in mass_results:
            if result['success']:
                print(f"  - {result['course_name']}: {result['progress_percentage']}%")
    
    print()
    
    # 6. Test de actualización de temas
    print("--- Test de Actualización de Temas ---")
    
    # Simular un progreso específico para testing
    test_progress = 60.0
    print(f"Simulando progreso de {test_progress}% para actualizar temas...")
    
    topics_result = calculator.update_topic_completion_status(str(first_course.id), test_progress)
    
    if topics_result['success']:
        print("✅ Actualización de temas exitosa:")
        print(f"  - Total de temas: {topics_result['total_topics']}")
        print(f"  - Temas completados: {topics_result['completed_topics']}")
        print(f"  - Temas actualizados: {topics_result['topics_updated']}")
    else:
        print(f"❌ Error actualizando temas: {topics_result['error']}")
    
    print("\n=== Test Completado ===")
    return True


def test_edge_cases():
    """Test de casos extremos y validaciones"""
    
    print("\n=== Test de Casos Extremos ===\n")
    
    calculator = ProgressCalculator()
    
    # Test con ID inexistente
    print("1. Test con ID de curso inexistente...")
    result = calculator.calculate_course_progress("00000000-0000-0000-0000-000000000000")
    
    if not result['success'] and result['error_code'] == 'COURSE_GROUP_NOT_FOUND':
        print("✅ Manejo correcto de curso inexistente")
    else:
        print("❌ Error en manejo de curso inexistente")
    
    # Test con curso sin profesor
    print("\n2. Test con curso sin profesor asignado...")
    course_without_teacher = CourseGroup.objects.filter(teacher__isnull=True).first()
    
    if course_without_teacher:
        result = calculator.calculate_course_progress(str(course_without_teacher.id))
        
        if not result['success'] and result['error_code'] == 'NO_TEACHER_ASSIGNED':
            print("✅ Manejo correcto de curso sin profesor")
        else:
            print("❌ Error en manejo de curso sin profesor")
    else:
        print("ℹ️  No hay cursos sin profesor para testing")
    
    print("\n=== Test de Casos Extremos Completado ===")


def show_system_status():
    """Muestra el estado actual del sistema"""
    
    print("\n=== Estado del Sistema ===\n")
    
    # Contar elementos del sistema
    total_courses = CourseGroup.objects.count()
    courses_with_teacher = CourseGroup.objects.filter(teacher__isnull=False).count()
    total_teachers = Teacher.objects.count()
    total_topics = CourseTopicContent.objects.count()
    completed_topics = CourseTopicContent.objects.filter(is_completed=True).count()
    total_attendance = TeacherAttendance.objects.count()
    
    print(f"📊 Estadísticas del Sistema:")
    print(f"  - Total de cursos: {total_courses}")
    print(f"  - Cursos con profesor: {courses_with_teacher}")
    print(f"  - Total de profesores: {total_teachers}")
    print(f"  - Total de temas: {total_topics}")
    print(f"  - Temas completados: {completed_topics}")
    print(f"  - Registros de asistencia: {total_attendance}")
    
    # Mostrar algunos cursos de ejemplo
    print(f"\n📚 Cursos disponibles para testing:")
    sample_courses = CourseGroup.objects.filter(teacher__isnull=False)[:5]
    
    for course in sample_courses:
        print(f"  - {course.course.name} (Grupo {course.group_code})")
        print(f"    Profesor: {course.teacher.user.get_full_name()}")
        print(f"    Progreso: {course.course_progress_percentage}%")
        print(f"    Clases: {course.classes_attended_by_teacher}/{course.total_planned_classes}")
        print()


if __name__ == "__main__":
    try:
        print("🚀 Iniciando tests del Calculador de Progreso...\n")
        
        # Mostrar estado del sistema
        show_system_status()
        
        # Ejecutar tests principales
        success = test_progress_calculator()
        
        # Ejecutar tests de casos extremos
        test_edge_cases()
        
        if success:
            print("\n🎉 Todos los tests completados exitosamente!")
        else:
            print("\n⚠️  Algunos tests fallaron. Revisar la implementación.")
            
    except Exception as e:
        print(f"\n💥 Error ejecutando tests: {str(e)}")
        import traceback
        traceback.print_exc()