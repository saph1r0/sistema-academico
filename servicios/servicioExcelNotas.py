"""
Servicio para procesamiento de archivos Excel de notas por fases académicas
"""
import pandas as pd
import logging
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.exceptions import ValidationError
from repositorio.postgres_repository.models import Student, CourseGroup, PhaseGrade, Teacher

logger = logging.getLogger(__name__)


class ExcelGradeTemplateProcessor:
    """Procesador de plantillas Excel para notas por fases académicas"""
    
    def __init__(self):
        self.results = {
            'success': False,
            'processed_count': 0,
            'updated_count': 0,
            'errors': [],
            'warnings': [],
            'invalid_students': [],
            'statistics': {}
        }
    
    def process_excel_template(self, file_path_or_buffer, expected_columns=None):
        """
        Procesa una plantilla Excel de notas P1 con validación de formato
        
        Args:
            file_path_or_buffer: Ruta del archivo o buffer de archivo Excel
            expected_columns: Lista de columnas esperadas (opcional)
            
        Returns:
            dict: Resultados del procesamiento con datos validados
        """
        try:
            # Leer Excel con diferentes headers para encontrar la estructura correcta
            df = self._read_excel_with_header_detection(file_path_or_buffer)
            
            if df is None:
                self.results['errors'].append("No se pudo detectar la estructura correcta del archivo Excel")
                return self.results
            
            # Validar formato de la plantilla
            validation_result = self._validate_template_format(df, expected_columns)
            if not validation_result['valid']:
                self.results['errors'].extend(validation_result['errors'])
                return self.results
            
            # Procesar y validar datos
            processed_data = self._process_and_validate_data(df)
            
            if processed_data:
                self.results['success'] = True
                self.results['processed_data'] = processed_data
                self.results['processed_count'] = len(processed_data)
                
                logger.info(f"Excel procesado exitosamente: {len(processed_data)} registros válidos")
            else:
                self.results['errors'].append("No se encontraron datos válidos para procesar")
                
        except Exception as e:
            error_msg = f"Error al procesar archivo Excel: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
        
        return self.results
    
    def _read_excel_with_header_detection(self, file_path_or_buffer):
        """
        Lee el archivo Excel detectando automáticamente la fila de headers
        
        Returns:
            DataFrame o None si no se puede detectar la estructura
        """
        try:
            # Probar diferentes filas como header (basado en el análisis previo)
            header_candidates = [9, 8, 10, 0, 1, 2]  # Fila 10 (índice 9) es la más común
            
            for header_row in header_candidates:
                try:
                    df = pd.read_excel(file_path_or_buffer, header=header_row)
                    
                    # Verificar si esta fila contiene headers válidos
                    if self._is_valid_header_row(df):
                        logger.info(f"Header detectado en fila {header_row + 1}")
                        return df
                        
                except Exception as e:
                    continue
            
            # Si no se encuentra header automáticamente, intentar sin header
            df = pd.read_excel(file_path_or_buffer, header=None)
            logger.warning("No se detectó header automáticamente, usando primera fila como datos")
            return df
            
        except Exception as e:
            logger.error(f"Error leyendo archivo Excel: {str(e)}")
            return None
    
    def _is_valid_header_row(self, df):
        """
        Verifica si el DataFrame tiene headers válidos para notas P1
        
        Returns:
            bool: True si los headers son válidos
        """
        if df.empty or len(df.columns) < 2:
            return False
        
        columns_str = [str(col).upper() for col in df.columns]
        
        # Buscar columnas de código de estudiante
        code_keywords = ['CUI', 'CODIGO', 'CODE', 'ESTUDIANTE', 'ALUMNO', 'STUDENT']
        has_code_column = any(
            any(keyword in col for keyword in code_keywords) 
            for col in columns_str
        )
        
        # Buscar columnas de notas
        grade_keywords = ['P1', 'PARCIAL', 'NOTA', 'GRADE', 'CONTINUA']
        has_grade_column = any(
            any(keyword in col for keyword in grade_keywords) 
            for col in columns_str
        )
        
        return has_code_column and has_grade_column
    
    def _validate_template_format(self, df, expected_columns=None):
        """
        Valida que la plantilla Excel tenga el formato correcto
        
        Returns:
            dict: Resultado de validación con errores si los hay
        """
        result = {'valid': True, 'errors': [], 'warnings': []}
        
        if df.empty:
            result['valid'] = False
            result['errors'].append("El archivo Excel está vacío")
            return result
        
        # Detectar columnas de código de estudiante
        code_column = self._detect_student_code_column(df)
        if not code_column:
            result['valid'] = False
            result['errors'].append("No se encontró columna de código de estudiante (CUI)")
            return result
        
        # Detectar columnas de notas
        grade_columns = self._detect_grade_columns(df)
        if not grade_columns:
            result['valid'] = False
            result['errors'].append("No se encontraron columnas de notas válidas")
            return result
        
        # Validar que tenemos al menos las columnas requeridas para P1
        required_grade_types = ['partial', 'continuous']  # Nota parcial y continua
        found_types = set(grade_columns.keys())
        
        if not all(req_type in found_types for req_type in required_grade_types):
            missing = set(required_grade_types) - found_types
            result['warnings'].append(f"Faltan tipos de nota: {missing}")
        
        # Validar que hay datos
        if len(df) == 0:
            result['valid'] = False
            result['errors'].append("No hay filas de datos en el archivo")
        
        return result
    
    def _detect_student_code_column(self, df):
        """
        Detecta la columna que contiene códigos de estudiante
        
        Returns:
            str: Nombre de la columna o None si no se encuentra
        """
        code_keywords = ['CUI', 'CODIGO', 'CODE', 'ESTUDIANTE', 'ALUMNO', 'STUDENT']
        
        for col in df.columns:
            col_str = str(col).upper()
            if any(keyword in col_str for keyword in code_keywords):
                return col
        
        return None
    
    def _detect_grade_columns(self, df):
        """
        Detecta las columnas que contienen notas
        
        Returns:
            dict: Mapeo de tipo de nota a nombre de columna
        """
        grade_columns = {}
        
        for col in df.columns:
            col_str = str(col).upper()
            
            # Detectar nota parcial
            if any(keyword in col_str for keyword in ['P1', 'PARCIAL']):
                grade_columns['partial'] = col
            
            # Detectar nota continua
            elif any(keyword in col_str for keyword in ['CONTINUA', 'CONTINUOUS', 'C1']):
                grade_columns['continuous'] = col
            
            # Detectar otras notas genéricas
            elif any(keyword in col_str for keyword in ['NOTA', 'GRADE']) and 'FINAL' not in col_str:
                if 'partial' not in grade_columns:
                    grade_columns['partial'] = col
                elif 'continuous' not in grade_columns:
                    grade_columns['continuous'] = col
        
        return grade_columns
    
    def _process_and_validate_data(self, df):
        """
        Procesa y valida los datos del DataFrame
        
        Returns:
            list: Lista de registros válidos para procesar
        """
        processed_data = []
        
        # Detectar columnas
        code_column = self._detect_student_code_column(df)
        grade_columns = self._detect_grade_columns(df)
        
        if not code_column or not grade_columns:
            return processed_data
        
        for index, row in df.iterrows():
            try:
                # Validar y procesar código de estudiante
                student_code = self._validate_student_code(row[code_column], index)
                if not student_code:
                    continue
                
                # Validar y procesar notas
                grades = {}
                for grade_type, column in grade_columns.items():
                    grade_value = self._validate_grade_value(row[column], grade_type, student_code, index)
                    if grade_value is not None:
                        grades[grade_type] = grade_value
                
                # Solo incluir si tenemos al menos una nota válida
                if grades:
                    processed_data.append({
                        'student_code': student_code,
                        'grades': grades,
                        'row_index': index + 1
                    })
                
            except Exception as e:
                self.results['warnings'].append(f"Error procesando fila {index + 1}: {str(e)}")
        
        return processed_data
    
    def _validate_student_code(self, code_value, row_index):
        """
        Valida y normaliza un código de estudiante
        
        Returns:
            str: Código normalizado o None si es inválido
        """
        if pd.isna(code_value):
            return None
        
        try:
            # Convertir a string, manejando números flotantes
            if isinstance(code_value, float):
                code_str = str(int(code_value))
            else:
                code_str = str(code_value).strip()
            
            # Validar que no esté vacío
            if not code_str or code_str.lower() in ['nan', 'none', '']:
                return None
            
            return code_str
            
        except (ValueError, TypeError):
            self.results['warnings'].append(f"Código de estudiante inválido en fila {row_index + 1}: {code_value}")
            return None
    
    def _validate_grade_value(self, grade_value, grade_type, student_code, row_index):
        """
        Valida un valor de nota
        
        Returns:
            Decimal: Nota válida o None si es inválida
        """
        if pd.isna(grade_value):
            return None
        
        try:
            # Convertir a decimal
            grade_decimal = Decimal(str(grade_value))
            
            # Validar rango (0-20)
            if grade_decimal < 0 or grade_decimal > 20:
                self.results['warnings'].append(
                    f"Nota fuera de rango ({grade_decimal}) para estudiante {student_code} "
                    f"en fila {row_index + 1}, tipo: {grade_type}"
                )
                return None
            
            return grade_decimal
            
        except (ValueError, TypeError, InvalidOperation):
            self.results['warnings'].append(
                f"Nota inválida '{grade_value}' para estudiante {student_code} "
                f"en fila {row_index + 1}, tipo: {grade_type}"
            )
            return None
    
    def get_processing_summary(self):
        """
        Retorna un resumen del procesamiento
        
        Returns:
            dict: Resumen con estadísticas y errores
        """
        return {
            'success': self.results['success'],
            'total_processed': self.results['processed_count'],
            'total_updated': self.results['updated_count'],
            'total_errors': len(self.results['errors']),
            'total_warnings': len(self.results['warnings']),
            'errors': self.results['errors'],
            'warnings': self.results['warnings'][:10],  # Limitar warnings mostrados
            'invalid_students': self.results['invalid_students'][:10]  # Limitar estudiantes inválidos
        }


