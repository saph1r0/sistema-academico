#!/usr/bin/env python
"""
Script para cargar profesores desde Excel y asignar cursos automáticamente
"""
import os
import sys
import django
import pandas as pd
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import Teacher, Course, Student, Enrollment, User, CourseGroup, AcademicPeriod

def leer_excel_profesores():
    """Lee el archivo Excel de profesores y muestra la estructura"""
    try:
        # Leer el archivo de profesores
        df_profesores = pd.read_excel('EXELS/profesores.xlsx')
        
        print("=== ESTRUCTURA DEL ARCHIVO PROFESORES ===")
        print(f"Columnas: {list(df_profesores.columns)}")
        print(f"Número de filas: {len(df_profesores)}")
        print("\nPrimeras 5 filas:")
        print(df_profesores.head())
        print(f"\nTipos de datos:")
        print(df_profesores.dtypes)
        
        return df_profesores
        
    except Exception as e:
        print(f"Error leyendo archivo de profesores: {e}")
        return None

def leer_excel_estudiantes():
    """Lee el archivo Excel de estudiantes ADA"""
    try:
        # Leer el archivo de estudiantes ADA
        df_estudiantes = pd.read_excel('EXELS/alumnos_ada(1).xlsx')
        
        print("\n=== ESTRUCTURA DEL ARCHIVO ESTUDIANTES ADA ===")
        print(f"Columnas: {list(df_estudiantes.columns)}")
        print(f"Número de filas: {len(df_estudiantes)}")
        print("\nPrimeras 5 filas:")
        print(df_estudiantes.head())
        
        return df_estudiantes
        
    except Exception as e:
        print(f"Error leyendo archivo de estudiantes: {e}")
        return None

def extraer_nombre_profesor(nombre_completo):
    """Extrae nombre y apellido del formato 'APELLIDO, NOMBRE'"""
    try:
        if pd.isna(nombre_completo) or not nombre_completo:
            return None, None
            
        # Limpiar el nombre
        nombre_limpio = str(nombre_completo).strip()
        
        if ',' in nombre_limpio:
            partes = nombre_limpio.split(',')
            apellido = partes[0].strip()
            nombre = partes[1].strip() if len(partes) > 1 else ""
        else:
            # Si no hay coma, asumir que todo es apellido
            apellido = nombre_limpio
            nombre = ""
            
        return nombre.title(), apellido.title()
        
    except Exception as e:
        print(f"Error procesando nombre '{nombre_completo}': {e}")
        return None, None

def crear_o_obtener_profesor(nombre, apellido, email):
    """Crea o obtiene un profesor de la base de datos"""
    try:
        # Buscar si ya existe un usuario con ese email
        user = User.objects.filter(institutional_email=email).first()
        
        if user and hasattr(user, 'teacher'):
            print(f"  - Profesor ya existe: {user.get_full_name()}")
            return user.teacher
            
        # Crear nuevo usuario si no existe
        if not user:
            user = User.objects.create(
                first_name=nombre,
                last_name=apellido,
                institutional_email=email,
                role='teacher',
                is_active=True
            )
            user.set_password('temporal123')  # Contraseña temporal
            user.save()
            
        # Crear nuevo profesor
        teacher = Teacher.objects.create(
            user=user,
            teacher_code=f"DOC{Teacher.objects.count() + 1:04d}",
            department="Ingeniería de Sistemas",
            specialty="Computación"
        )
        
        print(f"  + Profesor creado: {user.get_full_name()}")
        return teacher
        
    except Exception as e:
        print(f"Error creando profesor {nombre} {apellido}: {e}")
        return None

def crear_o_obtener_curso(codigo, nombre, ciclo, grupo):
    """Crea o obtiene un curso de la base de datos"""
    try:
        # Buscar si ya existe
        course = Course.objects.filter(code=str(codigo)).first()
        
        if course:
            print(f"  - Curso ya existe: {course.name}")
            return course
            
        # Crear nuevo curso
        course = Course.objects.create(
            code=str(codigo),
            name=nombre,
            credits=3,  # Valor por defecto
            theory_hours=2,  # Valor por defecto
            practice_hours=2  # Valor por defecto
        )
        
        print(f"  + Curso creado: {course.name}")
        return course
        
    except Exception as e:
        print(f"Error creando curso {codigo}: {e}")
        return None

def crear_estudiante_desde_ada(row):
    """Crea un estudiante desde los datos del Excel ADA"""
    try:
        # Extraer datos del estudiante (ajustar según las columnas reales)
        codigo = row.get('Codigo', '') or row.get('CODIGO', '') or row.get('codigo', '')
        nombre = row.get('Nombre', '') or row.get('NOMBRE', '') or row.get('nombre', '')
        apellido = row.get('Apellido', '') or row.get('APELLIDO', '') or row.get('apellido', '')
        
        if not codigo:
            print(f"  - Estudiante sin código, saltando: {row}")
            return None
            
        # Buscar si ya existe
        student = Student.objects.filter(student_code=str(codigo)).first()
        if student:
            return student
            
        # Crear usuario primero
        email = f"{codigo}@unsa.edu.pe"
        user = User.objects.filter(institutional_email=email).first()
        
        if not user:
            user = User.objects.create(
                first_name=str(nombre).title() if nombre else "Estudiante",
                last_name=str(apellido).title() if apellido else f"ADA{codigo}",
                institutional_email=email,
                role='student',
                is_active=True
            )
            user.set_password('temporal123')  # Contraseña temporal
            user.save()
            
        # Crear nuevo estudiante
        student = Student.objects.create(
            user=user,
            student_code=str(codigo),
            career="Ingeniería de Sistemas",
            current_cycle=1,
            academic_status='active'
        )
        
        print(f"  + Estudiante creado: {user.get_full_name()}")
        return student
        
    except Exception as e:
        print(f"Error creando estudiante: {e}")
        return None

