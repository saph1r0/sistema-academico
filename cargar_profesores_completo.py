#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para cargar TODOS los profesores del Excel a la base de datos
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
    """Carga TODOS los profesores del Excel"""
    print("=" * 80)
    print("CARGANDO TODOS LOS PROFESORES DEL EXCEL")
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
        print("\nPrimeras 3 filas del Excel:")
        for i in range(min(3, len(df))):
            print(f"Fila {i+1}: {list(df.iloc[i])}")
        
        # Procesar cada profesor
        profesores_creados = 0
        profesores_existentes = 0
        errores = 0
        
        for index, row in df.iterrows():
            try:
                # Intentar diferentes columnas para nombre y email
                nombre_completo = ""
                email = ""
                
                # Buscar nombre en las primeras columnas
                for col_idx in range(min(5, len(row))):
                    valor = str(row.iloc[col_idx]) if not pd.isna(row.iloc[col_idx]) else ""
                    if valor and valor.lower() != 'nan':
                        if '@' in valor:  # Es un email
                            email = valor.strip()
                        elif len(valor.split()) >= 2 and not nombre_completo:  # Es un nombre completo
                            nombre_completo = valor.strip()
                
                # Si no encontramos email, intentar generar uno
                if not email and nombre_completo:
                    # Generar email basado en el nombre
                    partes = nombre_completo.lower().split()
                    if len(partes) >= 2:
                        email = f"{partes[0]}.{partes[1]}@unsa.edu.pe"
                
                if not nombre_completo or not email:
                    print(f"Fila {index + 1}: Datos incompletos - Nombre: '{nombre_completo}' Email: '{email}'")
                    errores += 1
                    continue
                
                # Limpiar y separar nombre
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
                if User.objects.filter(institutional_email=email).exists():
                    print(f"  Ya existe: {email}")
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
                
                print(f"  ✓ CREADO: {email} (contraseña: {password})")
                profesores_creados += 1
                
            except Exception as e:
                print(f"  ERROR en fila {index + 1}: {str(e)}")
                errores += 1
                continue
        
        print(f"\n" + "=" * 80)
        print("RESUMEN FINAL:")
        print("=" * 80)
        print(f"Profesores CREADOS: {profesores_creados}")
        print(f"Profesores existentes: {profesores_existentes}")
        print(f"Errores: {errores}")
        print(f"Total procesado: {profesores_creados + profesores_existentes + errores}")
        
        # Mostrar todos los profesores en la base de datos
        print(f"\n" + "=" * 80)
        print("TODOS LOS PROFESORES EN LA BASE DE DATOS:")
        print("=" * 80)
        
        all_teachers = Teacher.objects.all().select_related('user')
        for i, teacher in enumerate(all_teachers, 1):
            print(f"{i:2d}. {teacher.user.first_name} {teacher.user.last_name}")
            print(f"     Email: {teacher.user.institutional_email}")
            print(f"     Código: {teacher.teacher_code}")
            print(f"     Contraseña: {teacher.user.first_name.lower()}123")
            print()
        
        print(f"TOTAL PROFESORES EN BD: {all_teachers.count()}")
        
        # Asignar profesores a cursos
        if profesores_creados > 0:
            asignar_profesores_a_cursos()
        
        return True
        
    except Exception as e:
        print(f"ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def asignar_profesores_a_cursos():
    """Asigna profesores a cursos de forma rotativa"""
    print(f"\n" + "=" * 80)
    print("ASIGNANDO PROFESORES A CURSOS...")
    print("=" * 80)
    
    try:
        # Obtener todos los profesores y cursos
        profesores = list(Teacher.objects.all())
        course_groups = CourseGroup.objects.all()
        
        print(f"Profesores disponibles: {len(profesores)}")
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