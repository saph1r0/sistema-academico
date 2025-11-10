#!/usr/bin/env python3
"""
Script de prueba para el CourseMapper
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioCourseMapper import CourseMapper


def test_course_mapper():
    """Prueba básica del CourseMapper"""
    print("🧪 Probando CourseMapper...")
    
    mapper = CourseMapper()
    
    # Probar extracción de nombres de archivos
    test_files = [
        'alumnos_isII(1).xlsx',
        'alumnos_ada(1).xlsx', 
        'alumnos_mac(1).xlsx',
        'alumnos_trabajo_interdiciplinarII (1).xlsx',
        'alumnos_trabajo_interdiciplinarIII.xlsx',
        'alumnos_nuevo_curso.xlsx'
    ]
    
    print("\n📋 Probando extracción de nombres:")
    for filename in test_files:
        course_name = mapper.extract_course_name(filename)
        print(f"  {filename} -> {course_name}")
    
    # Probar normalización
    print("\n🔧 Probando normalización:")
    test_names = [
        'Matemática Aplicada a la Computación',
        'INGENIERÍA DE SOFTWARE II',
        'análisis  y   diseño de algoritmos',
        'Trabajo Interdisciplinario III'
    ]
    
    for name in test_names:
        normalized = mapper._normalize_course_name(name)
        print(f"  '{name}' -> '{normalized}'")
    
    print("\n✅ Pruebas básicas completadas")


if __name__ == '__main__':
    test_course_mapper()