class GradeUploadService:
    """Servicio para subir notas procesadas desde Excel a la base de datos"""
    
    def __init__(self, teacher_id):
        self.teacher_id = teacher_id
        self.results = {
            'success': False,
            'created_count': 0,
            'updated_count': 0,
            'errors': [],
            'warnings': [],
            'invalid_students': [],
            'statistics': {}
        }
    
    def upload_phase_grades(self, processed_data, course_group_id, phase='primera'):
        """
        Sube las notas procesadas a la base de datos
        
        Args:
            processed_data: Lista de datos procesados del ExcelGradeTemplateProcessor
            course_group_id: ID del grupo de curso
            phase: Fase académica ('primera', 'segunda', 'tercera')
            
        Returns:
            dict: Resultados de la subida con estadísticas
        """
        try:
            with transaction.atomic():
                # Validar teacher y course_group
                teacher = self._validate_teacher()
                course_group = self._validate_course_group(course_group_id)
                
                if not teacher or not course_group:
                    return self.results
                
                # Procesar cada registro
                for record in processed_data:
                    self._process_student_grades(record, course_group, phase, teacher)
                
                # Calcular estadísticas finales
                self._calculate_upload_statistics(course_group, phase)
                
                self.results['success'] = True
                logger.info(f"Notas subidas exitosamente: {self.results['created_count']} creadas, "
                           f"{self.results['updated_count']} actualizadas")
                
        except Exception as e:
            error_msg = f"Error al subir notas: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
        
        return self.results
    
    def _validate_teacher(self):
        """Valida que el profesor existe y está activo"""
        try:
            teacher = Teacher.objects.get(id=self.teacher_id)
            return teacher
        except Teacher.DoesNotExist:
            self.results['errors'].append(f"Profesor con ID {self.teacher_id} no encontrado")
            return None
    
    def _validate_course_group(self, course_group_id):
        """Valida que el grupo de curso existe"""
        try:
            course_group = CourseGroup.objects.get(id=course_group_id)
            return course_group
        except CourseGroup.DoesNotExist:
            self.results['errors'].append(f"Grupo de curso con ID {course_group_id} no encontrado")
            return None
    
    def _process_student_grades(self, record, course_group, phase, teacher):
        """
        Procesa las notas de un estudiante individual
        
        Args:
            record: Registro con datos del estudiante y notas
            course_group: Instancia de CourseGroup
            phase: Fase académica
            teacher: Instancia de Teacher
        """
        try:
            student_code = record['student_code']
            grades = record['grades']
            
            # Buscar estudiante por código
            try:
                student = Student.objects.get(student_code=student_code)
            except Student.DoesNotExist:
                self.results['invalid_students'].append(student_code)
                self.results['warnings'].append(f"Estudiante con código {student_code} no encontrado")
                return
            
            # Verificar que el estudiante esté matriculado en el curso
            if not self._is_student_enrolled(student, course_group):
                self.results['warnings'].append(
                    f"Estudiante {student_code} no está matriculado en {course_group}"
                )
                return
            
            # Preparar datos de notas
            partial_grade = grades.get('partial')
            continuous_grade = grades.get('continuous')
            
            # Verificar que tenemos al menos una nota
            if partial_grade is None and continuous_grade is None:
                self.results['warnings'].append(f"No hay notas válidas para estudiante {student_code}")
                return
            
            # Crear o actualizar registro de PhaseGrade
            phase_grade, created = PhaseGrade.objects.update_or_create(
                student=student,
                course_group=course_group,
                phase=phase,
                defaults={
                    'partial_grade': partial_grade or Decimal('0.00'),
                    'continuous_grade': continuous_grade or Decimal('0.00'),
                    'uploaded_by': teacher
                }
            )
            
            if created:
                self.results['created_count'] += 1
                logger.info(f"Nota creada para {student_code}: P={partial_grade}, C={continuous_grade}")
            else:
                self.results['updated_count'] += 1
                logger.info(f"Nota actualizada para {student_code}: P={partial_grade}, C={continuous_grade}")
                
        except Exception as e:
            error_msg = f"Error procesando estudiante {record.get('student_code', 'desconocido')}: {str(e)}"
            self.results['errors'].append(error_msg)
            logger.error(error_msg)
    
    def _is_student_enrolled(self, student, course_group):
        """
        Verifica si un estudiante está matriculado en el grupo de curso
        
        Returns:
            bool: True si está matriculado
        """
        from repositorio.postgres_repository.models import Enrollment
        
        try:
            return Enrollment.objects.filter(
                student=student,
                course_group=course_group,
                status='active'
            ).exists()
        except Exception:
            # Si no existe la tabla de matrículas, asumir que está matriculado
            return True
    
    def _calculate_upload_statistics(self, course_group, phase):
        """
        Calcula estadísticas de las notas subidas
        
        Args:
            course_group: Instancia de CourseGroup
            phase: Fase académica
        """
        try:
            # Obtener todas las notas de la fase
            phase_grades = PhaseGrade.objects.filter(
                course_group=course_group,
                phase=phase
            ).exclude(
                final_phase_grade__isnull=True
            )
            
            if not phase_grades.exists():
                return
            
            # Calcular estadísticas
            grades_values = [pg.final_phase_grade for pg in phase_grades if pg.final_phase_grade]
            
            if grades_values:
                self.results['statistics'] = {
                    'total_students': len(grades_values),
                    'max_grade': float(max(grades_values)),
                    'min_grade': float(min(grades_values)),
                    'avg_grade': float(sum(grades_values) / len(grades_values)),
                    'passed_count': len([g for g in grades_values if g >= Decimal('10.5')]),
                    'failed_count': len([g for g in grades_values if g < Decimal('10.5')])
                }
                
                # Calcular tasa de aprobación
                total = self.results['statistics']['total_students']
                passed = self.results['statistics']['passed_count']
                self.results['statistics']['pass_rate'] = (passed / total * 100) if total > 0 else 0
                
        except Exception as e:
            logger.warning(f"Error calculando estadísticas: {str(e)}")
    
    def check_duplicate_grades(self, course_group_id, phase='primera'):
        """
        Verifica si ya existen notas para la fase en el curso
        
        Returns:
            dict: Información sobre duplicados
        """
        try:
            existing_count = PhaseGrade.objects.filter(
                course_group_id=course_group_id,
                phase=phase
            ).count()
            
            return {
                'has_existing_grades': existing_count > 0,
                'existing_count': existing_count,
                'message': f"Ya existen {existing_count} notas para {phase} fase" if existing_count > 0 else "No hay notas existentes"
            }
            
        except Exception as e:
            return {
                'has_existing_grades': False,
                'existing_count': 0,
                'error': str(e)
            }
    
    def get_upload_summary(self):
        """
        Retorna un resumen detallado de la subida
        
        Returns:
            dict: Resumen con estadísticas y resultados
        """
        summary = {
            'success': self.results['success'],
            'grades_created': self.results['created_count'],
            'grades_updated': self.results['updated_count'],
            'total_processed': self.results['created_count'] + self.results['updated_count'],
            'errors_count': len(self.results['errors']),
            'warnings_count': len(self.results['warnings']),
            'invalid_students_count': len(self.results['invalid_students']),
            'statistics': self.results.get('statistics', {})
        }
        
        # Agregar detalles de errores y warnings (limitados)
        summary['errors'] = self.results['errors'][:5]  # Primeros 5 errores
        summary['warnings'] = self.results['warnings'][:10]  # Primeros 10 warnings
        summary['invalid_students'] = self.results['invalid_students'][:10]  # Primeros 10 estudiantes inválidos
        
        return summary


