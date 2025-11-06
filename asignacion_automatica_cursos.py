#!/usr/bin/env python
"""
Sistema de Asignación Automática de Cursos - Versión Producción

Este script ejecuta automáticamente el proceso de asignación de estudiantes a cursos
desde archivos Excel sin intervención del usuario.

Características:
- Ejecución completamente automática
- Procesamiento de archivos Excel
- Creación automática de cursos
- Asignación de estudiantes
- Logging detallado
- Reportes completos

Uso:
    python asignacion_automatica_cursos.py
"""

import os
import sys
import django
import logging
from pathlib import Path
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioAsignacionCursos import CourseAssignmentService
from repositorio.postgres_repository.models import Student, Course, Enrollment, CourseGroup


def setup_logging():
    """Configura el sistema de logging para el proceso automático"""
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logging
    log_filename = log_dir / f"asignacion_automatica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def verificar_archivos_excel(excel_dir: str, logger) -> bool:
    """Verifica que existan los archivos Excel necesarios"""
    logger.info(f"Verificando archivos Excel en: {excel_dir}")
    
    if not os.path.exists(excel_dir):
        logger.error(f"Directorio no encontrado: {excel_dir}")
        return False
    
    # Verificar bdtotall.xlsx
    bdtotall_path = os.path.join(excel_dir, 'bdtotall.xlsx')
    if not os.path.exists(bdtotall_path):
        logger.error("Archivo bdtotall.xlsx no encontrado")
        return False
    
    logger.info("Archivo bdtotall.xlsx encontrado")
    
    # Buscar archivos de cursos
    course_files = []
    for file in os.listdir(excel_dir):
        if file.startswith('alumnos_') and file.endswith('.xlsx'):
            course_files.append(file)
    
    if not course_files:
        logger.warning("No se encontraron archivos alumnos_*.xlsx")
        return False
    
    logger.info(f"Encontrados {len(course_files)} archivos de cursos")
    for course_file in course_files:
        logger.info(f"   - {course_file}")
    
    return True


def mostrar_estado_inicial(logger):
    """Muestra el estado inicial de la base de datos"""
    logger.info("ESTADO INICIAL DE LA BASE DE DATOS")
    logger.info("-" * 50)
    
    try:
        student_count = Student.objects.count()
        course_count = Course.objects.count()
        coursegroup_count = CourseGroup.objects.count()
        enrollment_count = Enrollment.objects.count()
        
        logger.info(f"Estudiantes: {student_count}")
        logger.info(f"Cursos: {course_count}")
        logger.info(f"Grupos de cursos: {coursegroup_count}")
        logger.info(f"Inscripciones: {enrollment_count}")
        
        return {
            'students': student_count,
            'courses': course_count,
            'course_groups': coursegroup_count,
            'enrollments': enrollment_count
        }
        
    except Exception as e:
        logger.error(f"Error consultando base de datos: {e}")
        return None


def ejecutar_asignacion_automatica(excel_dir: str, logger):
    """Ejecuta el proceso automático de asignación de cursos"""
    logger.info("INICIANDO PROCESO AUTOMATICO DE ASIGNACION")
    logger.info("=" * 60)
    
    try:
        # Crear servicio de asignación
        service = CourseAssignmentService()
        
        # Ejecutar proceso
        logger.info("Procesando archivos Excel...")
        report = service.assign_students_from_excel(excel_dir)
        
        # Mostrar resultados
        mostrar_reporte_detallado(report, logger)
        
        return report
        
    except Exception as e:
        logger.error(f"Error durante la asignacion: {str(e)}")
        raise


