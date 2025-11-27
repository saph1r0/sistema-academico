#!/usr/bin/env python
"""
Script para asignar cursos a profesores basándose en el Excel de profesores.
Lee la columna "Asignatura" y asigna cada curso al profesor correspondiente.
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

from repositorio.postgres_repository.models import Teacher, Course, CourseGroup, AcademicPeriod, User

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

def buscar_profesor_por_email(email):
    """Busca un profesor por su email"""
    try:
        user = User.objects.filter(institutional_email=email, role='teacher').first()
        if user and hasattr(user, 'teacher'):
            return user.teacher
        return None
    except Exception as e:
        print(f"Error buscando profesor por email {email}: {e}")
        return None

def buscar_profesor_por_nombre(nombre, apellido):
    """Busca un profesor por nombre y apellido"""
    try:
        # Buscar por nombre y apellido exactos
        user = User.objects.filter(
            first_name__iexact=nombre,
            last_name__iexact=apellido,
            role='teacher'
        ).first()
        
        if user and hasattr(user, 'teacher'):
            return user.teacher
            
        # Buscar por apellido solamente si no se encuentra
        user = User.objects.filter(
            last_name__icontains=apellido,
            role='teacher'
        ).first()
        
        if user and hasattr(user, 'teacher'):
            return user.teacher
            
        return None
    except Exception as e:
        print(f"Error buscando profesor por nombre {nombre} {apellido}: {e}")
        return None

def buscar_curso_por_nombre(nombre_curso):
    """Busca un curso por su nombre"""
    try:
        # Buscar curso exacto
        curso = Course.objects.filter(name__iexact=nombre_curso).first()
        if curso:
            return curso
            
        # Buscar curso que contenga el nombre
        curso = Course.objects.filter(name__icontains=nombre_curso).first()
        if curso:
            return curso
            
        # Buscar por palabras clave
        palabras = nombre_curso.split()[:3]  # Primeras 3 palabras
        cursos = Course.objects.all()
        for palabra in palabras:
            if len(palabra) > 3:  # Solo palabras significativas
                cursos = cursos.filter(name__icontains=palabra)
        
        return cursos.first()
        
    except Exception as e:
        print(f"Error buscando curso {nombre_curso}: {e}")
        return None

def asignar_cursos_a_profesores():
    """Asigna cursos a profesores basándose en el Excel"""
    
    print("=== ASIGNANDO CURSOS A PROFESORES ===")
    
    # Leer el archivo Excel de profesores
    try:
        df_profesores = pd.read_excel('EXELS/profesores.xlsx')
        print(f"Archivo leído correctamente. Filas: {len(df_profesores)}")
    except Exception as e:
        print(f"Error leyendo archivo Excel: {e}")
        return
    
    # Obtener período académico
    periodo = AcademicPeriod.objects.filter(is_active=True).first()
    if not periodo:
        periodo = AcademicPeriod.objects.first()
    
    if not periodo:
        print("Error: No hay períodos académicos disponibles")
        return
    
    print(f"Usando período académico: {periodo.name}")
    
    # Procesar cada fila del Excel
    asignaciones_exitosas = 0
    asignaciones_fallidas = 0
    
    for idx, row in df_profesores.iterrows():
        try:
            print(f"\n--- Procesando fila {idx + 1} ---")
            
            # Extraer datos
            nombre_docente = row.get('Docentes', '')
            email_docente = row.get('Correo', '')
            nombre_asignatura = row.get('Asignatura', '')
            grupo = row.get('Grupo', 'A')
            
            print(f"Docente: {nombre_docente}")
            print(f"Email: {email_docente}")
            print(f"Asignatura: {nombre_asignatura}")
            print(f"Grupo: {grupo}")
            
            # Buscar profesor
            profesor = None
            
            # Primero buscar por email
            if email_docente:
                profesor = buscar_profesor_por_email(email_docente)
                if profesor:
                    print(f"  ✓ Profesor encontrado por email: {profesor.user.get_full_name()}")
            
            # Si no se encuentra por email, buscar por nombre
            if not profesor and nombre_docente:
                nombre, apellido = extraer_nombre_profesor(nombre_docente)
                if nombre or apellido:
                    profesor = buscar_profesor_por_nombre(nombre, apellido)
                    if profesor:
                        print(f"  ✓ Profesor encontrado por nombre: {profesor.user.get_full_name()}")
            
            if not profesor:
                print(f"  ✗ Profesor NO encontrado: {nombre_docente}")
                asignaciones_fallidas += 1
                continue
            
            # Buscar curso
            if not nombre_asignatura:
                print(f"  ✗ No hay nombre de asignatura")
                asignaciones_fallidas += 1
                continue
                
            curso = buscar_curso_por_nombre(nombre_asignatura)
            if not curso:
                print(f"  ✗ Curso NO encontrado: {nombre_asignatura}")
                asignaciones_fallidas += 1
                continue
            
            print(f"  ✓ Curso encontrado: {curso.name}")
            
            # Crear o actualizar CourseGroup
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
            
            # Si ya existe, actualizar el profesor
            if not created:
                course_group.teacher = profesor
                course_group.save()
                print(f"  ✓ Grupo actualizado: {profesor.user.get_full_name()} -> {curso.name} - Grupo {course_group.group_code}")
            else:
                print(f"  ✓ Grupo creado: {profesor.user.get_full_name()} -> {curso.name} - Grupo {course_group.group_code}")
            
            asignaciones_exitosas += 1
            
        except Exception as e:
            print(f"  ✗ Error procesando fila {idx + 1}: {e}")
            asignaciones_fallidas += 1
            continue
    
    print(f"\n=== RESUMEN DE ASIGNACIONES ===")
    print(f"Asignaciones exitosas: {asignaciones_exitosas}")
    print(f"Asignaciones fallidas: {asignaciones_fallidas}")
    print(f"Total procesadas: {len(df_profesores)}")
    
    # Mostrar resumen por profesor
    print(f"\n=== CURSOS POR PROFESOR ===")
    profesores_con_cursos = Teacher.objects.filter(
        coursegroup__academic_period=periodo
    ).distinct()
    
    for profesor in profesores_con_cursos:
        cursos = CourseGroup.objects.filter(
            teacher=profesor,
            academic_period=periodo
        )
        print(f"{profesor.user.get_full_name()}: {cursos.count()} curso(s)")
        for course_group in cursos:
            print(f"  - {course_group.course.name} - Grupo {course_group.group_code}")

if __name__ == "__main__":
    asignar_cursos_a_profesores()