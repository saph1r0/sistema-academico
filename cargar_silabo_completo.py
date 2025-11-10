#!/usr/bin/env python
"""
Script para cargar datos completos del Silabo-Mac.xlsx
Extrae información del curso, crea profesor con formato 'edu' y carga contenido del sílabo
"""
import os
import sys
import pandas as pd
import re
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.hashers import make_password
from django.db import transaction
from repositorio.postgres_repository.models import User, Student, Teacher, Course, CourseContent


class SilaboDataExtractor:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.df = None
        self.course_info = {}
        self.teachers_info = []
        self.content_data = []
    
    def load_excel(self):
        """Carga el archivo Excel"""
        try:
            self.df = pd.read_excel(self.excel_file_path)
            print(f'✅ Archivo Excel cargado: {len(self.df)} filas')
            return True
        except Exception as e:
            print(f'❌ Error cargando Excel: {e}')
            return False
    
    def extract_course_info(self):
        """Extrae información básica del curso"""
        print('\n📚 Extrayendo información del curso...')
        
        for i, row in self.df.iterrows():
            prop = str(row['Propiedad General']).strip()
            valor = row['Valor']
            
            if 'Periodo académico' in prop:
                self.course_info['periodo'] = str(valor).strip()
            elif 'Escuela Profesional' in prop:
                self.course_info['escuela'] = str(valor).strip()
            elif 'Código de la asignatura' in prop:
                self.course_info['codigo'] = str(valor).strip()
            elif 'Nombre de la asignatura' in prop:
                self.course_info['nombre'] = str(valor).strip()
            elif 'Semestre' in prop:
                self.course_info['semestre'] = str(valor).strip()
            elif 'Duración' in prop:
                self.course_info['duracion'] = str(valor).strip()
            elif 'Horas Teóricas' in prop:
                self.course_info['horas_teoricas'] = int(valor) if pd.notna(valor) else 0
            elif 'Horas Prácticas' in prop:
                self.course_info['horas_practicas'] = int(valor) if pd.notna(valor) else 0
            elif 'Horas Laboratorio' in prop:
                self.course_info['horas_laboratorio'] = int(valor) if pd.notna(valor) else 0
            elif 'Número de créditos' in prop:
                self.course_info['creditos'] = int(valor) if pd.notna(valor) else 0
        
        print(f'📋 Curso: {self.course_info.get("nombre", "N/A")}')
        print(f'📋 Código: {self.course_info.get("codigo", "N/A")}')
        print(f'📋 Escuela: {self.course_info.get("escuela", "N/A")}')
        print(f'📋 Período: {self.course_info.get("periodo", "N/A")}')
        
        return self.course_info
    
    def extract_teachers_info(self):
        """Extrae información de los profesores"""
        print('\n👨‍🏫 Extrayendo información de profesores...')
        
        for i, row in self.df.iterrows():
            prop = str(row['Propiedad General']).strip()
            
            # Buscar nombres de profesores (después de la fila "Docente")
            if prop and prop not in ['Docente', 'nan'] and pd.notna(row['Unnamed: 2']) and str(row['Unnamed: 2']).strip() == 'MATEMATICAS':
                teacher_name = prop.strip()
                department = str(row['Unnamed: 2']).strip()
                hours = row['Unnamed: 3'] if pd.notna(row['Unnamed: 3']) else 0
                schedule = str(row['Unnamed: 4']).strip() if pd.notna(row['Unnamed: 4']) else ''
                
                # Parsear nombre completo
                name_parts = teacher_name.split(',')
                if len(name_parts) >= 2:
                    apellidos = name_parts[0].strip()
                    nombres = name_parts[1].strip()
                    
                    teacher_info = {
                        'nombres': nombres,
                        'apellidos': apellidos,
                        'nombre_completo': teacher_name,
                        'departamento': department,
                        'horas': hours,
                        'horario': schedule
                    }
                    
                    self.teachers_info.append(teacher_info)
                    print(f'👨‍🏫 Profesor encontrado: {nombres} {apellidos}')
        
        return self.teachers_info
    
    def extract_course_content(self):
        """Extrae el contenido del curso (unidades, capítulos, temas)"""
        print('\n📖 Extrayendo contenido del curso...')
        
        current_unit = None
        current_chapter = None
        week_counter = 1
        
        for i, row in self.df.iterrows():
            prop = str(row['Propiedad General']).strip()
            valor = str(row['Valor']).strip() if pd.notna(row['Valor']) else ''
            tema_num = str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else ''
            descripcion = str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else ''
            
            # Detectar unidades
            if prop in ['PRIMERA UNIDAD', 'SEGUNDA UNIDAD', 'TERCERA UNIDAD']:
                current_unit = prop
                current_chapter = valor if valor and valor != 'nan' else ''
                print(f'📚 {current_unit}: {current_chapter}')
                continue
            
            # Detectar temas
            if current_unit and tema_num.startswith('Tema ') and descripcion and descripcion != 'nan':
                topic_number = tema_num.replace('Tema ', '').strip()
                
                # Determinar tipo de contenido
                content_type = 'topic'
                if 'examen' in descripcion.lower():
                    content_type = 'exam'
                elif 'tarea' in descripcion.lower() or 'proyecto' in descripcion.lower():
                    content_type = 'assignment'
                
                content_item = {
                    'unit_name': current_unit,
                    'chapter_name': current_chapter,
                    'topic_number': topic_number,
                    'title': descripcion,
                    'content_type': content_type,
                    'week_number': week_counter,
                    'order': int(topic_number) if topic_number.isdigit() else week_counter
                }
                
                self.content_data.append(content_item)
                print(f'  📝 Tema {topic_number}: {descripcion}')
                
                # Incrementar semana cada 2-3 temas (aproximadamente)
                if len(self.content_data) % 2 == 0:
                    week_counter += 1
        
        print(f'📖 Total de contenidos extraídos: {len(self.content_data)}')
        return self.content_data
    
    def generate_teacher_email(self, nombres, apellidos):
        """Genera email con formato: inicial_nombre + apellido + edu + @unsa.edu.pe"""
        nombres_clean = re.sub(r'[^a-zA-Z\s]', '', nombres).strip().lower()
        apellidos_clean = re.sub(r'[^a-zA-Z\s]', '', apellidos).strip().lower()
        
        # Tomar la primera letra del primer nombre
        primer_nombre = nombres_clean.split()[0] if nombres_clean.split() else 'x'
        inicial_nombre = primer_nombre[0] if primer_nombre else 'x'
        
        # Tomar el primer apellido
        primer_apellido = apellidos_clean.split()[0] if apellidos_clean.split() else 'apellido'
        
        # Generar email con sufijo 'edu'
        email = f"{inicial_nombre}{primer_apellido}edu@unsa.edu.pe"
        
        return email
    
    def generate_teacher_password(self, nombres):
        """Genera contraseña: primer_nombre + 123"""
        nombres_clean = re.sub(r'[^a-zA-Z\s]', '', nombres).strip().lower()
        primer_nombre = nombres_clean.split()[0] if nombres_clean.split() else 'profesor'
        return f"{primer_nombre}123"


