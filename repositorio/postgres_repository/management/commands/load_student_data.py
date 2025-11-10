"""
Comando para cargar datos de estudiantes desde archivo Excel
"""
import pandas as pd
import re
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.db import transaction
from repositorio.postgres_repository.models import User, Student, AcademicPeriod, Course, CourseGroup, Enrollment


class Command(BaseCommand):
    help = 'Carga datos de estudiantes desde archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='alumnos_450_1703240_B_A (1).xlsx',
            help='Ruta al archivo Excel con los datos de estudiantes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin hacer cambios en la base de datos'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Modo DRY RUN - No se harán cambios en la base de datos')
            )
        
        try:
            # Leer el archivo Excel
            self.stdout.write(f'Leyendo archivo: {file_path}')
            df = pd.read_excel(file_path)
            
            # Mostrar información del archivo
            self.stdout.write(f'Archivo cargado exitosamente')
            self.stdout.write(f'Número de filas: {len(df)}')
            self.stdout.write(f'Columnas: {list(df.columns)}')
            
            # Procesar los datos
            self.process_student_data(df, dry_run)
            
        except FileNotFoundError:
            raise CommandError(f'Archivo no encontrado: {file_path}')
        except Exception as e:
            raise CommandError(f'Error al procesar el archivo: {str(e)}')

    def process_student_data(self, df, dry_run=False):
        """Procesa los datos de estudiantes del DataFrame"""
        
        created_users = 0
        created_students = 0
        errors = 0
        
        # Buscar la fila donde empiezan los datos (contiene "Nro", "CUI", etc.)
        start_row = None
        for i, row in df.iterrows():
            if str(row.iloc[0]).strip() == "Nro" and str(row.iloc[1]).strip() == "CUI":
                start_row = i + 1  # Los datos empiezan en la siguiente fila
                break
        
        if start_row is None:
            self.stdout.write(self.style.ERROR('No se encontró la fila de encabezados'))
            return
        
        self.stdout.write(f'Datos de estudiantes empiezan en la fila {start_row + 1}')
        
        # Crear período académico por defecto si no existe
        if not dry_run:
            try:
                from repositorio.postgres_repository.models import AcademicPeriod
                period, created = AcademicPeriod.objects.get_or_create(
                    name='2024-I',
                    defaults={
                        'start_date': '2024-03-01',
                        'end_date': '2024-07-31',
                        'laboratory_enrollment_start': '2024-03-01',
                        'laboratory_enrollment_end': '2024-03-15',
                        'enrollment_change_deadline': '2024-03-12',
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Período académico creado: {period.name}')
            except:
                # Si no existe el modelo AcademicPeriod, continuar sin él
                pass
        
        # Procesar cada fila del DataFrame desde start_row
        for index in range(start_row, len(df)):
            try:
                row = df.iloc[index]
                
                # Extraer datos de la fila usando posiciones
                nro = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                cui = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
                apellidos_nombres = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
                
                # Verificar que tenemos datos válidos
                if not cui or not apellidos_nombres or cui == 'nan' or apellidos_nombres == 'nan':
                    continue
                
                # Separar apellidos y nombres
                # Formato: "APELLIDO1/APELLIDO2, NOMBRE1 NOMBRE2"
                if ',' in apellidos_nombres:
                    apellidos_part, nombres_part = apellidos_nombres.split(',', 1)
                    apellidos = apellidos_part.replace('/', ' ').strip()
                    nombres = nombres_part.strip()
                else:
                    # Si no hay coma, asumir que todo son apellidos
                    apellidos = apellidos_nombres.replace('/', ' ').strip()
                    nombres = 'Estudiante'
                
                if not cui or not apellidos or not nombres:
                    self.stdout.write(
                        self.style.WARNING(f'Fila {index + 1}: Datos incompletos - CUI: {cui}, Apellidos: {apellidos}, Nombres: {nombres}')
                    )
                    errors += 1
                    continue
                
                # Generar email institucional
                institutional_email = self.generate_institutional_email(nombres, apellidos)
                
                if not dry_run:
                    with transaction.atomic():
                        # Crear usuario
                        user, user_created = User.objects.get_or_create(
                            institutional_email=institutional_email,
                            defaults={
                                'first_name': nombres,
                                'last_name': apellidos,
                                'role': 'student',
                                'password': make_password(cui),  # CUI como contraseña
                                'is_active': True,
                                'dni': cui if len(cui) == 8 else None
                            }
                        )
                        
                        if user_created:
                            created_users += 1
                            self.stdout.write(f'Usuario creado: {institutional_email}')
                        
                        # Crear estudiante
                        student, student_created = Student.objects.get_or_create(
                            user=user,
                            defaults={
                                'student_code': cui,
                                'academic_status': 'active'
                            }
                        )
                        
                        if student_created:
                            created_students += 1
                            self.stdout.write(f'Estudiante creado: {cui} - {nombres} {apellidos}')
                else:
                    # Modo dry-run: solo mostrar lo que se haría
                    self.stdout.write(f'[DRY RUN] Crearía usuario: {institutional_email} (CUI: {cui})')
                    created_users += 1
                    created_students += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error en fila {index + 1}: {str(e)}')
                )
                errors += 1
                continue
        
        # Crear usuario administrador por defecto
        if not dry_run:
            admin_user, admin_created = User.objects.get_or_create(
                institutional_email='admin@unsa.edu.pe',
                defaults={
                    'first_name': 'Administrador',
                    'last_name': 'Sistema',
                    'role': 'admin',
                    'password': make_password('admin123'),
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if admin_created:
                self.stdout.write(
                    self.style.SUCCESS('Usuario administrador creado: admin@unsa.edu.pe (contraseña: admin123)')
                )
        
        # Mostrar resumen
        self.stdout.write(
            self.style.SUCCESS(
                f'\nResumen de la carga:\n'
                f'- Usuarios creados: {created_users}\n'
                f'- Estudiantes creados: {created_students}\n'
                f'- Errores: {errors}'
            )
        )

    def generate_institutional_email(self, nombres, apellidos):
        """
        Genera el email institucional basado en el formato:
        inicial_nombre + apellido + @unsa.edu.pe
        """
        # Limpiar y normalizar nombres
        nombres = re.sub(r'[^a-zA-Z\s]', '', nombres).strip().lower()
        apellidos = re.sub(r'[^a-zA-Z\s]', '', apellidos).strip().lower()
        
        # Tomar la primera letra del primer nombre
        primer_nombre = nombres.split()[0] if nombres.split() else 'x'
        inicial_nombre = primer_nombre[0] if primer_nombre else 'x'
        
        # Tomar el primer apellido
        primer_apellido = apellidos.split()[0] if apellidos.split() else 'apellido'
        
        # Generar email
        email = f"{inicial_nombre}{primer_apellido}@unsa.edu.pe"
        
        return email

    def create_sample_courses(self):
        """Crea algunos cursos de ejemplo"""
        sample_courses = [
            {'code': 'CS101', 'name': 'Introducción a la Programación', 'credits': 4, 'theory_hours': 3, 'practice_hours': 2},
            {'code': 'MAT101', 'name': 'Matemática Básica', 'credits': 4, 'theory_hours': 4, 'practice_hours': 0},
            {'code': 'FIS101', 'name': 'Física I', 'credits': 4, 'theory_hours': 3, 'practice_hours': 2},
            {'code': 'QUI101', 'name': 'Química General', 'credits': 4, 'theory_hours': 3, 'practice_hours': 2},
        ]
        
        for course_data in sample_courses:
            course, created = Course.objects.get_or_create(
                code=course_data['code'],
                defaults=course_data
            )
            if created:
                self.stdout.write(f'Curso creado: {course.code} - {course.name}')