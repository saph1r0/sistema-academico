#!/usr/bin/env python
"""
Script simple para verificar el calculador de progreso
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioCalculadorProgreso import ProgressCalculator
from repositorio.postgres_repository.models import CourseGroup


def main():
    """Verificación simple del calculador de progreso"""
    
    print("🔍 Verificando Calculador de Progreso...\n")
    
    try:
        # Crear instancia del calculador
        calculator = ProgressCalculator()
        print("✅ Calculador de progreso creado exitosamente")
        
        # Buscar un curso para testing
        course_groups = list(CourseGroup.objects.filter(teacher__isnull=False))
        
        if not course_groups:
            print("❌ No se encontraron cursos con profesores asignados")
            return
        
        # Tomar el primer curso
        course_group = course_groups[0]
        print(f"📚 Testing con curso: {course_group.course.name} - Grupo {course_group.group_code}")
        print(f"👨‍🏫 Profesor: {course_group.teacher.user.get_full_name()}")
        
        # Test básico de cálculo de progreso
        print("\n🔄 Calculando progreso...")
        result = calculator.calculate_course_progress(str(course_group.id))
        
        if result['success']:
            print("✅ Cálculo de progreso exitoso:")
            print(f"   - Clases asistidas: {result['classes_attended']}")
            print(f"   - Total programadas: {result['total_planned_classes']}")
            print(f"   - Progreso: {result['progress_percentage']}%")
            print(f"   - Temas actualizados: {result['topics_updated']}")
        else:
            print(f"❌ Error en cálculo: {result.get('error', 'Error desconocido')}")
            print(f"   Código de error: {result.get('error_code', 'N/A')}")
        
        # Test de estadísticas
        print("\n📊 Obteniendo estadísticas...")
        stats = calculator.get_progress_statistics(str(course_group.id))
        
        if stats['success']:
            print("✅ Estadísticas obtenidas:")
            print(f"   - Progreso actual: {stats['progress_percentage']}%")
            print(f"   - Total de temas: {stats['topic_statistics']['total_topics']}")
            print(f"   - Temas completados: {stats['topic_statistics']['completed_topics']}")
        else:
            print(f"❌ Error obteniendo estadísticas: {stats.get('error', 'Error desconocido')}")
        
        # Test de progreso esperado vs real
        print("\n⚖️ Comparando progreso esperado vs real...")
        comparison = calculator.get_expected_vs_actual_progress(str(course_group.id))
        
        if comparison['success']:
            print("✅ Comparación exitosa:")
            print(f"   - Progreso esperado: {comparison['expected_progress']}%")
            print(f"   - Progreso real: {comparison['actual_progress']}%")
            print(f"   - Estado: {comparison['status']}")
        else:
            print(f"❌ Error en comparación: {comparison.get('error', 'Error desconocido')}")
        
        print("\n🎉 Verificación completada exitosamente!")
        
    except Exception as e:
        print(f"\n💥 Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()