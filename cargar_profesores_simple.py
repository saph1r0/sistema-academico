#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para cargar profesores del Excel y asignarlos a cursos
"""
import os
import sys
import django
import pandas as pd
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import User, Teacher, Course, CourseGroup, AcademicPeriod

def main():
    """Carga profesores del Excel y los asigna a cursos"""
    print("=" * 80)
    print("CARGANDO PROFESORES DEL EXCEL")
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
        
        # Mostrar primeras filas para entender la estructura
        print("\nPrimeras 5 filas:")
        print(df.head())
        
        # Procesar cada profesor
        profesores_creados = 0
        profesores_existentes = 0
        
        for index, row in df.iterrows():
            try:
                # Extraer datos del profesor (ajustar según las columnas reales)
                # Asumiendo columnas comunes, ajustar según el Excel real
                nombre_completo = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
                email = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else ""
                
                if not email or not nombre_completo:
                    print(f"Fila {index + 1}: Datos incompletos, saltando...")
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
                
                print(f"\nProcesando: {nombre_completo} ({email})")
                
                # Verificar si el usuario ya existe
                user_exists = User.objects.filter(institutional_email=email).exists()
                
                if user_exists:
                    print(f"  Usuario ya existe: {email}")
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
                teacher = Teacher.objects.create(
                    user=user,
                    teacher_code=f"PROF{index + 1:03d}",
                    department="Ingeniería de Sistemas",
                    specialty="Profesor",
                    hours_per_week=20
                )
                
                print(f"  ✓ Profesor creado: {email} (contraseña: {password})")
                profesores_creados += 1
                
            except Exception as e:
                print(f"  ERROR procesando fila {index + 1}: {str(e)}")
                continue
        
        print(f"\n" + "=" * 80)
        print("RESUMEN:")
        print(f"Profesores creados: {profesores_creados}")
        print(f"Profesores existentes: {profesores_existentes}")
        print("=" * 80)
        
        # Ahora asignar profesores a cursos automáticamente
        asignar_profesores_a_cursos()
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def asignar_profesores_a_cursos():
    """Asigna profesores a cursos automáticamente"""
    print("\nASIGNANDO PROFESORES A CURSOS...")
    
    try:
        # Obtener todos los profesores y cursos
        profesores = list(Teacher.objects.all())
        course_groups = CourseGroup.objects.all()
        
        if not profesores:
            print("No hay profesores disponibles para asignar")
            return
        
        print(f"Profesores disponibles: {len(profesores)}")
        print(f"Grupos de cursos: {len(course_groups)}")
        
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