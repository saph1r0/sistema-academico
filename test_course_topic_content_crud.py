#!/usr/bin/env python
"""
Script para probar operaciones CRUD del modelo CourseTopicContent
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import CourseTopicContent, CourseGroup, Course, AcademicPeriod, Teacher, User
from django.utils import timezone
from decimal import Decimal

def test_crud_operations():
    """Prueba operaciones CRUD básicas"""
    print("=== Prueba de Operaciones CRUD ===")
    
    try:
        # 1. Verificar que podemos consultar el modelo (debería estar vacío)
        count = CourseTopicContent.objects.count()
        print(f"✅ Consulta inicial: {count} registros")
        
        # 2. Buscar un CourseGroup existente para usar en las pruebas
        course_group = CourseGroup.objects.first()
        if not course_group:
            print("❌ No hay CourseGroups disponibles para la prueba")
            return False
        
        print(f"✅ Usando CourseGroup: {course_group}")
        
        # 3. Crear un registro de prueba
        topic_content = CourseTopicContent.objects.create(
            course_group=course_group,
            topic_title="Introducción a la Programación",
            topic_description="Conceptos básicos de programación y algoritmos",
            topic_order=1,
            percentage_weight=10.0
        )
        
        print(f"✅ Registro creado: {topic_content}")
        print(f"   - ID: {topic_content.id}")
        print(f"   - Título: {topic_content.topic_title}")
        print(f"   - Orden: {topic_content.topic_order}")
        print(f"   - Peso: {topic_content.percentage_weight}%")
        print(f"   - Completado: {topic_content.is_completed}")
        
        # 4. Leer el registro
        retrieved = CourseTopicContent.objects.get(id=topic_content.id)
        print(f"✅ Registro leído: {retrieved.topic_title}")
        
        # 5. Actualizar el registro
        retrieved.topic_description = "Descripción actualizada"
        retrieved.percentage_weight = 15.0
        retrieved.save()
        print("✅ Registro actualizado")
        
        # 6. Probar el método mark_as_completed
        retrieved.mark_as_completed()
        print(f"✅ Marcado como completado: {retrieved.is_completed}")
        print(f"   - Fecha de completado: {retrieved.completion_date}")
        
        # 7. Probar el método mark_as_incomplete
        retrieved.mark_as_incomplete()
        print(f"✅ Marcado como incompleto: {retrieved.is_completed}")
        print(f"   - Fecha de completado: {retrieved.completion_date}")
        
        # 8. Crear múltiples registros para probar unique_together
        topics = [
            ("Variables y Tipos de Datos", 2, 15.0),
            ("Estructuras de Control", 3, 20.0),
            ("Funciones", 4, 25.0),
            ("Arrays y Listas", 5, 30.0)
        ]
        
        for title, order, weight in topics:
            CourseTopicContent.objects.create(
                course_group=course_group,
                topic_title=title,
                topic_order=order,
                percentage_weight=weight
            )
        
        print(f"✅ Creados {len(topics)} registros adicionales")
        
        # 9. Probar consultas
        all_topics = CourseTopicContent.objects.filter(course_group=course_group).order_by('topic_order')
        print(f"✅ Total de temas para el curso: {all_topics.count()}")
        
        for topic in all_topics:
            print(f"   - {topic.topic_order}. {topic.topic_title} ({topic.percentage_weight}%)")
        
        # 10. Probar relación inversa desde CourseGroup
        course_topics = course_group.topic_contents.all()
        print(f"✅ Temas desde CourseGroup: {course_topics.count()}")
        
        # 11. Limpiar datos de prueba
        CourseTopicContent.objects.filter(course_group=course_group).delete()
        print("✅ Datos de prueba eliminados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones CRUD: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_constraints():
    """Prueba las restricciones del modelo"""
    print("\n=== Prueba de Restricciones del Modelo ===")
    
    try:
        course_group = CourseGroup.objects.first()
        if not course_group:
            print("❌ No hay CourseGroups disponibles")
            return False
        
        # Crear primer registro
        topic1 = CourseTopicContent.objects.create(
            course_group=course_group,
            topic_title="Tema 1",
            topic_order=1,
            percentage_weight=50.0
        )
        print("✅ Primer registro creado")
        
        # Intentar crear registro con mismo course_group y topic_order (debería fallar)
        try:
            CourseTopicContent.objects.create(
                course_group=course_group,
                topic_title="Tema 1 Duplicado",
                topic_order=1,  # Mismo orden
                percentage_weight=50.0
            )
            print("❌ No se detectó violación de unique_together")
            return False
        except Exception:
            print("✅ Restricción unique_together funcionando correctamente")
        
        # Limpiar
        topic1.delete()
        print("✅ Datos de prueba eliminados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de restricciones: {e}")
        return False

if __name__ == "__main__":
    success = test_crud_operations()
    if success:
        success = test_model_constraints()
    
    if success:
        print("\n🎉 Todas las pruebas CRUD pasaron exitosamente!")
        print("\n=== Resumen de Funcionalidades Implementadas ===")
        print("✅ Modelo CourseTopicContent creado")
        print("✅ Relación con CourseGroup establecida")
        print("✅ Campos requeridos implementados:")
        print("   - topic_title: Título del tema")
        print("   - topic_description: Descripción del tema")
        print("   - topic_order: Orden del tema")
        print("   - percentage_weight: Peso porcentual")
        print("   - is_completed: Estado completado")
        print("   - completion_date: Fecha de completado")
        print("✅ Métodos implementados:")
        print("   - mark_as_completed(): Marca tema como completado")
        print("   - mark_as_incomplete(): Marca tema como incompleto")
        print("✅ Restricciones implementadas:")
        print("   - unique_together: (course_group, topic_order)")
        print("✅ Índices creados para optimización")
    else:
        print("\n💥 Algunas pruebas fallaron")
        sys.exit(1)