"""
Servicio para leer Excel y crear clases reales con datos de profesores y estudiantes
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date, time
import openpyxl
import pandas as pd
from django.db import transaction
from django.utils import timezone

from repositorio.postgres_repository.models import (
    User, Teacher, Student, Course, CourseGroup, AcademicPeriod,
    Enrollment, AttendanceRecord, Grade
)


# Configurar logging
logger = logging.getLogger(__name__)


@dataclass
class TeacherData:
    """Estructura de datos para profesor"""
    full_name: str
    email: str
    first_name: str = ""
    last_name: str = ""
    teacher_code: str = ""
    
    def __post_init__(self):
        """Procesar nombre completo después de inicialización"""
        if self.full_name and not (self.first_name and self.last_name):
            # Separar nombre completo en nombres y apellidos
            parts = self.full_name.strip().split()
            if len(parts) >= 2:
                # Asumir que el primer elemento son los nombres y el resto apellidos
                self.first_name = parts[0]
                self.last_name = " ".join(parts[1:])
            else:
                self.first_name = self.full_name
                self.last_name = ""


@dataclass
class ClassData:
    """Estructura de datos para una clase real"""
    course_name: str
    teacher_email: str
    teacher_name: str
    student_codes: List[str]
    schedule_info: Dict = None
    classroom: str = ""
    
    def __post_init__(self):
        if self.schedule_info is None:
            self.schedule_info = {}


@dataclass
class ProcessResult:
    """Resultado del procesamiento"""
    success: bool
    message: str = ""
    data: Optional[Dict] = None
    warnings: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class ServicioClasesReales:
    """
    Servicio para leer archivos Excel y crear clases reales con profesores y estudiantes
    
    Funcionalidades:
    - Lee archivo de profesores (EXELS/profesores.xlsx)
    - Lee archivos de cursos con estudiantes (EXELS/alumnos_*.xlsx)
    - Crea usuarios y profesores en la base de datos
    - Asigna profesores a cursos
    - Matricula estudiantes en cursos
    - Genera datos de asistencia y notas simuladas
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def procesar_excel_completo(self, excel_dir: str = "EXELS") -> ProcessResult:
        """
        Procesa todos los archivos Excel para crear clases reales
        
        Args:
            excel_dir: Directorio con archivos Excel
            
        Returns:
            ProcessResult con el resultado del procesamiento
        """
        self.logger.info("Iniciando procesamiento completo de Excel para clases reales")
        
        try:
            with transaction.atomic():
                # 1. Leer y procesar profesores
                teachers_result = self._procesar_profesores(excel_dir)
                if not teachers_result.success:
                    return teachers_result
                
                # 2. Leer y procesar estudiantes por curso
                courses_result = self._procesar_cursos_estudiantes(excel_dir)
                if not courses_result.success:
                    return courses_result
                
                # 3. Crear clases reales (asignar profesores a cursos)
                classes_result = self._crear_clases_reales(
                    teachers_result.data, 
                    courses_result.data
                )
                if not classes_result.success:
                    return classes_result
                
                # 4. Generar datos simulados de asistencia y notas
                simulation_result = self._generar_datos_simulados()
                
                # Compilar resultado final
                total_warnings = (teachers_result.warnings + 
                                courses_result.warnings + 
                                classes_result.warnings)
                
                return ProcessResult(
                    success=True,
                    message="Clases reales creadas exitosamente",
                    data={
                        'teachers_created': teachers_result.data.get('created', 0),
                        'courses_processed': len(courses_result.data),
                        'classes_created': classes_result.data.get('created', 0),
                        'simulation_data': simulation_result.data if simulation_result.success else None
                    },
                    warnings=total_warnings
                )
                
        except Exception as e:
            error_msg = f"Error en procesamiento completo: {str(e)}"
            self.logger.error(error_msg)
            return ProcessResult(
                success=False,
                message=error_msg
            )
    
    def _procesar_profesores(self, excel_dir: str) -> ProcessResult:
        """
        Lee el archivo de profesores y crea usuarios/profesores en la BD
        
        Args:
            excel_dir: Directorio con archivos Excel
            
        Returns:
            ProcessResult con profesores creados
        """
        self.logger.info("Procesando archivo de profesores")
        
        profesores_path = os.path.join(excel_dir, "profesores.xlsx")
        
        if not os.path.exists(profesores_path):
            return ProcessResult(
                success=False,
                message=f"Archivo de profesores no encontrado: {profesores_path}"
            )
        
        try:
            # Leer Excel con pandas
            df = pd.read_excel(profesores_path)
            
            self.logger.info(f"Columnas encontradas: {list(df.columns)}")
            self.logger.info(f"Total de filas: {len(df)}")
            
            teachers_data = []
            created_count = 0
            existing_count = 0
            warnings = []
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Extraer datos (ajustar según columnas reales)
                    # Buscar columna de nombres (puede ser "Docentes", "Nombre", etc.)
                    teacher_name = ""
                    teacher_email = ""
                    
                    # Buscar nombre del profesor
                    for col in df.columns:
                        if any(keyword in col.lower() for keyword in ['docente', 'nombre', 'profesor']):
                            teacher_name = str(row[col]) if not pd.isna(row[col]) else ""
                            break
                    
                    # Buscar email del profesor
                    for col in df.columns:
                        if any(keyword in col.lower() for keyword in ['correo', 'email', 'mail']):
                            teacher_email = str(row[col]) if not pd.isna(row[col]) else ""
                            break
                    
                    # Si no encontramos por nombre de columna, usar posición
                    if not teacher_name and len(df.columns) > 0:
                        # Buscar en las primeras columnas
                        for i in range(min(len(df.columns), 5)):
                            val = str(row.iloc[i]) if not pd.isna(row.iloc[i]) else ""
                            if val and '@' not in val and len(val) > 5:
                                teacher_name = val
                                break
                    
                    if not teacher_email and len(df.columns) > 1:
                        # Buscar email en las columnas
                        for i in range(len(df.columns)):
                            val = str(row.iloc[i]) if not pd.isna(row.iloc[i]) else ""
                            if '@' in val:
                                teacher_email = val
                                break
                    
                    if not teacher_name or not teacher_email:
                        warnings.append(f"Fila {index + 1}: Datos incompletos (nombre: {teacher_name}, email: {teacher_email})")
                        continue
                    
                    # Crear estructura de datos del profesor
                    teacher_data = TeacherData(
                        full_name=teacher_name.strip(),
                        email=teacher_email.strip().lower(),
                        teacher_code=f"PROF{index + 1:03d}"
                    )
                    
                    # Verificar si ya existe
                    if User.objects.filter(institutional_email=teacher_data.email).exists():
                        existing_count += 1
                        self.logger.debug(f"Profesor ya existe: {teacher_data.email}")
                        continue
                    
                    # Crear usuario
                    password = f"{teacher_data.first_name.lower()}123"
                    
                    user = User.objects.create(
                        institutional_email=teacher_data.email,
                        first_name=teacher_data.first_name,
                        last_name=teacher_data.last_name,
                        role='teacher',
                        is_active=True
                    )
                    user.set_password(password)
                    user.save()
                    
                    # Crear profesor
                    teacher = Teacher.objects.create(
                        user=user,
                        teacher_code=teacher_data.teacher_code,
                        department="Ingeniería de Sistemas",
                        specialty="Profesor",
                        hours_per_week=20
                    )
                    
                    teachers_data.append(teacher_data)
                    created_count += 1
                    
                    self.logger.info(f"Profesor creado: {teacher_data.email}")
                    
                except Exception as e:
                    warnings.append(f"Error procesando profesor en fila {index + 1}: {str(e)}")
                    continue
            
            return ProcessResult(
                success=True,
                message=f"Profesores procesados: {created_count} creados, {existing_count} existentes",
                data={
                    'created': created_count,
                    'existing': existing_count,
                    'teachers': teachers_data
                },
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Error procesando profesores: {str(e)}"
            self.logger.error(error_msg)
            return ProcessResult(
                success=False,
                message=error_msg
            )
    
    def _procesar_cursos_estudiantes(self, excel_dir: str) -> ProcessResult:
        """
        Lee archivos de cursos con estudiantes y los procesa
        
        Args:
            excel_dir: Directorio con archivos Excel
            
        Returns:
            ProcessResult con cursos y estudiantes procesados
        """
        self.logger.info("Procesando archivos de cursos con estudiantes")
        
        try:
            # Buscar archivos alumnos_*.xlsx
            course_files = []
            for filename in os.listdir(excel_dir):
                if filename.startswith('alumnos_') and filename.endswith('.xlsx'):
                    course_files.append(os.path.join(excel_dir, filename))
            
            if not course_files:
                return ProcessResult(
                    success=False,
                    message=f"No se encontraron archivos de cursos en {excel_dir}"
                )
            
            self.logger.info(f"Archivos de cursos encontrados: {len(course_files)}")
            
            courses_data = {}
            warnings = []
            
            for course_file in course_files:
                try:
                    # Extraer nombre del curso del nombre del archivo
                    filename = os.path.basename(course_file)
                    course_name = filename.replace('alumnos_', '').replace('.xlsx', '').replace('_', ' ').title()
                    
                    # Leer códigos de estudiantes del archivo
                    student_codes = self._extraer_codigos_estudiantes(course_file)
                    
                    if student_codes:
                        courses_data[course_name] = {
                            'file_path': course_file,
                            'student_codes': student_codes,
                            'student_count': len(student_codes)
                        }
                        
                        self.logger.info(f"Curso procesado: {course_name} - {len(student_codes)} estudiantes")
                    else:
                        warnings.append(f"No se encontraron códigos de estudiantes en {filename}")
                
                except Exception as e:
                    warnings.append(f"Error procesando archivo {course_file}: {str(e)}")
                    continue
            
            return ProcessResult(
                success=True,
                message=f"Cursos procesados: {len(courses_data)}",
                data=courses_data,
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Error procesando cursos: {str(e)}"
            self.logger.error(error_msg)
            return ProcessResult(
                success=False,
                message=error_msg
            )
    
    def _extraer_codigos_estudiantes(self, file_path: str) -> List[str]:
        """
        Extrae códigos de estudiantes de un archivo Excel
        
        Args:
            file_path: Ruta al archivo Excel
            
        Returns:
            Lista de códigos de estudiantes
        """
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active
            
            student_codes = []
            
            # Buscar códigos de estudiante en todo el archivo
            for row_num in range(1, sheet.max_row + 1):
                for col_num in range(1, sheet.max_column + 1):
                    try:
                        cell_value = sheet.cell(row=row_num, column=col_num).value
                        
                        if cell_value:
                            # Convertir a string y limpiar
                            str_value = str(cell_value).strip()
                            
                            # Verificar si es un código de estudiante (8 dígitos)
                            if str_value.replace('.', '').isdigit():
                                # Remover decimales si existen
                                clean_code = str_value.split('.')[0]
                                
                                # Verificar longitud típica de código de estudiante
                                if len(clean_code) == 8:
                                    if clean_code not in student_codes:
                                        student_codes.append(clean_code)
                    
                    except Exception:
                        # Ignorar errores de celdas individuales
                        continue
            
            workbook.close()
            return student_codes
            
        except Exception as e:
            self.logger.error(f"Error extrayendo códigos de {file_path}: {str(e)}")
            return []
    
    def _crear_clases_reales(self, teachers_data: Dict, courses_data: Dict) -> ProcessResult:
        """
        Crea clases reales asignando profesores a cursos y matriculando estudiantes
        
        Args:
            teachers_data: Datos de profesores procesados
            courses_data: Datos de cursos procesados
            
        Returns:
            ProcessResult con clases creadas
        """
        self.logger.info("Creando clases reales")
        
        try:
            # Obtener o crear período académico activo
            academic_period, created = AcademicPeriod.objects.get_or_create(
                name='2024-II',
                defaults={
                    'start_date': date(2024, 8, 1),
                    'end_date': date(2024, 12, 15),
                    'laboratory_enrollment_start': date(2024, 8, 1),
                    'laboratory_enrollment_end': date(2024, 8, 15),
                    'enrollment_change_deadline': date(2024, 8, 30),
                    'is_active': True
                }
            )
            
            if created:
                self.logger.info(f"Período académico creado: {academic_period.name}")
            
            # Obtener profesores disponibles
            teachers = list(Teacher.objects.all())
            if not teachers:
                return ProcessResult(
                    success=False,
                    message="No hay profesores disponibles para asignar"
                )
            
            classes_created = 0
            warnings = []
            
            # Procesar cada curso
            for course_name, course_info in courses_data.items():
                try:
                    # Crear o obtener curso
                    course_code = course_name.replace(' ', '_').upper()[:10]
                    course, created = Course.objects.get_or_create(
                        code=course_code,
                        defaults={
                            'name': course_name,
                            'credits': 3,
                            'theory_hours': 2,
                            'practice_hours': 2,
                            'is_active': True
                        }
                    )
                    
                    # Crear grupo de curso
                    course_group, created = CourseGroup.objects.get_or_create(
                        course=course,
                        academic_period=academic_period,
                        group_code='A',
                        defaults={
                            'capacity': len(course_info['student_codes']) + 5,
                            'enrolled_students': len(course_info['student_codes']),
                            'schedule_info': {
                                'days': ['Lunes', 'Miércoles'],
                                'start_time': '08:00',
                                'end_time': '10:00'
                            },
                            'classroom': f'Aula-{classes_created + 1:02d}'
                        }
                    )
                    
                    # Asignar profesor (rotativo)
                    teacher = teachers[classes_created % len(teachers)]
                    course_group.teacher = teacher
                    course_group.save()
                    
                    # Matricular estudiantes
                    enrolled_count = self._matricular_estudiantes(
                        course_info['student_codes'],
                        course_group,
                        academic_period
                    )
                    
                    classes_created += 1
                    
                    self.logger.info(
                        f"Clase creada: {course_name} - "
                        f"Profesor: {teacher.user.get_full_name()} - "
                        f"Estudiantes: {enrolled_count}"
                    )
                    
                except Exception as e:
                    warnings.append(f"Error creando clase para {course_name}: {str(e)}")
                    continue
            
            return ProcessResult(
                success=True,
                message=f"Clases reales creadas: {classes_created}",
                data={
                    'created': classes_created,
                    'academic_period': academic_period.name
                },
                warnings=warnings
            )
            
        except Exception as e:
            error_msg = f"Error creando clases reales: {str(e)}"
            self.logger.error(error_msg)
            return ProcessResult(
                success=False,
                message=error_msg
            )
    
    def _matricular_estudiantes(self, student_codes: List[str], course_group: CourseGroup, academic_period: AcademicPeriod) -> int:
        """
        Matricula estudiantes en un curso
        
        Args:
            student_codes: Lista de códigos de estudiantes
            course_group: Grupo de curso
            academic_period: Período académico
            
        Returns:
            Número de estudiantes matriculados
        """
        enrolled_count = 0
        
        for student_code in student_codes:
            try:
                # Buscar estudiante por código
                try:
                    student = Student.objects.get(student_code=student_code)
                except Student.DoesNotExist:
                    # Si no existe, crear estudiante básico
                    user = User.objects.create(
                        institutional_email=f"{student_code}@unsa.edu.pe",
                        first_name=f"Estudiante",
                        last_name=f"{student_code}",
                        role='student',
                        is_active=True
                    )
                    user.set_password('estudiante123')
                    user.save()
                    
                    student = Student.objects.create(
                        user=user,
                        student_code=student_code,
                        career="Ingeniería de Sistemas",
                        current_cycle=5,
                        academic_status='active'
                    )
                
                # Crear matrícula
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course_group=course_group,
                    academic_period=academic_period,
                    defaults={
                        'enrollment_date': timezone.now().date(),
                        'enrollment_type': 'regular',
                        'status': 'active'
                    }
                )
                
                if created:
                    enrolled_count += 1
                
            except Exception as e:
                self.logger.warning(f"Error matriculando estudiante {student_code}: {str(e)}")
                continue
        
        return enrolled_count
    
    def _generar_datos_simulados(self) -> ProcessResult:
        """
        Genera datos simulados de asistencia y notas para las clases creadas
        
        Returns:
            ProcessResult con datos simulados generados
        """
        self.logger.info("Generando datos simulados de asistencia y notas")
        
        try:
            # Obtener todas las matrículas activas
            enrollments = Enrollment.objects.filter(status='active')
            
            attendance_created = 0
            grades_created = 0
            
            # Generar datos para cada matrícula
            for enrollment in enrollments:
                try:
                    # Generar registros de asistencia (últimas 4 semanas)
                    for week in range(1, 5):
                        attendance_date = timezone.now().date().replace(day=week * 7)
                        
                        # Simular asistencia (80% presente, 15% ausente, 5% tardanza)
                        import random
                        status_choice = random.choices(
                            ['present', 'absent', 'late'],
                            weights=[80, 15, 5]
                        )[0]
                        
                        AttendanceRecord.objects.get_or_create(
                            student=enrollment.student,
                            course_group=enrollment.course_group,
                            date=attendance_date,
                            defaults={
                                'status': status_choice,
                                'recorded_by': enrollment.course_group.teacher.user if enrollment.course_group.teacher else None,
                                'notes': f'Registro automático semana {week}'
                            }
                        )
                        attendance_created += 1
                    
                    # Generar notas simuladas
                    exam_types = ['parcial_1', 'parcial_2', 'tarea']
                    
                    for exam_type in exam_types:
                        # Generar nota aleatoria entre 10 y 20
                        import random
                        grade_value = round(random.uniform(10.0, 20.0), 2)
                        
                        Grade.objects.get_or_create(
                            student=enrollment.student,
                            course=enrollment.course_group.course,
                            exam_type=exam_type,
                            grade_component='Nota 1',
                            defaults={
                                'grade': grade_value
                            }
                        )
                        grades_created += 1
                
                except Exception as e:
                    self.logger.warning(f"Error generando datos simulados para matrícula {enrollment.id}: {str(e)}")
                    continue
            
            return ProcessResult(
                success=True,
                message=f"Datos simulados generados: {attendance_created} asistencias, {grades_created} notas",
                data={
                    'attendance_records': attendance_created,
                    'grades': grades_created
                }
            )
            
        except Exception as e:
            error_msg = f"Error generando datos simulados: {str(e)}"
            self.logger.error(error_msg)
            return ProcessResult(
                success=False,
                message=error_msg
            )