#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de ejecución automática para el sistema de asignación de cursos
Este script ejecuta automáticamente el proceso completo de asignación
de estudiantes a cursos sin requerir intervención manual.

Uso:
    python ejecutar_asignacion_automatica.py

O con poetry:
    poetry run python ejecutar_asignacion_automatica.py
"""
import os
import sys
import django
import logging
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioAsignacionCursos import CourseAssignmentService

def setup_logging():
    """Configura el logging para el proceso automático"""
    # Configurar encoding UTF-8 para evitar problemas con caracteres especiales
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('asignacion_automatica.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Ejecuta el proceso automático de asignación de cursos"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 80)
    print("EJECUCION AUTOMATICA: ASIGNACION DE CURSOS")
    print("=" * 80)
    
    try:
        # Verificar directorio de archivos Excel
        excel_dir = 'EXELS'
        if not os.path.exists(excel_dir):
            logger.error(f"Directorio {excel_dir} no encontrado")
            print(f"ERROR: Directorio {excel_dir} no encontrado")
            return False

        # Verificar archivo principal
        bdtotall_path = os.path.join(excel_dir, 'bdtotall.xlsx')
        if not os.path.exists(bdtotall_path):
            logger.error("Archivo bdtotall.xlsx no encontrado")
            print("ERROR: Archivo bdtotall.xlsx no encontrado")
            return False

        # Contar archivos de cursos
        course_files = []
        for file in os.listdir(excel_dir):
            if file.startswith('alumnos_') and file.endswith('.xlsx'):
                course_files.append(file)

        if not course_files:
            logger.warning("No se encontraron archivos de cursos")
            print("ADVERTENCIA: No se encontraron archivos alumnos_*.xlsx")
            return False

        print(f"Directorio: {os.path.abspath(excel_dir)}")
        print(f"Archivo principal: bdtotall.xlsx")
        print(f"Archivos de cursos: {len(course_files)}")
        
        # Mostrar archivos encontrados
        for course_file in sorted(course_files):
            print(f"   • {course_file}")

        print("\nIniciando proceso de asignación automática...")

        # Ejecutar servicio de asignación
        service = CourseAssignmentService()
        report = service.assign_students_from_excel(excel_dir)

        # Mostrar resultados
        print("\n" + "=" * 80)
        print("RESULTADOS DEL PROCESO AUTOMATICO")
        print("=" * 80)
        print(f"Estudiantes procesados: {report.total_students_processed}")
        print(f"Cursos procesados: {report.total_courses_processed}")
        print(f"Asignaciones creadas: {report.total_assignments_created}")
        print(f"Asignaciones omitidas: {report.total_assignments_skipped}")
        print(f"Errores totales: {len(report.errors)}")
        print(f"Advertencias totales: {len(report.warnings)}")

        # Mostrar errores si los hay
        if report.errors:
            print(f"\nERRORES ENCONTRADOS:")
            for i, error in enumerate(report.errors[:5], 1):  # Mostrar solo los primeros 5
                print(f"   {i}. {error}")
            if len(report.errors) > 5:
                print(f"   ... y {len(report.errors) - 5} errores más")

        # Mostrar advertencias si las hay
        if report.warnings:
            print(f"\nADVERTENCIAS:")
            for i, warning in enumerate(report.warnings[:5], 1):  # Mostrar solo las primeras 5
                print(f"   {i}. {warning}")
            if len(report.warnings) > 5:
                print(f"   ... y {len(report.warnings) - 5} advertencias más")

        # Determinar éxito del proceso
        total_assignments = report.total_assignments_created
        total_errors = len(report.errors)
        
        if total_assignments > 0:
            print(f"\nPROCESO COMPLETADO EXITOSAMENTE")
            print(f"   Se crearon {total_assignments} asignaciones")
            if total_errors > 0:
                print(f"   Con {total_errors} errores que requieren atención")
            logger.info(f"Proceso completado: {total_assignments} asignaciones creadas")
            return True
        else:
            print(f"\nPROCESO COMPLETADO CON PROBLEMAS")
            print(f"   No se crearon asignaciones debido a errores")
            logger.warning("Proceso completado sin crear asignaciones")
            return False

    except Exception as e:
        error_msg = f"Error durante el proceso automático: {str(e)}"
        logger.error(error_msg)
        print(f"\nERROR CRITICO: {error_msg}")
        return False

    finally:
        print("\n" + "=" * 80)
        print("Log guardado en: asignacion_automatica.log")
        print("=" * 80)

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)