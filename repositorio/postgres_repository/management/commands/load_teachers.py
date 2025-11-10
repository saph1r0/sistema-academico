"""
Comando Django para cargar profesores del Excel
"""
import os
import pandas as pd
from django.core.management.base import BaseCommand
from repositorio.postgres_repository.models import User, Teacher, CourseGroup

class Command(BaseCommand):
    help = 'Carga profesores del archivo Excel'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("CARGANDO PROFESORES DEL EXCEL")
        self.stdout.write("=" * 80)
        
        try:
            # Leer archivo de profesores
            excel_path = 'EXELS/profesores.xlsx'
            if not os.path.exists(excel_path):
                self.stdout.write(f"ERROR: No se encontró el archivo {excel_path}")
                return
            
            self.stdout.write(f"Leyendo archivo: {excel_path}")
            df = pd.read_excel(excel_path)
            
            self.stdout.write(f"Columnas encontradas: {list(df.columns)}")
            self.stdout.write(f"Total de filas: {len(df)}")
            
            # Procesar cada profesor
            profesores_creados = 0
            profesores_existentes = 0
            
            for index, row in df.iterrows():
                try:
                    # Extraer datos del profesor
                    nombre_completo = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
                    email = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else ""
                    
                    if not email or not nombre_completo:
                        self.stdout.write(f"Fila {index + 1}: Datos incompletos, saltando...")
                        continue
                    
                    # Separar nombre y apellidos
                    partes_nombre = nombre_completo.strip().split()
                    if len(partes_nombre) >= 2:
                        primer_nombre = partes_nombre[0]
                        apellidos = " ".join(partes_nombre[1:])
                    else:
                        primer_nombre = nombre_completo
                        apellidos = ""
                    
                    # Crear contraseña: primer nombre + 123
                    password = f"{primer_nombre.lower()}123"
                    
                    self.stdout.write(f"\nProcesando: {nombre_completo} ({email})")
                    
                    # Verificar si el usuario ya existe
                    if User.objects.filter(institutional_email=email).exists():
                        self.stdout.write(f"  Usuario ya existe: {email}")
                        profesores_existentes += 1
                        continue
                    
                    # Crear usuario
                    user = User.objects.create(
                        institutional_email=email,
                        first_name=primer_nombre,
                        last_name=apellidos,
                        role='teacher',
                        is_active=True
                    )
                    user.set_password(password)
                    user.save()
                    
                    # Crear profesor
                    Teacher.objects.create(
                        user=user,
                        teacher_code=f"PROF{index + 1:03d}",
                        department="Ingeniería de Sistemas",
                        specialty="Profesor",
                        hours_per_week=20
                    )
                    
                    self.stdout.write(f"  ✓ Profesor creado: {email} (contraseña: {password})")
                    profesores_creados += 1
                    
                except Exception as e:
                    self.stdout.write(f"  ERROR procesando fila {index + 1}: {str(e)}")
                    continue
            
            self.stdout.write(f"\n" + "=" * 80)
            self.stdout.write("RESUMEN:")
            self.stdout.write(f"Profesores creados: {profesores_creados}")
            self.stdout.write(f"Profesores existentes: {profesores_existentes}")
            self.stdout.write("=" * 80)
            
            # Asignar profesores a cursos
            self.assign_teachers_to_courses()
            
        except Exception as e:
            self.stdout.write(f"ERROR: {str(e)}")

    def assign_teachers_to_courses(self):
        """Asigna profesores a cursos automáticamente"""
        self.stdout.write("\nASIGNANDO PROFESORES A CURSOS...")
        
        try:
            # Obtener todos los profesores y cursos
            profesores = list(Teacher.objects.all())
            course_groups = CourseGroup.objects.all()
            
            if not profesores:
                self.stdout.write("No hay profesores disponibles para asignar")
                return
            
            self.stdout.write(f"Profesores disponibles: {len(profesores)}")
            self.stdout.write(f"Grupos de cursos: {len(course_groups)}")
            
            # Asignar profesores de forma rotativa
            asignaciones = 0
            for i, course_group in enumerate(course_groups):
                # Seleccionar profesor de forma rotativa
                profesor = profesores[i % len(profesores)]
                
                # Asignar profesor al grupo de curso
                course_group.teacher = profesor
                course_group.save()
                
                self.stdout.write(f"  ✓ {course_group.course.name} -> {profesor.user.first_name} {profesor.user.last_name}")
                asignaciones += 1
            
            self.stdout.write(f"\nAsignaciones completadas: {asignaciones}")
            
        except Exception as e:
            self.stdout.write(f"ERROR asignando profesores: {str(e)}")