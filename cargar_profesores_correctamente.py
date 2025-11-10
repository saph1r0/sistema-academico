#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para cargar CORRECTAMENTE los profesores del Excel
Usando los NOMBRES REALES de los profesores, no los nombres de cursos
"""
import os
import sys
import django
import pandas as pd

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import User, Teacher, CourseGroup

def main():
    """Carga CORRECTAMENTE los profesores del Excel usando nombres reales"""
    print("=" * 80)
    print("CORRIGIENDO: CARGANDO PROFESORES REALES DEL EXCEL")
    print("=" * 80)
    
    try:
        # Leer archivo de profesores
        excel_path = 'EXELS/profesores.xlsx'
        if not os.path.exists(excel_path):
            print(f"ERROR: No se encontró el archivo {excel_path}")
            return False
        
        print(f"Leyendo archivo: {excel_path}")
        df = pd.read_excel(excel_path)
        
        print(f"Columnas encontradas: {list(df.columns)}")
        print(f"Total de filas: {len(df)}")
        
        # Mostrar estructura del Excel
        print("\nEstructura del Excel:")
        print("Columna 'Docentes' (índice 5):", df.columns[5] if len(df.columns) > 5 else "No existe")
        print("Columna 'Correo' (índice 6):", df.columns[6] if len(df.columns) > 6 else "No existe")
        
        # Mostrar primeras filas para confirmar estructura
        print("\nPrimeras 3 filas:")
        for i in range(min(3, len(df))):
            docente = df.iloc[i, 5] if len(df.columns) > 5 else "N/A"  # Columna Docentes
            correo = df.iloc[i, 6] if len(df.columns) > 6 else "N/A"   # Columna Correo
            print(f"Fila {i+1}: Docente='{docente}' | Correo='{correo}'")
        
        # LIMPIAR PROFESORES INCORRECTOS PRIMERO
        print(f"\n" + "=" * 80)
        print("LIMPIANDO PROFESORES INCORRECTOS...")
        print("=" * 80)
        
        # Eliminar profesores con nombres de cursos (incorrectos)
        profesores_incorrectos = Teacher.objects.filter(
            user__first_name__in=[
                'LENGUA', 'METODOLOGIA', 'ARTE', 'FUNDAMENTOS', 'ESTRUCTURAS',
                'CIENCIA', 'COMUNICACION', 'ARQUITECTURA', 'CIENCIAS', 'DESARROLLO',
                'TRABAJO', 'INGLES', 'CIUDADANIA', 'ALGORITMOS', 'TEORIA', 'BASE',
                'ALGEBRA', 'ESTADISTICA', 'ECOLOGIA', 'ANALISIS', 'INGENIERIA',
                'ECUACIONES', 'PROGRAMACION', 'SISTEMAS', 'MATEMATICA', 'INVESTIGACION',
                'REDES', 'COMPUTACION', 'INTELIGENCIA', 'INTERACCION', 'PROYECTO',
                'SEGURIDAD', 'RELACIONES', 'FISICA', 'TOPICOS', 'BIG', 'ETICA',
                'BIOINFORMATICA', 'CLOUD', 'INTERNET', 'ROBOTICA', 'PRACTICAS',
                'METODOLOGˆ', 'INTRODUCCIˆ', 'INGLˆ', 'PROGRAMACIˆ', 'Cˆ',
                'LINGˆ', 'REALIDAD'
            ]
        )
        
        eliminados = 0
        for profesor in profesores_incorrectos:
            print(f"Eliminando profesor incorrecto: {profesor.user.first_name} {profesor.user.last_name}")
            profesor.user.delete()  # Esto también elimina el Teacher por CASCADE
            eliminados += 1
        
        print(f"Profesores incorrectos eliminados: {eliminados}")
        
        # PROCESAR PROFESORES REALES
        print(f"\n" + "=" * 80)
        print("CARGANDO PROFESORES REALES...")
        print("=" * 80)
        
        profesores_creados = 0
        profesores_existentes = 0
        errores = 0
        profesores_unicos = set()  # Para evitar duplicados
        
        for index, row in df.iterrows():
            try:
                # Obtener nombre del docente (columna 5) y correo (columna 6)
                nombre_docente = str(row.iloc[5]) if not pd.isna(row.iloc[5]) else ""
                correo_docente = str(row.iloc[6]) if not pd.isna(row.iloc[6]) else ""
                
                # Limpiar datos
                nombre_docente = nombre_docente.strip()
                correo_docente = correo_docente.strip()
                
                if not nombre_docente or not correo_docente or nombre_docente.lower() == 'nan' or correo_docente.lower() == 'nan':
                    print(f"Fila {index + 1}: Datos incompletos - Docente: '{nombre_docente}' Correo: '{correo_docente}'")
                    errores += 1
                    continue
                
                # Evitar duplicados
                if correo_docente in profesores_unicos:
                    continue
                profesores_unicos.add(correo_docente)
                
                # Separar nombre y apellidos
                partes_nombre = nombre_docente.split(',')
                if len(partes_nombre) >= 2:
                    # Formato: "APELLIDOS, NOMBRES"
                    apellidos = partes_nombre[0].strip()
                    nombres = partes_nombre[1].strip()
                    primer_nombre = nombres.split()[0] if nombres.split() else nombres
                else:
                    # Formato directo
                    partes = nombre_docente.split()
                    if len(partes) >= 2:
                        primer_nombre = partes[0]
                        apellidos = " ".join(partes[1:])
                    else:
                        primer_nombre = nombre_docente
                        apellidos = ""
                
                # Crear contraseña: primer nombre + 123
                password = f"{primer_nombre.lower()}123"
                
                print(f"\nProcesando: {nombre_docente} ({correo_docente})")
                
                # Verificar si el usuario ya existe
                if User.objects.filter(institutional_email=correo_docente).exists():
                    print(f"  Ya existe: {correo_docente}")
                    profesores_existentes += 1
                    continue
                
                # Crear usuario
                user = User.objects.create(
                    institutional_email=correo_docente,
                    first_name=primer_nombre.title(),
                    last_name=apellidos.title(),
                    role='teacher',
                    is_active=True
                )
                user.set_password(password)
                user.save()
                
                # Crear profesor
                teacher = Teacher.objects.create(
                    user=user,
                    teacher_code=f"DOC{profesores_creados + 1:03d}",
                    department="Ingeniería de Sistemas",
                    specialty="Profesor",
                    hours_per_week=20
                )
                
                print(f"  ✓ CREADO: {correo_docente} (contraseña: {password})")
                print(f"    Nombre: {primer_nombre.title()} {apellidos.title()}")
                profesores_creados += 1
                
            except Exception as e:
                print(f"  ERROR en fila {index + 1}: {str(e)}")
                errores += 1
                continue
        
        print(f"\n" + "=" * 80)
        print("RESUMEN FINAL:")
        print("=" * 80)
        print(f"Profesores REALES creados: {profesores_creados}")
        print(f"Profesores existentes: {profesores_existentes}")
        print(f"Profesores incorrectos eliminados: {eliminados}")
        print(f"Errores: {errores}")
        
        # Mostrar todos los profesores REALES en la base de datos
        print(f"\n" + "=" * 80)
        print("PROFESORES REALES EN LA BASE DE DATOS:")
        print("=" * 80)
        
        all_teachers = Teacher.objects.all().select_related('user').order_by('user__first_name')
        for i, teacher in enumerate(all_teachers, 1):
            print(f"{i:2d}. {teacher.user.first_name} {teacher.user.last_name}")
            print(f"     Email: {teacher.user.institutional_email}")
            print(f"     Contraseña: {teacher.user.first_name.lower()}123")
            print()
        
        print(f"TOTAL PROFESORES REALES EN BD: {all_teachers.count()}")
        
        # Asignar profesores a cursos
        asignar_profesores_a_cursos()
        
        return True
        
    except Exception as e:
        print(f"ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def asignar_profesores_a_cursos():
    """Asigna profesores REALES a cursos de forma rotativa"""
    print(f"\n" + "=" * 80)
    print("ASIGNANDO PROFESORES REALES A CURSOS...")
    print("=" * 80)
    
    try:
        # Obtener todos los profesores y cursos
        profesores = list(Teacher.objects.all())
        course_groups = CourseGroup.objects.all()
        
        print(f"Profesores REALES disponibles: {len(profesores)}")
        print(f"Grupos de cursos: {len(course_groups)}")
        
        if not profesores:
            print("No hay profesores disponibles para asignar")
            return
        
        # Asignar profesores de forma rotativa
        asignaciones = 0
        for i, course_group in enumerate(course_groups):
            # Seleccionar profesor de forma rotativa
            profesor = profesores[i % len(profesores)]
            
            # Asignar profesor al grupo de curso
            course_group.teacher = profesor
            course_group.save()
            
            print(f"  ✓ {course_group.course.name} -> {profesor.user.first_name} {profesor.user.last_name}")
            asignaciones += 1
        
        print(f"\nAsignaciones completadas: {asignaciones}")
        
    except Exception as e:
        print(f"ERROR asignando profesores: {str(e)}")

if __name__ == '__main__':
    main()