def mostrar_reporte_detallado(report, logger):
    """Muestra el reporte detallado de asignaciones"""
    logger.info("\n" + "=" * 60)
    logger.info("REPORTE DE ASIGNACION AUTOMATICA")
    logger.info("=" * 60)
    
    # Estadísticas generales
    logger.info(f"Estudiantes procesados: {report.total_students_processed}")
    logger.info(f"Cursos procesados: {report.total_courses_processed}")
    logger.info(f"Asignaciones creadas: {report.total_assignments_created}")
    logger.info(f"Asignaciones omitidas: {report.total_assignments_skipped}")
    logger.info(f"Errores totales: {len(report.errors)}")
    logger.info(f"Advertencias totales: {len(report.warnings)}")
    
    # Detalles por curso
    if report.course_results:
        logger.info("\nDETALLES POR CURSO:")
        logger.info("-" * 40)
        
        for course_result in report.course_results:
            logger.info(f"\nCurso: {course_result.course_name}")
            logger.info(f"   ID: {course_result.course_id}")
            logger.info(f"   Codigo: {course_result.course_code}")
            logger.info(f"   Asignados: {course_result.assigned_count}")
            logger.info(f"   Omitidos: {course_result.skipped_count}")
            
            if course_result.errors:
                logger.info(f"   Errores: {len(course_result.errors)}")
                for error in course_result.errors[:3]:  # Mostrar solo los primeros 3
                    logger.warning(f"      - {error}")
                if len(course_result.errors) > 3:
                    remaining = len(course_result.errors) - 3
                    logger.info(f"      ... y {remaining} errores mas")
            
            if course_result.warnings:
                logger.info(f"   Advertencias: {len(course_result.warnings)}")
                for warning in course_result.warnings[:3]:  # Mostrar solo las primeras 3
                    logger.warning(f"      - {warning}")
                if len(course_result.warnings) > 3:
                    remaining = len(course_result.warnings) - 3
                    logger.info(f"      ... y {remaining} advertencias mas")
    
    # Errores generales (solo los más importantes)
    if report.errors:
        logger.info("\nERRORES PRINCIPALES:")
        for error in report.errors[:5]:  # Mostrar solo los primeros 5
            logger.error(f"   - {error}")
        if len(report.errors) > 5:
            remaining = len(report.errors) - 5
            logger.info(f"   ... y {remaining} errores mas (ver log completo)")


def mostrar_estado_final(estado_inicial, logger):
    """Muestra el estado final y las diferencias"""
    logger.info("\nESTADO FINAL DE LA BASE DE DATOS")
    logger.info("-" * 50)
    
    try:
        student_count = Student.objects.count()
        course_count = Course.objects.count()
        coursegroup_count = CourseGroup.objects.count()
        enrollment_count = Enrollment.objects.count()
        
        logger.info(f"Estudiantes: {student_count}")
        logger.info(f"Cursos: {course_count}")
        logger.info(f"Grupos de cursos: {coursegroup_count}")
        logger.info(f"Inscripciones: {enrollment_count}")
        
        if estado_inicial:
            logger.info("\nCAMBIOS REALIZADOS:")
            logger.info(f"   Estudiantes: +{student_count - estado_inicial['students']}")
            logger.info(f"   Cursos: +{course_count - estado_inicial['courses']}")
            logger.info(f"   Grupos: +{coursegroup_count - estado_inicial['course_groups']}")
            logger.info(f"   Inscripciones: +{enrollment_count - estado_inicial['enrollments']}")
        
        return {
            'students': student_count,
            'courses': course_count,
            'course_groups': coursegroup_count,
            'enrollments': enrollment_count
        }
        
    except Exception as e:
        logger.error(f"Error consultando estado final: {e}")
        return None


def verificar_resultados(logger):
    """Verifica los resultados de la asignación"""
    logger.info("\nVERIFICACION DE RESULTADOS")
    logger.info("-" * 40)
    
    try:
        # Verificar cursos con estudiantes
        courses_with_students = Course.objects.filter(
            coursegroup__enrollment__isnull=False
        ).distinct()
        
        logger.info(f"Cursos con estudiantes: {courses_with_students.count()}")
        
        for course in courses_with_students[:5]:  # Mostrar solo los primeros 5
            enrollment_count = Enrollment.objects.filter(
                course_group__course=course
            ).count()
            logger.info(f"   - {course.name}: {enrollment_count} estudiantes")
        
        if courses_with_students.count() > 5:
            remaining = courses_with_students.count() - 5
            logger.info(f"   ... y {remaining} cursos mas")
        
        # Verificar duplicados
        from django.db.models import Count
        duplicates = Enrollment.objects.values('student', 'course_group').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            logger.warning(f"Duplicados encontrados: {duplicates.count()}")
        else:
            logger.info("No se encontraron duplicados")
        
    except Exception as e:
        logger.error(f"Error verificando resultados: {e}")


