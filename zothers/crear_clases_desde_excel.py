#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script ejecutable para procesar Excel de profesores y crear todas las clases
Cada fila del Excel representa una clase específica (profesor + curso + grupo)
"""
import os
import sys
import django
import logging
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioCreadorClases import CourseGroupCreator
from repositorio.postgres_repository.models import CourseGroup, Teacher, Course


def setup_logging():
    """Configura el sistema de logging"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"{log_dir}/crear_clases_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file


def print_header():
    """Imprime el encabezado del script"""
    print("=" * 80)
    print("CREADOR DE CLASES DESDE EXCEL DE PROFESORES")
    print("=" * 80)
    print("Este script lee el Excel de profesores y crea una clase por cada fila")
    print("Cada fila representa: Profesor + Curso + Grupo = Clase específica")
    print("=" * 80)


def print_current_status():
    """Imprime el estado actual del sistema"""
    print("\n" + "=" * 50)
    print("ESTADO ACTUAL DEL SISTEMA:")
    print("=" * 50)
    
    try:
        total_teachers = Teacher.objects.count()
        total_courses = Course.objects.count()
        total_groups = CourseGroup.objects.count()
        groups_with_teacher = CourseGroup.objects.filter(teacher__isnull=False).count()
        
        print(f"Profesores registrados: {total_teachers}")
        print(f"Cursos registrados: {total_courses}")
        print(f"Grupos de curso (clases): {total_groups}")
        print(f"Clases con profesor asignado: {groups_with_teacher}")
        print(f"Clases sin profesor: {total_groups - groups_with_teacher}")
        
        if total_groups > 0:
            percentage = round((groups_with_teacher / total_groups) * 100, 2)
            print(f"Porcentaje de asignación: {percentage}%")
        
    except Exception as e:
        print(f"Error obteniendo estado: {str(e)}")


def validate_excel_file(excel_path: str) -> bool:
    """
    Valida que el archivo Excel existe y es accesible
    
    Args:
        excel_path: Ruta al archivo Excel
        
    Returns:
        True si el archivo es válido
    """
    if not os.path.exists(excel_path):
        print(f"❌ ERROR: No se encontró el archivo {excel_path}")
        return False
    
    if not excel_path.lower().endswith(('.xlsx', '.xls')):
        print(f"❌ ERROR: El archivo debe ser Excel (.xlsx o .xls)")
        return False
    
    try:
        file_size = os.path.getsize(excel_path)
        if file_size == 0:
            print(f"❌ ERROR: El archivo está vacío")
            return False
        
        print(f"✓ Archivo encontrado: {excel_path} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: No se puede acceder al archivo: {str(e)}")
        return False


def preview_excel_data(excel_path: str):
    """
    Muestra una vista previa de los datos del Excel
    
    Args:
        excel_path: Ruta al archivo Excel
    """
    try:
        import pandas as pd
        
        print("\n" + "=" * 50)
        print("VISTA PREVIA DEL EXCEL:")
        print("=" * 50)
        
        df = pd.read_excel(excel_path)
        print(f"Total de filas: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        
        print("\nPrimeras 5 filas de datos relevantes:")
        print("-" * 50)
        
        for i in range(min(5, len(df))):
            try:
                # Asumiendo estructura: col 1=curso, col 2=grupo, col 5=docente, col 6=email
                curso = str(df.iloc[i, 1]) if len(df.columns) > 1 else "N/A"
                grupo = str(df.iloc[i, 2]) if len(df.columns) > 2 else "N/A"
                docente = str(df.iloc[i, 5]) if len(df.columns) > 5 else "N/A"
                email = str(df.iloc[i, 6]) if len(df.columns) > 6 else "N/A"
                
                if curso != "nan" and docente != "nan":
                    print(f"  {i+1}. {curso} - Grupo {grupo}")
                    print(f"     Profesor: {docente}")
                    print(f"     Email: {email}")
                    print()
                    
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"Error mostrando vista previa: {str(e)}")


