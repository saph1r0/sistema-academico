"""
Servicio principal de asignación automática de estudiantes a cursos
"""
import os
import glob
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .servicioExcelReader import ExcelReader, StudentData, ExcelReadResult
from .servicioCourseMapperSimple import CourseMapper, CourseMapping
from .servicioAssignmentProcessor import AssignmentProcessor, AssignmentResult


@dataclass
class CourseAssignments:
    """Resultado de asignaciones para un curso específico"""
    course_name: str
    course_id: str
    course_code: str
    assigned_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AssignmentReport:
    """Reporte completo del proceso de asignación"""
    total_students_processed: int = 0
    total_courses_processed: int = 0
    total_assignments_created: int = 0
    total_assignments_skipped: int = 0
    course_results: List[CourseAssignments] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CourseAssignmentService:
    """
    Servicio principal que coordina todo el proceso de asignación automática
    de estudiantes a cursos mediante lectura de archivos Excel.
    
    Flujo de procesamiento:
    1. Cargar todos los estudiantes desde bdtotall.xlsx
    2. Buscar archivos alumnos_*.xlsx en el directorio
    3. Para cada archivo de curso:
       - Extraer nombre del curso del archivo
       - Leer lista de estudiantes del archivo
       - Crear asignaciones en la base de datos
    4. Generar reporte de resultados
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.excel_reader = ExcelReader()
        self.course_mapper = CourseMapper()
        self.assignment_processor = AssignmentProcessor()
    
    def assign_students_from_excel(self, excel_directory: str) -> AssignmentReport:
        """
        Ejecuta el proceso completo de asignación de estudiantes a cursos
        
        Args:
            excel_directory: Directorio que contiene los archivos Excel
            
        Returns:
            AssignmentReport con el resumen completo del proceso
        """
        self.logger.info(f"Iniciando proceso de asignación desde directorio: {excel_directory}")
        
        report = AssignmentReport()
        
        try:
            # 1. Cargar todos los estudiantes desde bdtotall.xlsx
            students_db = self._load_all_students(excel_directory)
            if not students_db:
                report.errors.append("No se pudieron cargar los estudiantes desde bdtotall.xlsx")
                return report
            
            report.total_students_processed = len(students_db)
            self.logger.info(f"Estudiantes cargados: {len(students_db)}")
            
            # 2. Buscar archivos de cursos
            course_files = self._find_course_files(excel_directory)
            if not course_files:
                report.warnings.append("No se encontraron archivos alumnos_*.xlsx en el directorio")
                return report
            
            self.logger.info(f"Archivos de cursos encontrados: {len(course_files)}")
            
            # 3. Procesar cada archivo de curso secuencialmente
            for course_file in course_files:
                try:
                    course_result = self._process_course_file(course_file, students_db)
                    report.course_results.append(course_result)
                    report.total_courses_processed += 1
                    report.total_assignments_created += course_result.assigned_count
                    report.total_assignments_skipped += course_result.skipped_count
                    
                    # Agregar errores y advertencias del curso al reporte general
                    report.errors.extend(course_result.errors)
                    report.warnings.extend(course_result.warnings)
                    
                    self.logger.info(
                        f"Curso procesado: {course_result.course_name} "
                        f"(Asignados: {course_result.assigned_count}, "
                        f"Omitidos: {course_result.skipped_count})"
                    )
                    
                except Exception as e:
                    error_msg = f"Error procesando archivo {course_file}: {str(e)}"
                    self.logger.error(error_msg)
                    report.errors.append(error_msg)
            
            self.logger.info(
                f"Proceso completado. Cursos: {report.total_courses_processed}, "
                f"Asignaciones creadas: {report.total_assignments_created}, "
                f"Asignaciones omitidas: {report.total_assignments_skipped}"
            )
            
        except Exception as e:
            error_msg = f"Error general en el proceso de asignación: {str(e)}"
            self.logger.error(error_msg)
            report.errors.append(error_msg)
        
        return report
    
    def _load_all_students(self, excel_directory: str) -> Dict[str, StudentData]:
        """
        Carga todos los estudiantes desde el archivo bdtotall.xlsx
        
        Args:
            excel_directory: Directorio que contiene bdtotall.xlsx
            
        Returns:
            Diccionario {student_code: StudentData} con todos los estudiantes
        """
        bdtotall_path = os.path.join(excel_directory, 'bdtotall.xlsx')
        
        self.logger.info(f"Cargando estudiantes desde: {bdtotall_path}")
        
        if not os.path.exists(bdtotall_path):
            self.logger.error(f"Archivo bdtotall.xlsx no encontrado en: {bdtotall_path}")
            return {}
        
        # Leer archivo de estudiantes
        result = self.excel_reader.read_students_file(bdtotall_path)
        
        if not result.success:
            self.logger.error(f"Error leyendo bdtotall.xlsx: {result.error_message}")
            return {}
        
        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(f"Advertencia en bdtotall.xlsx: {warning}")
        
        students_data = result.data or {}
        self.logger.info(f"Estudiantes cargados exitosamente: {len(students_data)}")
        
        return students_data
    
    def _find_course_files(self, excel_directory: str) -> List[str]:
        """
        Busca automáticamente archivos alumnos_*.xlsx en el directorio
        
        Args:
            excel_directory: Directorio donde buscar los archivos
            
        Returns:
            Lista de rutas completas a los archivos encontrados
        """
        self.logger.info(f"Buscando archivos alumnos_*.xlsx en: {excel_directory}")
        
        # Patrón para buscar archivos alumnos_*.xlsx
        pattern = os.path.join(excel_directory, 'alumnos_*.xlsx')
        course_files = glob.glob(pattern)
        
        # Filtrar archivos válidos y ordenar
        valid_files = []
        for file_path in course_files:
            if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
                valid_files.append(file_path)
            else:
                self.logger.warning(f"Archivo inválido o vacío omitido: {file_path}")
        
        # Ordenar archivos por nombre para procesamiento consistente
        valid_files.sort()
        
        self.logger.info(f"Archivos válidos encontrados: {len(valid_files)}")
        for file_path in valid_files:
            self.logger.debug(f"  - {os.path.basename(file_path)}")
        
        return valid_files
    
    def _process_course_file(self, course_file_path: str, students_db: Dict[str, StudentData]) -> CourseAssignments:
        """
        Procesa un archivo de curso específico y crea las asignaciones
        
        Args:
            course_file_path: Ruta al archivo alumnos_*.xlsx
            students_db: Base de datos de estudiantes cargada desde bdtotall.xlsx
            
        Returns:
            CourseAssignments con el resultado del procesamiento
        """
        filename = os.path.basename(course_file_path)
        self.logger.info(f"Procesando archivo de curso: {filename}")
        
        # Inicializar resultado
        course_result = CourseAssignments(
            course_name="",
            course_id="",
            course_code=""
        )
        
        try:
            # 1. Extraer nombre del curso desde el nombre del archivo
            course_name = self.course_mapper.extract_course_name(filename)
            course_result.course_name = course_name
            
            self.logger.info(f"Nombre de curso extraído: {course_name}")
            
            # 2. Encontrar o crear el curso en la base de datos
            course_mapping = self.course_mapper.find_or_create_course(course_name)
            course_result.course_id = course_mapping.course_id
            course_result.course_code = course_mapping.course_code
            
            if course_mapping.created:
                course_result.warnings.append(f"Curso creado automáticamente: {course_name}")
            
            # 3. Leer códigos de estudiantes del archivo de curso
            excel_result = self.excel_reader.read_course_file(course_file_path)
            
            if not excel_result.success:
                course_result.errors.append(f"Error leyendo archivo: {excel_result.error_message}")
                return course_result
            
            student_codes = excel_result.data or []
            self.logger.info(f"Códigos de estudiantes encontrados en archivo: {len(student_codes)}")
            
            # 4. Procesar asignaciones para cada estudiante
            for student_code in student_codes:
                try:
                    assignment_result = self._process_student_assignment(
                        student_code, students_db, course_mapping
                    )
                    
                    if assignment_result['assigned']:
                        course_result.assigned_count += 1
                    elif assignment_result['skipped']:
                        course_result.skipped_count += 1
                    
                    if assignment_result['error']:
                        course_result.errors.append(assignment_result['error'])
                    
                    if assignment_result['warning']:
                        course_result.warnings.append(assignment_result['warning'])
                        
                except Exception as e:
                    error_msg = f"Error procesando estudiante {student_code}: {str(e)}"
                    course_result.errors.append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(
                f"Archivo procesado: {filename} - "
                f"Asignados: {course_result.assigned_count}, "
                f"Omitidos: {course_result.skipped_count}, "
                f"Errores: {len(course_result.errors)}"
            )
            
        except Exception as e:
            error_msg = f"Error general procesando archivo {filename}: {str(e)}"
            course_result.errors.append(error_msg)
            self.logger.error(error_msg)
        
        return course_result
    
    def _process_student_assignment(
        self, 
        student_code: str, 
        students_db: Dict[str, StudentData], 
        course_mapping: CourseMapping
    ) -> Dict:
        """
        Procesa la asignación de un estudiante específico a un curso
        
        Args:
            student_code: Código del estudiante
            students_db: Base de datos de estudiantes
            course_mapping: Información del curso
            
        Returns:
            Diccionario con resultado de la asignación
        """
        result = {
            'assigned': False,
            'skipped': False,
            'error': None,
            'warning': None
        }
        
        try:
            # Verificar que el estudiante existe en la base de datos principal
            if student_code not in students_db:
                result['warning'] = f"Estudiante {student_code} no encontrado en bdtotall.xlsx"
                return result
            
            student_data = students_db[student_code]
            
            # Usar el AssignmentProcessor para manejar la asignación
            assignment_result = self.assignment_processor.process_student_assignment(
                student_code, student_data, course_mapping
            )
            
            # Convertir resultado del AssignmentProcessor al formato esperado
            if assignment_result.success:
                if assignment_result.assigned:
                    result['assigned'] = True
                    self.logger.debug(f"Asignación creada: {student_code} -> {course_mapping.course_name}")
                elif assignment_result.skipped:
                    result['skipped'] = True
                    result['warning'] = assignment_result.warning_message
            else:
                result['error'] = assignment_result.error_message
            
            # Agregar advertencias si existen
            if assignment_result.warning_message and not result['warning']:
                result['warning'] = assignment_result.warning_message
            
        except Exception as e:
            result['error'] = f"Error procesando asignación de {student_code}: {str(e)}"
        
        return result
    