def generar_resumen_final(report, estado_inicial, estado_final, logger):
    """Genera el resumen final del proceso"""
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN FINAL DEL PROCESO AUTOMATICO")
    logger.info("=" * 60)
    
    # Determinar el resultado general
    if report.errors and report.total_assignments_created == 0:
        resultado = "PROCESO FALLIDO"
        logger.error(resultado)
    elif report.errors and report.total_assignments_created > 0:
        resultado = "PROCESO COMPLETADO CON ERRORES"
        logger.warning(resultado)
    elif report.total_assignments_created > 0:
        resultado = "PROCESO EXITOSO"
        logger.info(resultado)
    else:
        resultado = "NO SE CREARON NUEVAS ASIGNACIONES"
        logger.info(resultado)
    
    # Estadísticas finales
    logger.info(f"\nESTADISTICAS FINALES:")
    logger.info(f"   Archivos procesados: {report.total_courses_processed}")
    logger.info(f"   Estudiantes procesados: {report.total_students_processed}")
    logger.info(f"   Asignaciones exitosas: {report.total_assignments_created}")
    logger.info(f"   Asignaciones omitidas: {report.total_assignments_skipped}")
    logger.info(f"   Errores: {len(report.errors)}")
    logger.info(f"   Advertencias: {len(report.warnings)}")
    
    if estado_inicial and estado_final:
        nuevas_inscripciones = estado_final['enrollments'] - estado_inicial['enrollments']
        nuevos_cursos = estado_final['courses'] - estado_inicial['courses']
        nuevos_estudiantes = estado_final['students'] - estado_inicial['students']
        
        logger.info(f"\nIMPACTO EN BASE DE DATOS:")
        logger.info(f"   Nuevas inscripciones: {nuevas_inscripciones}")
        logger.info(f"   Nuevos cursos: {nuevos_cursos}")
        logger.info(f"   Nuevos estudiantes: {nuevos_estudiantes}")
    
    return resultado


def main():
    """Función principal del proceso automático"""
    
    # Configurar logging
    logger = setup_logging()
    
    logger.info("INICIANDO ASIGNACION AUTOMATICA DE CURSOS")
    logger.info("=" * 80)
    logger.info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Configurar directorio de Excel
        excel_dir = 'EXELS'  # Usar directorio real con datos
        
        # 1. Verificar archivos Excel
        if not verificar_archivos_excel(excel_dir, logger):
            logger.error("Verificacion de archivos fallida. Abortando proceso.")
            return False
        
        # 2. Mostrar estado inicial
        estado_inicial = mostrar_estado_inicial(logger)
        
        # 3. Ejecutar asignación automática
        report = ejecutar_asignacion_automatica(excel_dir, logger)
        
        # 4. Mostrar estado final
        estado_final = mostrar_estado_final(estado_inicial, logger)
        
        # 5. Verificar resultados
        verificar_resultados(logger)
        
        # 6. Generar resumen final
        resultado = generar_resumen_final(report, estado_inicial, estado_final, logger)
        
        # 7. Determinar código de salida
        if "EXITOSO" in resultado:
            logger.info("Proceso completado exitosamente")
            return True
        elif "ERRORES" in resultado:
            logger.warning("Proceso completado con errores")
            return True  # Aún consideramos éxito parcial
        else:
            logger.error("Proceso fallido")
            return False
            
    except Exception as e:
        logger.error(f"Error critico en el proceso: {str(e)}")
        logger.exception("Detalles del error:")
        return False
    
    finally:
        logger.info("Fin del proceso automatico")
        logger.info("=" * 80)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)