class ExcelGradeProcessingService:
    """Servicio principal que combina procesamiento y subida de notas Excel"""
    
    def __init__(self, teacher_id):
        self.teacher_id = teacher_id
        self.processor = ExcelGradeTemplateProcessor()
        self.uploader = GradeUploadService(teacher_id)
    
    def process_and_upload_grades(self, file_path_or_buffer, course_group_id, phase='primera', 
                                 expected_columns=None, allow_duplicates=False):
        """
        Procesa un archivo Excel y sube las notas a la base de datos
        
        Args:
            file_path_or_buffer: Archivo Excel a procesar
            course_group_id: ID del grupo de curso
            phase: Fase académica ('primera', 'segunda', 'tercera')
            expected_columns: Columnas esperadas (opcional)
            allow_duplicates: Si permitir actualizar notas existentes
            
        Returns:
            dict: Resultado completo del procesamiento y subida
        """
        result = {
            'success': False,
            'processing_result': {},
            'upload_result': {},
            'summary': {}
        }
        
        try:
            # Verificar duplicados si no se permiten
            if not allow_duplicates:
                duplicate_check = self.uploader.check_duplicate_grades(course_group_id, phase)
                if duplicate_check['has_existing_grades']:
                    result['error'] = f"Ya existen notas para {phase} fase. Use allow_duplicates=True para actualizar."
                    result['duplicate_info'] = duplicate_check
                    return result
            
            # Procesar archivo Excel
            processing_result = self.processor.process_excel_template(file_path_or_buffer, expected_columns)
            result['processing_result'] = processing_result
            
            if not processing_result['success']:
                result['error'] = "Error en el procesamiento del archivo Excel"
                return result
            
            # Subir notas a la base de datos
            processed_data = processing_result.get('processed_data', [])
            if not processed_data:
                result['error'] = "No hay datos válidos para subir"
                return result
            
            upload_result = self.uploader.upload_phase_grades(processed_data, course_group_id, phase)
            result['upload_result'] = upload_result
            
            # Generar resumen combinado
            result['summary'] = self._generate_combined_summary(processing_result, upload_result)
            result['success'] = upload_result['success']
            
        except Exception as e:
            result['error'] = f"Error en el procesamiento completo: {str(e)}"
            logger.error(result['error'])
        
        return result
    
    def _generate_combined_summary(self, processing_result, upload_result):
        """
        Genera un resumen combinado del procesamiento y subida
        
        Returns:
            dict: Resumen completo
        """
        return {
            'excel_processing': {
                'rows_processed': processing_result.get('processed_count', 0),
                'errors': len(processing_result.get('errors', [])),
                'warnings': len(processing_result.get('warnings', []))
            },
            'database_upload': {
                'grades_created': upload_result.get('created_count', 0),
                'grades_updated': upload_result.get('updated_count', 0),
                'invalid_students': len(upload_result.get('invalid_students', [])),
                'errors': len(upload_result.get('errors', []))
            },
            'statistics': upload_result.get('statistics', {}),
            'total_success': processing_result.get('success', False) and upload_result.get('success', False)
        }