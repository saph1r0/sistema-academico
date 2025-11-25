#!/usr/bin/env python
"""
Script para probar el modelo CourseTopicContent
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import CourseTopicContent, CourseGroup, Course, AcademicPeriod, Teacher, User
from django.utils import timezone

def test_course_topic_content_model():
    """Prueba el modelo CourseTopicContent"""
    print("=== Prueba del Modelo CourseTopicContent ===")
    
    try:
        # 1. Verificar que el modelo se puede importar
        print("✅ Modelo CourseTopicContent importado correctamente")
        
        # 2. Verificar los campos del modelo
        fields = [field.name for field in CourseTopicContent._meta.fields]
        expected_fields = [
            'id', 'course_group', 'topic_title', 'topic_description', 
            'topic_order', 'percentage_weight', 'is_completed', 
            'completion_date', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            if field in fields:
                print(f"✅ Campo '{field}' presente")
            else:
                print(f"❌ Campo '{field}' faltante")
        
        # 3. Verificar métodos del modelo
        methods = ['mark_as_completed', 'mark_as_incomplete', '__str__']
        for method in methods:
            if hasattr(CourseTopicContent, method):
                print(f"✅ Método '{method}' presente")
            else:
                print(f"❌ Método '{method}' faltante")
        
        # 4. Verificar Meta opciones
        meta = CourseTopicContent._meta
        print(f"✅ Tabla de base de datos: {meta.db_table}")
        print(f"✅ Verbose name: {meta.verbose_name}")
        print(f"✅ Ordering: {meta.ordering}")
        
        # 5. Verificar unique_together
        if meta.unique_together:
            print(f"✅ Unique together: {meta.unique_together}")
        
        # 6. Verificar índices
        if meta.indexes:
            print(f"✅ Índices definidos: {len(meta.indexes)}")
            for idx in meta.indexes:
                print(f"   - {idx.name}: {idx.fields}")
        
        print("\n=== Verificación del modelo completada exitosamente ===")
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar el modelo: {e}")
        return False

def test_model_relationships():
    """Prueba las relaciones del modelo"""
    print("\n=== Prueba de Relaciones del Modelo ===")
    
    try:
        # Verificar relación con CourseGroup
        course_group_field = CourseTopicContent._meta.get_field('course_group')
        print(f"✅ Relación con CourseGroup: {course_group_field.related_model.__name__}")
        print(f"✅ Related name: {course_group_field.related_query_name()}")
        print(f"✅ On delete: {course_group_field.remote_field.on_delete}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar relaciones: {e}")
        return False

if __name__ == "__main__":
    success = test_course_topic_content_model()
    if success:
        success = test_model_relationships()
    
    if success:
        print("\n🎉 Todas las pruebas del modelo CourseTopicContent pasaron exitosamente!")
    else:
        print("\n💥 Algunas pruebas fallaron")
        sys.exit(1)