#!/usr/bin/env python3
"""
Demostración del servicio de gestión de contenido del curso
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioContenidoCurso import CourseContentManager
from repositorio.postgres_repository.models import CourseGroup, Teacher


def demo_course_content_service():
    """Demostración práctica del servicio"""
    
    print("=== Demostración del Servicio de Gestión de Contenido ===\n")
    
    content_manager = CourseContentManager()
    
    # 1. Buscar un grupo de curso existente
    print("1. Buscando un grupo de curso para la demostración...")
    
    course_group = CourseGroup.objects.filter(teacher__isnull=False).first()
    
    if not course_group:
        print("   ⚠️  No hay grupos de curso con profesor asignado")
        print("   💡 Ejecute primero los scripts de carga de datos")
        return
    
    print(f"   ✓ Usando grupo: {course_group}")
    print(f"   ✓ Profesor: {course_group.teacher.user.get_full_name()}")
    print(f"   ✓ Progreso actual: {course_group.course_progress_percentage}%")
    print()
    
    # 2. Crear temas de ejemplo para el curso
    print("2. Creando temas de ejemplo para el curso...")
    
    sample_topics = [
        {
            'title': 'Introducción al Curso',
            'description': 'Presentación del curso, objetivos y metodología'
        },
        {
            'title': 'Fundamentos Teóricos',
            'description': 'Conceptos básicos y principios fundamentales'
        },
        {
            'title': 'Práctica Inicial',
            'description': 'Ejercicios básicos y primeras aplicaciones'
        },
        {
            'title': 'Desarrollo Intermedio',
            'description': 'Conceptos intermedios y casos de estudio'
        },
        {
            'title': 'Práctica Avanzada',
            'description': 'Ejercicios complejos y proyectos'
        },
        {
            'title': 'Proyecto Integrador',
            'description': 'Desarrollo de proyecto final'
        },
        {
            'title': 'Evaluación Final',
            'description': 'Presentación y evaluación de proyectos'
        }
    ]
    
    result = content_manager.upload_course_topics(
        course_group_id=str(course_group.id),
        topics=sample_topics,
        teacher_id=str(course_group.teacher.id)
    )
    
    if result['success']:
        print(f"   ✓ {result['message']}")
        print(f"   ✓ Temas creados: {result['topics_created']}")
        
        print("   ✓ Temas con porcentajes automáticos:")
        for topic in result['topics']:
            print(f"      - {topic['title']}: {topic['percentage']}%")
    else:
        print(f"   ✗ Error: {result['error']}")
        return
    
    print()
    
    # 3. Simular progreso del curso
    print("3. Simulando progreso del curso...")
    
    # Actualizar progreso a 40%
    course_group.course_progress_percentage = 40.0
    course_group.classes_attended_by_teacher = 27  # 40% de 68 clases
    course_group.save()
    
    print(f"   ✓ Progreso actualizado a: {course_group.course_progress_percentage}%")
    print(f"   ✓ Clases asistidas: {course_group.classes_attended_by_teacher}")
    
    # Actualizar temas completados automáticamente
    update_result = content_manager.update_topic_completion_by_progress(str(course_group.id))
    
    if update_result['success']:
        print(f"   ✓ {update_result['message']}")
        print(f"   ✓ Temas que deberían estar completados: {update_result['completed_topics']}")
    
    print()
    
    # 4. Mostrar estado actual de los temas
    print("4. Estado actual de los temas...")
    
    topics_result = content_manager.get_course_topics(str(course_group.id))
    
    if topics_result['success']:
        print(f"   ✓ Total de temas: {topics_result['total_topics']}")
        print(f"   ✓ Temas completados: {topics_result['completed_topics']}")
        
        print("   ✓ Estado detallado:")
        for topic in topics_result['topics']:
            status = "✅ COMPLETADO" if topic['completed'] else "⏳ PENDIENTE"
            print(f"      {topic['order']}. {topic['title']} ({topic['percentage']}%) - {status}")
    
    print()
    
    # 5. Agregar un tema adicional
    print("5. Agregando un tema adicional...")
    
    new_topic = {
        'title': 'Revisión y Retroalimentación',
        'description': 'Sesión de revisión de conceptos y retroalimentación'
    }
    
    add_result = content_manager.add_single_topic(
        course_group_id=str(course_group.id),
        topic_data=new_topic,
        teacher_id=str(course_group.teacher.id)
    )
    
    if add_result['success']:
        print(f"   ✓ {add_result['message']}")
        print(f"   ✓ Nuevo tema: {add_result['topic_created']['title']}")
        print(f"   ✓ Total de temas ahora: {add_result['total_topics']}")
        print("   ✓ Porcentajes recalculados automáticamente")
    
    print()
    
    # 6. Mostrar resumen final
    print("6. Resumen final del curso...")
    
    summary = content_manager.get_course_progress_summary(str(course_group.id))
    
    if summary['success']:
        print(f"   📚 Curso: {summary['course_name']}")
        print(f"   👥 Grupo: {summary['group_code']}")
        print(f"   👨‍🏫 Profesor: {summary['teacher']}")
        print(f"   📊 Progreso del curso: {summary['progress_percentage']}%")
        print(f"   📝 Temas completados: {summary['completed_topics']}/{summary['total_topics']}")
        print(f"   📈 Tasa de completado: {summary['completion_rate']:.1f}%")
        print(f"   🎯 Clases asistidas: {summary['classes_attended']}/{summary['total_planned_classes']}")
    
    print()
    
    # 7. Mostrar solo temas completados
    print("7. Temas completados hasta ahora...")
    
    completed_topics = content_manager.get_completed_topics(str(course_group.id))
    
    if completed_topics:
        print(f"   ✅ {len(completed_topics)} temas completados:")
        for topic in completed_topics:
            print(f"      {topic['order']}. {topic['title']} ({topic['percentage']}%)")
    else:
        print("   ℹ️  Aún no hay temas completados")
    
    print()
    
    # 8. Simular más progreso
    print("8. Simulando más progreso (75%)...")
    
    course_group.course_progress_percentage = 75.0
    course_group.classes_attended_by_teacher = 51  # 75% de 68 clases
    course_group.save()
    
    # Actualizar temas completados
    update_result = content_manager.update_topic_completion_by_progress(str(course_group.id))
    
    if update_result['success']:
        print(f"   ✓ Progreso actualizado a: {course_group.course_progress_percentage}%")
        print(f"   ✓ {update_result['message']}")
        print(f"   ✓ Temas completados ahora: {update_result['completed_topics']}")
        
        # Mostrar temas completados actualizados
        completed_topics = content_manager.get_completed_topics(str(course_group.id))
        print(f"   ✅ Temas completados con 75% de progreso:")
        for topic in completed_topics:
            print(f"      {topic['order']}. {topic['title']}")
    
    print("\n=== DEMOSTRACIÓN COMPLETADA ===")
    print("\n💡 El servicio está listo para usar en el sistema!")
    print("   - Los temas se crean con porcentajes automáticos")
    print("   - El progreso se actualiza basado en asistencia docente")
    print("   - Los temas se marcan como completados automáticamente")
    print("   - Se pueden agregar/quitar temas dinámicamente")


if __name__ == '__main__':
    demo_course_content_service()