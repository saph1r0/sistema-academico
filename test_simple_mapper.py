#!/usr/bin/env python3
"""
Script de prueba simple para el CourseMapper sin Django
"""
import os
import sys

# Agregar el directorio actual al path
sys.path.append('.')

# Probar importación directa
try:
    from servicios.servicioCourseMapper import CourseMapping
    print("✅ CourseMapping importado correctamente")
except ImportError as e:
    print(f"❌ Error importando CourseMapping: {e}")

try:
    from servicios.servicioCourseMapper import CourseMapper
    print("✅ CourseMapper importado correctamente")
    
    # Probar funcionalidad básica sin Django
    mapper = CourseMapper()
    
    # Probar extracción de nombres
    test_files = [
        'alumnos_isII(1).xlsx',
        'alumnos_ada(1).xlsx', 
        'alumnos_nuevo_curso.xlsx'
    ]
    
    print("\n📋 Probando extracción de nombres:")
    for filename in test_files:
        try:
            course_name = mapper.extract_course_name(filename)
            print(f"  {filename} -> {course_name}")
        except Exception as e:
            print(f"  ❌ Error con {filename}: {e}")
    
    # Probar normalización
    print("\n🔧 Probando normalización:")
    test_names = [
        'Matemática Aplicada a la Computación',
        'INGENIERÍA DE SOFTWARE II'
    ]
    
    for name in test_names:
        try:
            normalized = mapper._normalize_course_name(name)
            print(f"  '{name}' -> '{normalized}'")
        except Exception as e:
            print(f"  ❌ Error normalizando '{name}': {e}")
    
    print("\n✅ Pruebas básicas completadas")
    
except ImportError as e:
    print(f"❌ Error importando CourseMapper: {e}")
except Exception as e:
    print(f"❌ Error ejecutando pruebas: {e}")