def confirm_execution() -> bool:
    """
    Solicita confirmación del usuario para ejecutar el proceso
    
    Returns:
        True si el usuario confirma
    """
    print("\n" + "=" * 50)
    print("CONFIRMACIÓN DE EJECUCIÓN:")
    print("=" * 50)
    print("Este proceso:")
    print("• Leerá cada fila del Excel de profesores")
    print("• Creará un CourseGroup (clase) por cada fila válida")
    print("• Creará profesores automáticamente si no existen")
    print("• Creará cursos automáticamente si no existen")
    print("• Manejará duplicados y errores automáticamente")
    print("\n⚠️  IMPORTANTE: Este proceso modificará la base de datos")
    
    while True:
        response = input("\n¿Desea continuar? (s/n): ").lower().strip()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Por favor responda 's' para sí o 'n' para no")


def print_report(report):
    """
    Imprime el reporte de creación de clases
    
    Args:
        report: CreationReport del servicio
    """
    print("\n" + "=" * 80)
    print("REPORTE DE CREACIÓN DE CLASES")
    print("=" * 80)
    
    if report.success:
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    else:
        print("❌ PROCESO COMPLETADO CON ERRORES")
    
    print(f"\nEstadísticas:")
    print(f"• Clases creadas: {report.classes_created}")
    print(f"• Profesores creados: {report.teachers_created}")
    print(f"• Cursos creados: {report.courses_created}")
    print(f"• Duplicados encontrados: {report.duplicates_found}")
    
    if report.warnings:
        print(f"\n⚠️  Advertencias ({len(report.warnings)}):")
        for warning in report.warnings[:10]:  # Mostrar máximo 10
            print(f"  • {warning}")
        if len(report.warnings) > 10:
            print(f"  ... y {len(report.warnings) - 10} advertencias más")
    
    if report.errors:
        print(f"\n❌ Errores ({len(report.errors)}):")
        for error in report.errors[:10]:  # Mostrar máximo 10
            print(f"  • {error}")
        if len(report.errors) > 10:
            print(f"  ... y {len(report.errors) - 10} errores más")


def print_final_status():
    """Imprime el estado final del sistema"""
    print("\n" + "=" * 50)
    print("ESTADO FINAL DEL SISTEMA:")
    print("=" * 50)
    
    try:
        creator = CourseGroupCreator()
        summary = creator.get_creation_summary()
        
        print(f"Profesores totales: {summary.get('total_teachers', 0)}")
        print(f"Cursos totales: {summary.get('total_courses', 0)}")
        print(f"Clases totales: {summary.get('total_course_groups', 0)}")
        print(f"Clases con profesor: {summary.get('groups_with_teacher', 0)}")
        print(f"Clases sin profesor: {summary.get('groups_without_teacher', 0)}")
        print(f"Porcentaje de asignación: {summary.get('teacher_assignment_percentage', 0)}%")
        
        # Mostrar algunos ejemplos de clases creadas
        print(f"\n" + "=" * 40)
        print("EJEMPLOS DE CLASES CREADAS:")
        print("=" * 40)
        
        recent_groups = CourseGroup.objects.filter(
            teacher__isnull=False
        ).select_related('course', 'teacher__user').order_by('-created_at')[:5]
        
        for group in recent_groups:
            print(f"• {group.course.name} - Grupo {group.group_code}")
            print(f"  Profesor: {group.teacher.user.get_full_name()}")
            print(f"  Email: {group.teacher.user.institutional_email}")
            print()
        
    except Exception as e:
        print(f"Error obteniendo estado final: {str(e)}")


def main():
    """Función principal del script"""
    # Configurar logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Imprimir encabezado
        print_header()
        
        # Mostrar estado actual
        print_current_status()
        
        # Definir ruta del Excel
        excel_path = 'EXELS/profesores.xlsx'
        
        # Validar archivo Excel
        if not validate_excel_file(excel_path):
            return False
        
        # Mostrar vista previa
        preview_excel_data(excel_path)
        
        # Solicitar confirmación
        if not confirm_execution():
            print("\n❌ Proceso cancelado por el usuario")
            return False
        
        # Crear instancia del servicio
        creator = CourseGroupCreator()
        
        print("\n" + "=" * 50)
        print("PROCESANDO EXCEL...")
        print("=" * 50)
        
        # Ejecutar creación de clases
        report = creator.create_classes_from_excel(excel_path)
        
        # Imprimir reporte
        print_report(report)
        
        # Mostrar estado final
        print_final_status()
        
        print(f"\n📄 Log completo guardado en: {log_file}")
        
        return report.success
        
    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario")
        return False
        
    except Exception as e:
        logger.error(f"Error general en el script: {str(e)}")
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)