#!/usr/bin/env python3
"""
Script de prueba para el servicio de asignación de cursos
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioAsignacionCursos import CourseAssignmentService


def test_course_assignment_service():
    """Prueba básica del servicio de asignación de cursos"""
    
    print("=== Prueba del Servicio de Asignación de Cursos ===\n")
    
    # Directorio con archivos Excel
    excel_directory = "EXELS"
    
    if not os.path.exists(excel_directory):
        print(f"❌ Error: Directorio {excel_directory} no encontrado")
        return
    
    # Verificar archivos requeridos
    bdtotall_path = os.path.join(excel_directory, "bdtotall.xlsx")
    if not os.path.exists(bdtotall_path):
        print(f"❌ Error: Archivo bdtotall.xlsx no encontrado en {excel_directory}")
        return
    
    print(f"✅ Directorio de archivos Excel: {excel_directory}")
    print(f"✅ Archivo bdtotall.xlsx encontrado")
    
    # Listar archivos alumnos_*.xlsx
    import glob
    course_files = glob.glob(os.path.join(excel_directory, "alumnos_*.xlsx"))
    print(f"✅ Archivos de cursos encontrados: {len(course_files)}")
    for file_path in course_files:
        print(f"   - {os.path.basename(file_path)}")
    
    if not course_files:
        print("⚠️  Advertencia: No se encontraron archivos alumnos_*.xlsx")
        return
    
    print("\n--- Iniciando proceso de asignación ---\n")
    
    try:
        # Crear servicio y ejecutar asignación
        service = CourseAssignmentService()
        report = service.assign_students_from_excel(excel_directory)
        
        # Mostrar resultados
        print("=== REPORTE DE ASIGNACIÓN ===\n")
        
        print(f"📊 Estudiantes procesados: {report.total_students_processed}")
        print(f"📚 Cursos procesados: {report.total_courses_processed}")
        print(f"✅ Asignaciones creadas: {report.total_assignments_created}")
        print(f"⏭️  Asignaciones omitidas: {report.total_assignments_skipped}")
        
        if report.errors:
            print(f"\n❌ Errores ({len(report.errors)}):")
            for error in report.errors:
                print(f"   - {error}")
        
        if report.warnings:
            print(f"\n⚠️  Advertencias ({len(report.warnings)}):")
            for warning in report.warnings:
                print(f"   - {warning}")
        
        print("\n--- Detalle por curso ---")
        for course_result in report.course_results:
            print(f"\n📚 {course_result.course_name} ({course_result.course_code})")
            print(f"   ✅ Asignados: {course_result.assigned_count}")
            print(f"   ⏭️  Omitidos: {course_result.skipped_count}")
            
            if course_result.errors:
                print(f"   ❌ Errores: {len(course_result.errors)}")
                for error in course_result.errors[:3]:  # Mostrar solo los primeros 3
                    print(f"      - {error}")
                if len(course_result.errors) > 3:
                    print(f"      ... y {len(course_result.errors) - 3} más")
            
            if course_result.warnings:
                print(f"   ⚠️  Advertencias: {len(course_result.warnings)}")
        
        print(f"\n🎉 Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error ejecutando el servicio: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_course_assignment_service()