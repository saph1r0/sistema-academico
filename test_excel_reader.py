#!/usr/bin/env python3
"""
Script de prueba para el servicio ExcelReader
"""
import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Agregar el directorio actual al path para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from servicios.servicioExcelReader import ExcelReader, StudentData, ExcelReadResult


def test_excel_reader():
    """Prueba el servicio ExcelReader"""
    
    print("🧪 PROBANDO SERVICIO EXCEL READER")
    print("=" * 60)
    
    reader = ExcelReader()
    
    # Probar lectura del archivo principal de estudiantes
    print("\n📚 1. PROBANDO LECTURA DE ARCHIVO PRINCIPAL (bdtotall.xlsx)")
    print("-" * 50)
    
    students_file = "EXELS/bdtotall.xlsx"
    
    if os.path.exists(students_file):
        result = reader.read_students_file(students_file)
        
        if result.success:
            students_data = result.data
            print(f"✅ Archivo leído exitosamente")
            print(f"📊 Total estudiantes: {len(students_data)}")
            
            # Mostrar algunos ejemplos
            print(f"\n👥 PRIMEROS 3 ESTUDIANTES:")
            for i, (code, student) in enumerate(students_data.items()):
                if i >= 3:
                    break
                print(f"  • {code}: {student.full_name} ({student.email})")
            
            if result.warnings:
                print(f"\n⚠️  ADVERTENCIAS ({len(result.warnings)}):")
                for warning in result.warnings[:5]:  # Mostrar solo las primeras 5
                    print(f"  - {warning}")
                if len(result.warnings) > 5:
                    print(f"  ... y {len(result.warnings) - 5} advertencias más")
        else:
            print(f"❌ Error: {result.error_message}")
    else:
        print(f"❌ Archivo no encontrado: {students_file}")
    
    # Probar lectura de archivos de cursos
    print(f"\n📋 2. PROBANDO LECTURA DE ARCHIVOS DE CURSOS")
    print("-" * 50)
    
    course_files = []
    if os.path.exists('EXELS'):
        for file in os.listdir('EXELS'):
            if file.startswith('alumnos_') and file.endswith('.xlsx'):
                course_files.append(os.path.join('EXELS', file))
    
    print(f"📁 Archivos de cursos encontrados: {len(course_files)}")
    
    for course_file in course_files[:2]:  # Probar solo los primeros 2
        print(f"\n📄 Probando: {os.path.basename(course_file)}")
        
        result = reader.read_course_file(course_file)
        
        if result.success:
            student_codes = result.data
            print(f"  ✅ Leído exitosamente")
            print(f"  📊 Códigos encontrados: {len(student_codes)}")
            
            # Mostrar algunos códigos
            if student_codes:
                print(f"  🔢 Primeros códigos: {student_codes[:5]}")
        else:
            print(f"  ❌ Error: {result.error_message}")
    
    # Probar validación de archivos
    print(f"\n🔍 3. PROBANDO VALIDACIÓN DE ARCHIVOS")
    print("-" * 50)
    
    # Archivo que no existe
    result = reader._validate_file("archivo_inexistente.xlsx")
    print(f"Archivo inexistente: {'✅ Validación correcta' if not result.success else '❌ Debería fallar'}")
    
    # Archivo que existe
    if os.path.exists(students_file):
        result = reader._validate_file(students_file)
        print(f"Archivo existente: {'✅ Validación correcta' if result.success else '❌ Debería pasar'}")
    
    # Probar información de archivo
    print(f"\n📋 4. PROBANDO INFORMACIÓN DE ARCHIVO")
    print("-" * 50)
    
    if os.path.exists(students_file):
        info = reader.get_file_info(students_file)
        print(f"Archivo: {os.path.basename(info['file_path'])}")
        print(f"Existe: {info['exists']}")
        print(f"Legible: {info['readable']}")
        print(f"Hojas: {info['sheets']}")
        print(f"Dimensiones: {info['dimensions']}")
        if info['error']:
            print(f"Error: {info['error']}")
    
    print(f"\n✅ PRUEBAS COMPLETADAS")


if __name__ == "__main__":
    test_excel_reader()