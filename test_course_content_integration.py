#!/usr/bin/env python3
"""
Test de integración para verificar el servicio con datos existentes
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioContenidoCurso import CourseContentManager
from repositorio.postgres_repository.models import CourseGroup, Teacher


def test_with_existing_data():
    """Test con datos existentes en la base de datos"""
    
    print("=== Test de Integración con Datos Existentes ===\n")
    
    content_manager = CourseContentManager()
    
    # 1. Buscar un CourseGroup existente
    print("1. Buscando grupos de curso existentes...")
    
    course_groups = list(CourseGroup.objects.all()[:3])  # Tomar los primeros 3
    
    if not course_groups:
        print("   ⚠️  No hay grupos de curso en la base de datos")
        print("   💡 Ejecute primero los scripts de carga de datos")
        return
    
    for group in course_groups:
        print(f"   ✓ Encontrado: {group}")
        print(f"     - Profesor: {group.teacher.user.get_full_name() if group.teacher else 'Sin asignar'}")
        print(f"     - Progreso: {group.course_progress_percentage}%")
        print(f"     - Clases: {group.classes_attended_by_teacher}/{group.total_planned_classes}")
    
    print()
    
    # 2. Test con el primer grupo encontrado
    test_group = course_groups[0]
    print(f"2. Probando con el grupo: {test_group}")
    
    # Obtener temas existentes
    existing_topics = content_manager.get_course_topics(str(test_group.id))
    
    if existing_topics['success']:
        print(f"   ✓ Temas existentes: {existing_topics['total_topics']}")
        print(f"   ✓ Temas completados: {existing_topics['completed_topics']}")
        
        if existing_topics['total_topics'] > 0:
            print("   ✓ Algunos temas encontrados:")
            for topic in existing_topics['topics'][:3]:
                status = "COMPLETADO" if topic['completed'] else "PENDIENTE"
                print(f"      - {topic['title']} ({topic['percentage']}%) - {status}")
        else:
            print("   ℹ️  No hay temas definidos para este curso")
    else:
        print(f"   ✗ Error: {existing_topics['error']}")
    
    print()
    
    # 3. Test de resumen de progreso
    print("3. Probando resumen de progreso...")
    
    summary = content_manager.get_course_progress_summary(str(test_group.id))
    
    if summary['success']:
        print(f"   ✓ Curso: {summary['course_name']}")
        print(f"   ✓ Grupo: {summary['group_code']}")
        print(f"   ✓ Profesor: {summary['teacher']}")
        print(f"   ✓ Progreso: {summary['progress_percentage']}%")
        print(f"   ✓ Temas: {summary['completed_topics']}/{summary['total_topics']}")
        print(f"   ✓ Asistencia: {summary['classes_attended']}/{summary['total_planned_classes']}")
    else:
        print(f"   ✗ Error: {summary['error']}")
    
    print()
    
    # 4. Test de cálculo de porcentajes
    print("4. Probando cálculo de porcentajes...")
    
    test_cases = [5, 8, 10, 12, 15]
    
    for num_topics in test_cases:
        percentages = content_manager.calculate_topic_percentages(num_topics)
        total = sum(percentages)
        print(f"   ✓ {num_topics} temas: suma = {total}% (cada tema ≈ {100/num_topics:.2f}%)")
    
    print()
    
    # 5. Test de actualización de progreso
    print("5. Probando actualización de progreso...")
    
    if existing_topics['success'] and existing_topics['total_topics'] > 0:
        update_result = content_manager.update_topic_completion_by_progress(str(test_group.id))
        
        if update_result['success']:
            print(f"   ✓ {update_result['message']}")
            print(f"   ✓ Progreso actual: {update_result['current_progress']}%")
            print(f"   ✓ Temas completados: {update_result['completed_topics']}/{update_result['total_topics']}")
        else:
            print(f"   ✗ Error: {update_result['error']}")
    else:
        print("   ℹ️  No hay temas para actualizar")
    
    print()
    
    # 6. Mostrar estadísticas generales
    print("6. Estadísticas generales del sistema...")
    
    total_groups = CourseGroup.objects.count()
    groups_with_teacher = CourseGroup.objects.filter(teacher__isnull=False).count()
    groups_with_progress = CourseGroup.objects.filter(course_progress_percentage__gt=0).count()
    
    print(f"   ✓ Total de grupos de curso: {total_groups}")
    print(f"   ✓ Grupos con profesor asignado: {groups_with_teacher}")
    print(f"   ✓ Grupos con progreso > 0%: {groups_with_progress}")
    
    # Contar temas por grupo
    from repositorio.postgres_repository.models import CourseTopicContent
    
    groups_with_topics = CourseTopicContent.objects.values('course_group').distinct().count()
    total_topics = CourseTopicContent.objects.count()
    completed_topics = CourseTopicContent.objects.filter(is_completed=True).count()
    
    print(f"   ✓ Grupos con temas definidos: {groups_with_topics}")
    print(f"   ✓ Total de temas en el sistema: {total_topics}")
    print(f"   ✓ Temas completados: {completed_topics}")
    
    if total_topics > 0:
        completion_rate = (completed_topics / total_topics) * 100
        print(f"   ✓ Tasa de completado global: {completion_rate:.1f}%")
    
    print("\n=== TEST DE INTEGRACIÓN COMPLETADO ===")


if __name__ == '__main__':
    test_with_existing_data()