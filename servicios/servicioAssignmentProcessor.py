"""
Procesador de asignaciones para manejar operaciones de base de datos
con verificación de duplicados y manejo robusto de errores
"""
import logging
import uuid
from typing import Optional, Dict, Any
from dataclasses import dataclass
from django.db import connection, transaction, IntegrityError, DatabaseError

from .servicioExcelReader import StudentData
from .servicioCourseMapperSimple import CourseMapping


@dataclass
class AssignmentResult:
    """Resultado de una operación de asignación individual"""
    success: bool
    assigned: bool = False
    skipped: bool = False
    error_message: Optional[str] = None
    warning_message: Optional[str] = None
    student_id: Optional[str] = None
    enrollment_id: Optional[str] = None


class AssignmentProcessor:
    """
    Procesador especializado para manejar asignaciones de estudiantes a cursos
    con verificación de duplicados, manejo de errores de base de datos y transacciones.
    
    Responsabilidades:
    - Verificar duplicados antes de crear asignaciones
    - Manejar errores de base de datos y transacciones
    - Crear lógica para omitir asignaciones existentes
    - Proporcionar logging detallado de operaciones
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process_student_assignment(
        self, 
        student_code: str, 
        student_data: StudentData, 
        course_mapping: CourseMapping
    ) -> AssignmentResult:
        """
        Procesa la asignación de un estudiante específico a un curso
        
        Args:
            student_code: Código del estudiante
            student_data: Datos completos del estudiante
            course_mapping: Información del curso
            
        Returns:
            AssignmentResult con el resultado detallado de la operación
        """
        self.logger.debug(f"Procesando asignación: {student_code} -> {course_mapping.course_name}")
        
        try:
            # 1. Verificar si ya existe la asignación
            if self._assignment_exists(student_code, course_mapping.course_id):
                return AssignmentResult(
                    success=True,
                    skipped=True,
                    warning_message=f"Asignación ya existe para estudiante {student_code} en curso {course_mapping.course_name}"
                )
            
            # 2. Crear la asignación con manejo de transacciones
            return self._create_assignment_with_transaction(student_data, course_mapping)
            
        except Exception as e:
            error_msg = f"Error inesperado procesando asignación de {student_code}: {str(e)}"
            self.logger.error(error_msg)
            return AssignmentResult(
                success=False,
                error_message=error_msg
            )
    
    def _assignment_exists(self, student_code: str, course_id: str) -> bool:
        """
        Verifica si ya existe una asignación para el estudiante y curso
        
        Args:
            student_code: Código del estudiante
            course_id: ID del curso
            
        Returns:
            True si la asignación ya existe
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM enrollments e
                    JOIN students s ON e.student_id = s.id
                    JOIN course_groups cg ON e.course_group_id = cg.id
                    WHERE s.student_code = %s AND cg.course_id = %s
                """, [student_code, course_id])
                
                count = cursor.fetchone()[0]
                exists = count > 0
                
                if exists:
                    self.logger.debug(f"Asignación existente encontrada: {student_code} -> {course_id}")
                
                return exists
                
        except DatabaseError as e:
            self.logger.error(f"Error de base de datos verificando asignación existente: {str(e)}")
            # En caso de error, asumimos que no existe para intentar crear
            return False
        except Exception as e:
            self.logger.error(f"Error inesperado verificando asignación existente: {str(e)}")
            return False
    
    def _create_assignment_with_transaction(
        self, 
        student_data: StudentData, 
        course_mapping: CourseMapping
    ) -> AssignmentResult:
        """
        Crea una nueva asignación usando transacciones atómicas
        
        Args:
            student_data: Datos del estudiante
            course_mapping: Información del curso
            
        Returns:
            AssignmentResult con el resultado de la operación
        """
        try:
            with transaction.atomic():
                # 1. Buscar o crear el estudiante
                student_result = self._find_or_create_student(student_data)
                if not student_result['success']:
                    return AssignmentResult(
                        success=False,
                        error_message=student_result['error']
                    )
                
                student_id = student_result['student_id']
                
                # 2. Buscar o crear grupo de curso
                course_group_result = self._find_or_create_course_group(course_mapping.course_id)
                if not course_group_result['success']:
                    return AssignmentResult(
                        success=False,
                        error_message=course_group_result['error']
                    )
                
                course_group_id = course_group_result['course_group_id']
                
                # 3. Obtener período académico activo
                academic_period_result = self._get_or_create_active_academic_period()
                if not academic_period_result['success']:
                    return AssignmentResult(
                        success=False,
                        error_message=academic_period_result['error']
                    )
                
                academic_period_id = academic_period_result['period_id']
                
                # 4. Crear la matrícula
                enrollment_result = self._create_enrollment(
                    student_id, course_group_id, academic_period_id
                )
                
                if enrollment_result['success']:
                    self.logger.debug(
                        f"Asignación creada exitosamente: {student_data.student_code} -> {course_mapping.course_name}"
                    )
                    return AssignmentResult(
                        success=True,
                        assigned=True,
                        student_id=student_id,
                        enrollment_id=enrollment_result['enrollment_id']
                    )
                else:
                    return AssignmentResult(
                        success=False,
                        error_message=enrollment_result['error']
                    )
                    
        except IntegrityError as e:
            # Error de integridad (duplicados, constraints, etc.)
            error_msg = f"Error de integridad creando asignación para {student_data.student_code}: {str(e)}"
            self.logger.warning(error_msg)
            return AssignmentResult(
                success=True,  # No es un error fatal, probablemente duplicado
                skipped=True,
                warning_message=error_msg
            )
        except DatabaseError as e:
            # Error de base de datos
            error_msg = f"Error de base de datos creando asignación para {student_data.student_code}: {str(e)}"
            self.logger.error(error_msg)
            return AssignmentResult(
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            # Error inesperado
            error_msg = f"Error inesperado creando asignación para {student_data.student_code}: {str(e)}"
            self.logger.error(error_msg)
            return AssignmentResult(
                success=False,
                error_message=error_msg
            )
    
    def _find_or_create_student(self, student_data: StudentData) -> Dict[str, Any]:
        """
        Busca o crea un estudiante en la base de datos
        
        Args:
            student_data: Datos del estudiante
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            with connection.cursor() as cursor:
                # Buscar estudiante existente por código
                cursor.execute(
                    "SELECT id FROM students WHERE student_code = %s",
                    [student_data.student_code]
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'success': True,
                        'student_id': result[0],
                        'created': False
                    }
                
                # Crear nuevo estudiante
                return self._create_new_student(student_data)
                
        except DatabaseError as e:
            return {
                'success': False,
                'error': f"Error de base de datos buscando estudiante {student_data.student_code}: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado buscando estudiante {student_data.student_code}: {str(e)}"
            }
    
    def _create_new_student(self, student_data: StudentData) -> Dict[str, Any]:
        """
        Crea un nuevo estudiante y su usuario asociado
        
        Args:
            student_data: Datos del estudiante
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            with connection.cursor() as cursor:
                # Verificar si ya existe un usuario con el mismo email
                cursor.execute(
                    "SELECT id FROM users WHERE institutional_email = %s",
                    [student_data.email]
                )
                user_result = cursor.fetchone()
                
                if user_result:
                    user_id = user_result[0]
                else:
                    # Crear nuevo usuario
                    user_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO users (
                            id, institutional_email, email, first_name, last_name, 
                            role, is_active, date_joined, password
                        ) VALUES (%s, %s, %s, %s, %s, 'student', TRUE, NOW(), %s)
                    """, [user_id, student_data.email, student_data.email, student_data.first_name, student_data.last_name, 'pbkdf2_sha256$260000$temp$temp'])
                
                # Crear el estudiante
                student_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO students (
                        id, user_id, student_code, academic_status
                    ) VALUES (%s, %s, %s, 'active')
                """, [student_id, user_id, student_data.student_code])
                
                self.logger.debug(f"Estudiante creado: {student_data.student_code}")
                
                return {
                    'success': True,
                    'student_id': student_id,
                    'created': True
                }
                
        except IntegrityError as e:
            return {
                'success': False,
                'error': f"Error de integridad creando estudiante {student_data.student_code}: {str(e)}"
            }
        except DatabaseError as e:
            return {
                'success': False,
                'error': f"Error de base de datos creando estudiante {student_data.student_code}: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado creando estudiante {student_data.student_code}: {str(e)}"
            }
    
    def _find_or_create_course_group(self, course_id: str) -> Dict[str, Any]:
        """
        Busca o crea un grupo de curso por defecto
        
        Args:
            course_id: ID del curso
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            with connection.cursor() as cursor:
                # Obtener período académico activo
                academic_period_result = self._get_or_create_active_academic_period()
                if not academic_period_result['success']:
                    return {
                        'success': False,
                        'error': academic_period_result['error']
                    }
                
                academic_period_id = academic_period_result['period_id']
                
                # Buscar grupo existente
                cursor.execute("""
                    SELECT id FROM course_groups 
                    WHERE course_id = %s AND academic_period_id = %s
                    ORDER BY group_code LIMIT 1
                """, [course_id, academic_period_id])
                
                result = cursor.fetchone()
                if result:
                    return {
                        'success': True,
                        'course_group_id': result[0],
                        'created': False
                    }
                
                # Crear nuevo grupo por defecto
                group_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO course_groups (
                        id, course_id, academic_period_id, group_code, 
                        capacity, enrolled_students, created_at
                    ) VALUES (%s, %s, %s, 'A', 50, 0, NOW())
                """, [group_id, course_id, academic_period_id])
                
                self.logger.debug(f"Grupo de curso creado: {course_id} - Grupo A")
                
                return {
                    'success': True,
                    'course_group_id': group_id,
                    'created': True
                }
                
        except DatabaseError as e:
            return {
                'success': False,
                'error': f"Error de base de datos creando grupo de curso: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado creando grupo de curso: {str(e)}"
            }
    
    def _get_or_create_active_academic_period(self) -> Dict[str, Any]:
        """
        Obtiene o crea el período académico activo
        
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM academic_periods WHERE is_active = TRUE LIMIT 1"
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'success': True,
                        'period_id': result[0],
                        'created': False
                    }
                
                # Si no hay período activo, crear uno por defecto
                from datetime import date, timedelta
                
                period_id = str(uuid.uuid4())
                today = date.today()
                end_date = today + timedelta(days=120)  # 4 meses
                
                cursor.execute("""
                    INSERT INTO academic_periods (
                        id, name, start_date, end_date, 
                        laboratory_enrollment_start, laboratory_enrollment_end,
                        enrollment_change_deadline, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                """, [
                    period_id, f"{today.year}-AUTO", today, end_date,
                    today, end_date, end_date, 
                ])
                
                self.logger.info(f"Período académico creado automáticamente: {today.year}-AUTO")
                
                return {
                    'success': True,
                    'period_id': period_id,
                    'created': True
                }
                
        except DatabaseError as e:
            return {
                'success': False,
                'error': f"Error de base de datos obteniendo período académico: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado obteniendo período académico: {str(e)}"
            }
    
    def _create_enrollment(
        self, 
        student_id: str, 
        course_group_id: str, 
        academic_period_id: str
    ) -> Dict[str, Any]:
        """
        Crea una nueva matrícula
        
        Args:
            student_id: ID del estudiante
            course_group_id: ID del grupo de curso
            academic_period_id: ID del período académico
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            with connection.cursor() as cursor:
                # Verificar duplicado una vez más antes de insertar
                cursor.execute("""
                    SELECT COUNT(*) FROM enrollments 
                    WHERE student_id = %s AND course_group_id = %s AND academic_period_id = %s
                """, [student_id, course_group_id, academic_period_id])
                
                if cursor.fetchone()[0] > 0:
                    return {
                        'success': True,  # No es error, solo duplicado
                        'skipped': True,
                        'warning': 'Matrícula ya existe'
                    }
                
                # Crear la matrícula
                enrollment_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO enrollments (
                        id, student_id, course_group_id, academic_period_id,
                        enrollment_date, enrollment_type, status
                    ) VALUES (%s, %s, %s, %s, CURRENT_DATE, 'regular', 'active')
                """, [enrollment_id, student_id, course_group_id, academic_period_id])
                
                # Actualizar contador de estudiantes matriculados
                cursor.execute("""
                    UPDATE course_groups 
                    SET enrolled_students = enrolled_students + 1 
                    WHERE id = %s
                """, [course_group_id])
                
                return {
                    'success': True,
                    'enrollment_id': enrollment_id
                }
                
        except IntegrityError as e:
            return {
                'success': True,  # No es error fatal, probablemente duplicado
                'skipped': True,
                'warning': f'Error de integridad en matrícula: {str(e)}'
            }
        except DatabaseError as e:
            return {
                'success': False,
                'error': f"Error de base de datos creando matrícula: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado creando matrícula: {str(e)}"
            }
    
    def get_assignment_statistics(self, course_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de asignaciones
        
        Args:
            course_id: ID del curso específico (opcional)
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            with connection.cursor() as cursor:
                if course_id:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_enrollments,
                            COUNT(DISTINCT e.student_id) as unique_students,
                            COUNT(DISTINCT cg.course_id) as unique_courses
                        FROM enrollments e
                        JOIN course_groups cg ON e.course_group_id = cg.id
                        WHERE cg.course_id = %s
                    """, [course_id])
                else:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_enrollments,
                            COUNT(DISTINCT e.student_id) as unique_students,
                            COUNT(DISTINCT cg.course_id) as unique_courses
                        FROM enrollments e
                        JOIN course_groups cg ON e.course_group_id = cg.id
                    """)
                
                result = cursor.fetchone()
                
                return {
                    'success': True,
                    'total_enrollments': result[0],
                    'unique_students': result[1],
                    'unique_courses': result[2]
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }