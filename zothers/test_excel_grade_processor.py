#!/usr/bin/env python3
"""
Test para el servicio de procesamiento de Excel de notas
"""
import os
import django
import pandas as pd
import tempfile
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioExcelNotas import ExcelGradeTemplateProcessor, GradeUploadService, ExcelGradeProcessingService
from repositorio.postgres_repository.models import Student, Teacher, CourseGroup, PhaseGrade


def create_test_excel():
    """Crea un archivo Excel de prueba con el formato esperado"""
    
    # Datos de prueba
    test_data = {
        'CUI': ['2021001', '2021002', '2021003', '2021004', '2021005'],
        'Apellidos y Nombres': ['Pérez, Juan', 'García, María', 'López, Carlos', 'Martín, Ana', 'Ruiz, Pedro'],
        'P1': [15.5, 12.0, 18.5, 8.5, 16.0],  # Nota parcial
        'Continua': [14.0, 13.5, 17.0, 9.0, 15.5]  # Nota continua
    }
    
    # Crear DataFrame
    df = pd.DataFrame(test_data)
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    
    # Escribir con headers en fila 10 (como en el formato real)
    with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
        # Escribir filas vacías primero
        empty_df = pd.DataFrame([[''] * len(df.columns)] * 9)
        empty_df.to_excel(writer, index=False, header=False, startrow=0)
        
        # Escribir datos con headers en fila 10
        df.to_excel(writer, index=False, startrow=9)
    
    return temp_file.name


def test_excel_template_processor():
    """Prueba el procesador de plantillas Excel"""
    
    print("🧪 Probando ExcelGradeTemplateProcessor...")
    
    # Crear archivo de prueba
    test_file = create_test_excel()
    
    try:
        # Inicializar procesador
        processor = ExcelGradeTemplateProcessor()
        
        # Procesar archivo
        result = processor.process_excel_template(test_file)
        
        print(f"✅ Procesamiento exitoso: {result['success']}")
        print(f"📊 Registros procesados: {result['processed_count']}")
        print(f"❌ Errores: {len(result['errors'])}")
        print(f"⚠️  Warnings: {len(result['warnings'])}")
        
        if result['errors']:
            print("Errores encontrados:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print("Warnings encontrados:")
            for warning in result['warnings'][:5]:  # Mostrar solo los primeros 5
                print(f"  - {warning}")
        
        # Mostrar datos procesados
        if 'processed_data' in result:
            print(f"\n📋 Datos procesados ({len(result['processed_data'])} registros):")
            for i, record in enumerate(result['processed_data'][:3]):  # Mostrar solo los primeros 3
                print(f"  {i+1}. Estudiante: {record['student_code']}")
                print(f"     Notas: {record['grades']}")
        
        return result['success']
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(test_file):
            os.unlink(test_file)


def test_grade_upload_service():
    """Prueba el servicio de subida de notas"""
    
    print("\n🧪 Probando GradeUploadService...")
    
    try:
        # Obtener un profesor de prueba
        teacher = Teacher.objects.first()
        if not teacher:
            print("❌ No hay profesores disponibles para la prueba")
            return False
        
        # Obtener un grupo de curso
        course_group = CourseGroup.objects.first()
        if not course_group:
            print("❌ No hay grupos de curso disponibles para la prueba")
            return False
        
        print(f"👨‍🏫 Profesor: {teacher.user.get_full_name()}")
        print(f"📚 Curso: {course_group}")
        
        # Crear datos de prueba
        test_processed_data = [
            {
                'student_code': '2021001',
                'grades': {'partial': Decimal('15.5'), 'continuous': Decimal('14.0')},
                'row_index': 1
            },
            {
                'student_code': '2021002',
                'grades': {'partial': Decimal('12.0'), 'continuous': Decimal('13.5')},
                'row_index': 2
            }
        ]
        
        # Inicializar servicio
        uploader = GradeUploadService(teacher.id)
        
        # Verificar duplicados
        duplicate_check = uploader.check_duplicate_grades(course_group.id, 'primera')
        print(f"🔍 Verificación de duplicados: {duplicate_check}")
        
        # Subir notas (en modo de prueba, no ejecutar realmente)
        print("📤 Simulando subida de notas...")
        print(f"  - Datos a procesar: {len(test_processed_data)} registros")
        
        # Mostrar resumen
        summary = uploader.get_upload_summary()
        print(f"📊 Resumen: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de subida: {str(e)}")
        return False


def test_complete_service():
    """Prueba el servicio completo de procesamiento y subida"""
    
    print("\n🧪 Probando ExcelGradeProcessingService...")
    
    # Crear archivo de prueba
    test_file = create_test_excel()
    
    try:
        # Obtener un profesor de prueba
        teacher = Teacher.objects.first()
        if not teacher:
            print("❌ No hay profesores disponibles para la prueba")
            return False
        
        # Obtener un grupo de curso
        course_group = CourseGroup.objects.first()
        if not course_group:
            print("❌ No hay grupos de curso disponibles para la prueba")
            return False
        
        # Inicializar servicio completo
        service = ExcelGradeProcessingService(teacher.id)
        
        # Procesar archivo (sin subir realmente)
        print("🔄 Procesando archivo Excel completo...")
        
        # Solo procesar, no subir
        processing_result = service.processor.process_excel_template(test_file)
        
        print(f"✅ Procesamiento completo exitoso: {processing_result['success']}")
        
        if processing_result['success']:
            summary = service.processor.get_processing_summary()
            print(f"📊 Resumen del procesamiento:")
            print(f"  - Total procesado: {summary['total_processed']}")
            print(f"  - Errores: {summary['total_errors']}")
            print(f"  - Warnings: {summary['total_warnings']}")
        
        return processing_result['success']
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(test_file):
            os.unlink(test_file)


def main():
    """Función principal de pruebas"""
    
    print("🚀 Iniciando pruebas del servicio de Excel de notas")
    print("=" * 60)
    
    # Verificar conexión a base de datos
    try:
        student_count = Student.objects.count()
        teacher_count = Teacher.objects.count()
        course_count = CourseGroup.objects.count()
        
        print(f"📊 Estado de la base de datos:")
        print(f"  - Estudiantes: {student_count}")
        print(f"  - Profesores: {teacher_count}")
        print(f"  - Grupos de curso: {course_count}")
        
        if teacher_count == 0 or course_count == 0:
            print("⚠️  Advertencia: Datos insuficientes para pruebas completas")
        
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {str(e)}")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Procesador de plantillas Excel", test_excel_template_processor),
        ("Servicio de subida de notas", test_grade_upload_service),
        ("Servicio completo", test_complete_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Mostrar resumen final
    print("\n" + "=" * 60)
    print("📋 Resumen de pruebas:")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    total_passed = sum(1 for _, result in results if result)
    print(f"\n🎯 Resultado: {total_passed}/{len(results)} pruebas pasaron")


if __name__ == "__main__":
    main()