def main():
    try:
        print('🚀 Iniciando carga completa del sílabo...')
        
        # Verificar archivo
        if not os.path.exists('Silabo-Mac.xlsx'):
            print('❌ Archivo Silabo-Mac.xlsx no encontrado')
            return
        
        # Crear extractor y cargar datos
        extractor = SilaboDataExtractor('Silabo-Mac.xlsx')
        
        if not extractor.load_excel():
            return
        
        # Extraer información
        course_info = extractor.extract_course_info()
        teachers_info = extractor.extract_teachers_info()
        content_data = extractor.extract_course_content()
        
        if not teachers_info:
            print('⚠️  No se encontraron profesores, creando profesor de ejemplo...')
            teachers_info = [{
                'nombres': 'RICARDO JAVIER',
                'apellidos': 'HANCCO ANCORI',
                'nombre_completo': 'HANCCO ANCORI, RICARDO JAVIER',
                'departamento': 'MATEMATICAS',
                'horas': 4,
                'horario': 'Lun: 07:00-08:40 Mar: 09:40-11:30'
            }]
        
        print(f'\n📊 RESUMEN DE EXTRACCIÓN:')
        print(f'- Curso: {course_info.get("nombre", "N/A")}')
        print(f'- Profesores encontrados: {len(teachers_info)}')
        print(f'- Contenidos extraídos: {len(content_data)}')
        
        # Crear usuarios y curso en la base de datos
        created_users = 0
        created_teachers = 0
        created_courses = 0
        created_contents = 0
        
        with transaction.atomic():
            # Crear profesores
            for teacher_info in teachers_info:
                teacher_email = extractor.generate_teacher_email(
                    teacher_info['nombres'], 
                    teacher_info['apellidos']
                )
                teacher_password = extractor.generate_teacher_password(teacher_info['nombres'])
                
                print(f'\n👨‍🏫 Creando profesor:')
                print(f'- Nombre: {teacher_info["nombres"]} {teacher_info["apellidos"]}')
                print(f'- Email: {teacher_email}')
                print(f'- Contraseña: {teacher_password}')
                
                # Crear usuario profesor
                teacher_user, teacher_created = User.objects.get_or_create(
                    institutional_email=teacher_email,
                    defaults={
                        'first_name': teacher_info['nombres'],
                        'last_name': teacher_info['apellidos'],
                        'role': 'teacher',
                        'password': make_password(teacher_password),
                        'is_active': True
                    }
                )
                
                if teacher_created:
                    created_users += 1
                    print(f'✅ Usuario profesor creado: {teacher_email}')
                
                # Crear perfil de profesor
                teacher_code = f"DOC{len(Teacher.objects.all()) + 1:03d}"
                teacher_profile, teacher_profile_created = Teacher.objects.get_or_create(
                    user=teacher_user,
                    defaults={
                        'teacher_code': teacher_code,
                        'department': teacher_info['departamento'],
                        'specialty': course_info.get('nombre', ''),
                        'hours_per_week': teacher_info.get('horas', 4)
                    }
                )
                
                if teacher_profile_created:
                    created_teachers += 1
                    print(f'✅ Perfil de profesor creado: {teacher_code}')
                
                # Crear curso
                course_code = course_info.get('codigo', 'MATH001')
                course, course_created = Course.objects.get_or_create(
                    code=course_code,
                    defaults={
                        'name': course_info.get('nombre', 'MATEMATICA APLICADA A LA COMPUTACION'),
                        'credits': course_info.get('creditos', 4),
                        'theory_hours': course_info.get('horas_teoricas', 2),
                        'practice_hours': course_info.get('horas_practicas', 2),
                        'teacher': teacher_profile,
                        'department': course_info.get('escuela', 'CIENCIA DE LA COMPUTACIÓN'),
                        'cycle': 'VI',
                        'group': 'A',
                        'academic_year': '2025',
                        'semester': 'B',
                        'weekly_hours': teacher_info.get('horas', 4),
                        'total_weeks': 17,
                        'duration': course_info.get('duracion', '17 semanas'),
                        'is_active': True
                    }
                )
                
                if course_created:
                    created_courses += 1
                    print(f'✅ Curso creado: {course.name}')
                
                # Crear contenido del curso
                for content_item in content_data:
                    content, content_created = CourseContent.objects.get_or_create(
                        course=course,
                        topic_number=content_item['topic_number'],
                        defaults={
                            'unit_name': content_item['unit_name'],
                            'chapter_name': content_item['chapter_name'],
                            'title': content_item['title'],
                            'content_type': content_item['content_type'],
                            'week_number': content_item['week_number'],
                            'order': content_item['order'],
                            'is_completed': False
                        }
                    )
                    
                    if content_created:
                        created_contents += 1
                
                print(f'✅ Contenidos del curso creados: {created_contents}')
                
                # Solo crear un profesor (el primero)
                break
        
        # Crear secretaria super usuario
        print(f'\n👩‍💼 Creando secretaria super usuario...')
        
        with transaction.atomic():
            secretary_user, secretary_created = User.objects.get_or_create(
                institutional_email='secretaria@unsa.edu.pe',
                defaults={
                    'first_name': 'María Elena',
                    'last_name': 'García Mendoza',
                    'role': 'secretary',
                    'password': make_password('secretaria123'),
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            if secretary_created:
                created_users += 1
                print(f'✅ Secretaria super usuario creada: secretaria@unsa.edu.pe')
        
        # Mostrar resumen final
        print(f'''
🎉 CARGA COMPLETA DEL SÍLABO EXITOSA:

📚 CURSO CREADO:
- Nombre: {course_info.get("nombre", "N/A")}
- Código: {course_info.get("codigo", "N/A")}
- Créditos: {course_info.get("creditos", "N/A")}
- Duración: {course_info.get("duracion", "N/A")}

👨‍🏫 PROFESOR CREADO:
- Email: {extractor.generate_teacher_email(teachers_info[0]["nombres"], teachers_info[0]["apellidos"])}
- Contraseña: {extractor.generate_teacher_password(teachers_info[0]["nombres"])}
- Departamento: {teachers_info[0]["departamento"]}

👩‍💼 SECRETARIA CREADA:
- Email: secretaria@unsa.edu.pe
- Contraseña: secretaria123 (SUPER USUARIO)

📊 ESTADÍSTICAS:
- Usuarios creados: {created_users}
- Profesores creados: {created_teachers}
- Cursos creados: {created_courses}
- Contenidos creados: {created_contents}

🚀 Para probar el sistema:
1. poetry run python manage.py runserver
2. Accede como profesor para gestionar el curso
3. Accede como secretaria para supervisión global
        ''')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()