def limpiar_periodos_duplicados():
    """Limpia períodos académicos duplicados"""
    try:
        # Desactivar todos los períodos excepto el primero
        periodos = AcademicPeriod.objects.filter(name='2024-I')
        if periodos.count() > 1:
            print(f"Encontrados {periodos.count()} períodos duplicados. Limpiando...")
            # Mantener solo el primero activo
            primer_periodo = periodos.first()
            primer_periodo.is_active = True
            primer_periodo.save()
            
            # Desactivar los demás
            for periodo in periodos[1:]:
                periodo.is_active = False
                periodo.save()
                
            print("Períodos duplicados limpiados.")
    except Exception as e:
        print(f"Error limpiando períodos: {e}")

def procesar_profesores_y_cursos():
    """Procesa el archivo de profesores y crea cursos con asignaciones"""
    
    # Limpiar períodos duplicados primero
    limpiar_periodos_duplicados()
    
    # Leer archivos
    df_profesores = leer_excel_profesores()
    df_estudiantes = leer_excel_estudiantes()
    
    if df_profesores is None or df_estudiantes is None:
        print("Error: No se pudieron leer los archivos Excel")
        return
    
    print("\n=== PROCESANDO PROFESORES Y CURSOS ===")
    
    # Crear estudiantes ADA primero
    print("\n1. Creando estudiantes ADA...")
    estudiantes_ada = []
    for idx, row in df_estudiantes.iterrows():
        estudiante = crear_estudiante_desde_ada(row)
        if estudiante:
            estudiantes_ada.append(estudiante)
    
    print(f"Estudiantes ADA creados/encontrados: {len(estudiantes_ada)}")
    
    # Procesar cada fila del archivo de profesores
    print("\n2. Procesando profesores y cursos...")
    
    for idx, row in df_profesores.iterrows():
        try:
            print(f"\nProcesando fila {idx + 1}:")
            
            # Extraer datos
            codigo_curso = row.get('Codigo', '')
            nombre_asignatura = row.get('Asignatura', '')
            ciclo = row.get('Ciclo', '')
            grupo = row.get('Grupo', '')
            nombre_docente = row.get('Docentes', '')
            email_docente = row.get('Correo', '')
            
            print(f"  Curso: {codigo_curso} - {nombre_asignatura}")
            print(f"  Docente: {nombre_docente}")
            print(f"  Email: {email_docente}")
            
            # Crear curso
            curso = crear_o_obtener_curso(codigo_curso, nombre_asignatura, ciclo, grupo)
            if not curso:
                continue
                
            # Procesar profesor
            nombre, apellido = extraer_nombre_profesor(nombre_docente)
            if not nombre and not apellido:
                print(f"  ! No se pudo extraer nombre del docente: {nombre_docente}")
                continue
                
            profesor = crear_o_obtener_profesor(nombre, apellido, email_docente)
            if not profesor:
                continue
                
            # Obtener período académico activo o crear uno
            periodo = AcademicPeriod.objects.filter(is_active=True).first()
            if not periodo:
                periodo, created = AcademicPeriod.objects.get_or_create(
                    name='2024-I',
                    defaults={
                        'start_date': '2024-03-01',
                        'end_date': '2024-07-31',
                        'laboratory_enrollment_start': '2024-03-01',
                        'laboratory_enrollment_end': '2024-03-15',
                        'enrollment_change_deadline': '2024-03-20',
                        'is_active': True
                    }
                )
            
            # Crear o obtener grupo de curso
            course_group, created = CourseGroup.objects.get_or_create(
                course=curso,
                academic_period=periodo,
                group_code=str(grupo) if grupo else 'A',
                defaults={
                    'teacher': profesor,
                    'capacity': 30,
                    'enrolled_students': 0
                }
            )
            
            if not created and course_group.teacher != profesor:
                course_group.teacher = profesor
                course_group.save()
                
            print(f"  ✓ Profesor {profesor.user.get_full_name()} asignado al curso {curso.name} - Grupo {course_group.group_code}")
            
            # Matricular estudiantes ADA en este curso (solo si es la primera vez que vemos este curso)
            matriculados = 0
            if created:  # Solo matricular si es un nuevo grupo de curso
                for estudiante in estudiantes_ada:
                    enrollment, enrollment_created = Enrollment.objects.get_or_create(
                        student=estudiante,
                        course_group=course_group,
                        academic_period=periodo,
                        defaults={'enrollment_date': '2024-03-01'}
                    )
                    if enrollment_created:
                        matriculados += 1
                        
                print(f"  ✓ {matriculados} estudiantes ADA matriculados en {curso.name}")
            else:
                # Contar matrículas existentes para este grupo
                matriculas_existentes = Enrollment.objects.filter(
                    course_group=course_group,
                    academic_period=periodo
                ).count()
                print(f"  ✓ {matriculas_existentes} estudiantes ya matriculados en {curso.name}")
            
        except Exception as e:
            print(f"Error procesando fila {idx + 1}: {e}")
            continue
    
    print("\n=== RESUMEN FINAL ===")
    print(f"Total profesores: {Teacher.objects.count()}")
    print(f"Total cursos: {Course.objects.count()}")
    print(f"Total grupos de curso: {CourseGroup.objects.count()}")
    print(f"Total estudiantes: {Student.objects.count()}")
    print(f"Total matrículas: {Enrollment.objects.count()}")
    print(f"Total períodos académicos: {AcademicPeriod.objects.count()}")

if __name__ == "__main__":
    procesar_profesores_y_cursos()