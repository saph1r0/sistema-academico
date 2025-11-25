#!/usr/bin/env python3
"""
Verificación simple del servicio ExcelReader
"""
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from servicios.servicioExcelReader import ExcelReader

def main():
    print("🧪 Verificando ExcelReader...")
    
    reader = ExcelReader()
    
    # Test 1: Validación de archivo inexistente
    print("\n1. Probando validación de archivo inexistente...")
    result = reader._validate_file("archivo_inexistente.xlsx")
    assert not result.success, "Debería fallar para archivo inexistente"
    print("✅ Validación correcta para archivo inexistente")
    
    # Test 2: Validación de archivo existente
    print("\n2. Probando validación de archivo existente...")
    students_file = "EXELS/bdtotall.xlsx"
    if os.path.exists(students_file):
        result = reader._validate_file(students_file)
        assert result.success, f"Debería pasar para archivo existente: {result.error_message}"
        print("✅ Validación correcta para archivo existente")
    else:
        print("⚠️ Archivo bdtotall.xlsx no encontrado, saltando test")
    
    # Test 3: Lectura de archivo de estudiantes
    print("\n3. Probando lectura de archivo de estudiantes...")
    if os.path.exists(students_file):
        result = reader.read_students_file(students_file)
        if result.success:
            print(f"✅ Archivo leído exitosamente: {len(result.data)} estudiantes")
            if result.warnings:
                print(f"⚠️ {len(result.warnings)} advertencias encontradas")
        else:
            print(f"❌ Error leyendo archivo: {result.error_message}")
    
    # Test 4: Lectura de archivo de curso
    print("\n4. Probando lectura de archivo de curso...")
    course_files = [f for f in os.listdir('EXELS') if f.startswith('alumnos_') and f.endswith('.xlsx')]
    if course_files:
        course_file = os.path.join('EXELS', course_files[0])
        result = reader.read_course_file(course_file)
        if result.success:
            print(f"✅ Archivo de curso leído: {len(result.data)} códigos encontrados")
        else:
            print(f"❌ Error leyendo archivo de curso: {result.error_message}")
    
    # Test 5: Información de archivo
    print("\n5. Probando información de archivo...")
    if os.path.exists(students_file):
        info = reader.get_file_info(students_file)
        print(f"✅ Información obtenida: existe={info['exists']}, legible={info['readable']}")
    
    print("\n🎉 Verificación completada!")

if __name__ == "__main__":
    main()