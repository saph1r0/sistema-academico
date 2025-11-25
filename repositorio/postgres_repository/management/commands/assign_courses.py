"""
Comando de gestión Django para asignar estudiantes a cursos automáticamente desde archivos Excel
"""
import os
import logging
from django.core.management.base import BaseCommand, CommandError
from servicios.servicioAsignacionCursos import CourseAssignmentService


class Command(BaseCommand):
    help = 'Asigna estudiantes a cursos automáticamente leyendo archivos Excel (bdtotall.xlsx y alumnos_*.xlsx)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            default='EXELS',
            help='Directorio que contiene los archivos Excel (por defecto: EXELS)'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada del proceso'
        )
        
        parser.add_argument(
            '--log-level',
            type=str,
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='Nivel de logging (por defecto: INFO)'
        )
    
    def handle(self, *args, **options):
        """Maneja la ejecución del comando de asignación de cursos"""
        
        # Configurar parámetros
        excel_directory = options['directory']
        verbose = options['verbose']
        log_level = options['log_level']
        
        # Configurar logging
        self._setup_logging(log_level, verbose)
        
        # Validar directorio
        if not os.path.exists(excel_directory):
            raise CommandError(f'❌ Directorio no encontrado: {excel_directory}')
        
        if not os.path.isdir(excel_directory):
            raise CommandError(f'❌ La ruta especificada no es un directorio: {excel_directory}')
        
        # Mostrar información inicial
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Iniciando asignación automática de cursos')
        )
        self.stdout.write(f'📁 Directorio: {os.path.abspath(excel_directory)}')
        
        # Verificar archivos requeridos
        self._validate_required_files(excel_directory)
        
        try:
            # Ejecutar proceso de asignación
            service = CourseAssignmentService()
            report = service.assign_students_from_excel(excel_directory)
            
            # Mostrar resultados
            self._display_assignment_report(report)
            
            # Determinar código de salida
            if report.errors:
                self.stdout.write(
                    self.style.ERROR('⚠️  Proceso completado con errores')
                )
                if not report.total_assignments_created:
                    raise CommandError('No se pudieron crear asignaciones debido a errores')
            elif report.total_assignments_created > 0:
                self.stdout.write(
                    self.style.SUCCESS('🎉 ¡Proceso completado exitosamente!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('ℹ️  No se crearon nuevas asignaciones')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la asignación: {str(e)}')
            )
            raise CommandError(f'Error en el proceso de asignación: {str(e)}')
    
    def _setup_logging(self, log_level: str, verbose: bool):
        """Configura el sistema de logging para el comando"""
        
        # Configurar nivel de logging
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configurar logger para CourseAssignmentService
        logger = logging.getLogger('CourseAssignmentService')
        logger.setLevel(numeric_level)
        
        # Crear handler para consola si no existe
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(numeric_level)
            
            # Formato de logging
            if verbose:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            else:
                formatter = logging.Formatter('%(levelname)s: %(message)s')
            
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        if verbose:
            self.stdout.write(f'🔧 Logging configurado: nivel {log_level}')
    
    def _validate_required_files(self, excel_directory: str):
        """Valida que existan los archivos requeridos en el directorio"""
        
        # Verificar bdtotall.xlsx
        bdtotall_path = os.path.join(excel_directory, 'bdtotall.xlsx')
        if not os.path.exists(bdtotall_path):
            raise CommandError(
                f'❌ Archivo requerido no encontrado: bdtotall.xlsx en {excel_directory}'
            )
        
        self.stdout.write(f'✅ Archivo principal encontrado: bdtotall.xlsx')
        
        # Buscar archivos alumnos_*.xlsx
        import glob
        pattern = os.path.join(excel_directory, 'alumnos_*.xlsx')
        course_files = glob.glob(pattern)
        
        if not course_files:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  No se encontraron archivos alumnos_*.xlsx en {excel_directory}'
                )
            )
            self.stdout.write('   El proceso continuará pero no se crearán asignaciones')
        else:
            self.stdout.write(f'✅ Archivos de cursos encontrados: {len(course_files)}')
            for course_file in sorted(course_files):
                filename = os.path.basename(course_file)
                self.stdout.write(f'   📄 {filename}')
    
    def _display_assignment_report(self, report):
        """Muestra el reporte completo de asignaciones"""
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('📊 REPORTE DE ASIGNACIÓN AUTOMÁTICA DE CURSOS'))
        self.stdout.write('='*80)
        
        # Estadísticas generales
        self.stdout.write(f'👥 Estudiantes procesados: {report.total_students_processed}')
        self.stdout.write(f'📚 Cursos procesados: {report.total_courses_processed}')
        self.stdout.write(f'✅ Asignaciones creadas: {report.total_assignments_created}')
        self.stdout.write(f'⏭️  Asignaciones omitidas: {report.total_assignments_skipped}')
        self.stdout.write(f'❌ Errores totales: {len(report.errors)}')
        self.stdout.write(f'⚠️  Advertencias totales: {len(report.warnings)}')
        
        # Detalles por curso
        if report.course_results:
            self.stdout.write('\n📋 DETALLES POR CURSO:')
            self.stdout.write('-' * 60)
            
            for course_result in report.course_results:
                self.stdout.write(f'\n📖 Curso: {course_result.course_name}')
                self.stdout.write(f'   🆔 ID: {course_result.course_id}')
                self.stdout.write(f'   📝 Código: {course_result.course_code}')
                self.stdout.write(f'   ✅ Asignados: {course_result.assigned_count}')
                self.stdout.write(f'   ⏭️  Omitidos: {course_result.skipped_count}')
                
                if course_result.errors:
                    self.stdout.write(f'   ❌ Errores: {len(course_result.errors)}')
                    for error in course_result.errors[:2]:  # Mostrar solo los primeros 2
                        self.stdout.write(f'      • {error}')
                    if len(course_result.errors) > 2:
                        remaining = len(course_result.errors) - 2
                        self.stdout.write(f'      ... y {remaining} errores más')
                
                if course_result.warnings:
                    self.stdout.write(f'   ⚠️  Advertencias: {len(course_result.warnings)}')
                    for warning in course_result.warnings[:2]:  # Mostrar solo las primeras 2
                        self.stdout.write(f'      • {warning}')
                    if len(course_result.warnings) > 2:
                        remaining = len(course_result.warnings) - 2
                        self.stdout.write(f'      ... y {remaining} advertencias más')
        
        # Errores generales
        if report.errors:
            self.stdout.write('\n🚨 ERRORES GENERALES:')
            for error in report.errors[:5]:  # Mostrar solo los primeros 5
                self.stdout.write(f'   • {error}')
            if len(report.errors) > 5:
                remaining = len(report.errors) - 5
                self.stdout.write(f'   ... y {remaining} errores más')
        
        # Advertencias generales
        if report.warnings:
            self.stdout.write('\n⚠️  ADVERTENCIAS GENERALES:')
            for warning in report.warnings[:5]:  # Mostrar solo las primeras 5
                self.stdout.write(f'   • {warning}')
            if len(report.warnings) > 5:
                remaining = len(report.warnings) - 5
                self.stdout.write(f'   ... y {remaining} advertencias más')
        
        self.stdout.write('='*80)