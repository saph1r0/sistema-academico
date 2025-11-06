#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para cargar los profesores REALES del Excel
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
    """Carga los profesores REALES del Excel"""
    print("=" * 80)
    print("CARGANDO PROFESORES REALES DEL EXCEL")
    print("=" * 80)
    
    try:
        # Leer archivo de profesores
        excel_path = 'EXELS/profesores.xlsx'
        if not os.path.exists(excel_path):
            print(f"ERROR: No se encontró el archivo {excel_path}")
            return False
        
        print(f"Leyendo archivo: {excel_path}")
        df = pd.read_excel(excel_path)
        
        print(f"Columnas: {list(df.columns)}")
        print(f"Total filas: {len(df)}")
        
        # Ejemplo de lo que vamos a procesar
        print("\nEjemplos de profesores a procesar:")
        for i in range(min(5, len(df))):
            docente = str(df.iloc[i, 5]) if len(df.columns) > 5 else "N/A"
            correo = str(df.iloc[i, 6]) if len(df.columns) > 6 else "N/A"
            if docente != "nan" and correo != "nan":
                print(f"  {docente} -> {correo}")
        
        profesores_creados = 0
        profesores_existentes = 0
        errores = 0
        profesores_unicos = set()
        
        for index, row in df.iterrows():
            try:
                # Obtener datos del profesor (columna 5 = Docentes, columna 6 = Correo)
                nombre_docente = str(row.iloc[5]) if not pd.isna(row.iloc[5]) else ""
                correo_docente = str(row.iloc[6]) if not pd.isna(row.iloc[6]) else ""
                
                # Limpiar datos
                nombre_docente = nombre_docente.strip()
                correo_docente = correo_docente.strip()
                
                # Validar datos
                if (not nombre_docente or not correo_docente or 
                    nombre_docente.lower() == 'nan' or correo_docente.lower() == 'nan' or
                    '@' not in correo_docente):
                    errores += 1
                    continue
                
                # Evitar duplicados
                if correo_docente in profesores_unicos:
                    continue
                profesores_unicos.add(correo_docente)
                
                # Verificar si ya existe
                if User.objects.filter(institutional_email=correo_docente).exists():
                    profesores_existentes += 1
                    continue
                
                # Procesar nombre: formato "APELLIDOS, NOMBRES"
                if ',' in nombre_docente:
                    partes = nombre_docente.split(',', 1)
                    apellidos = partes[0].strip().title()
                    nombres = partes[1].strip().title()
                    primer_nombre = nombres.split()[0] if nombres.split() else nombres
                else:
                    # Formato directo
                    partes = nombre_docente.split()
                    primer_nombre = partes[0].title() if partes else nombre_docente.title()
                    apellidos = " ".join(partes[1:]).title() if len(partes) > 1 else ""
                
                # Contraseña: primer nombre + 123
                password = f"{primer_nombre.lower()}123"
                
                # Crear usuario
                user = User.objects.create(
                    institutional_email=correo_docente,
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
                    teacher_code=f"DOC{len(profesores_unicos):03d}",
                    department="Ingeniería de Sistemas",
                    specialty="Profesor",
                    hours_per_week=20
                )
                
                print(f"✓ {primer_nombre} {apellidos} ({correo_docente}) - contraseña: {password}")
                profesores_creados += 1
                
            except Exception as e:
                print(f"ERROR fila {index + 1}: {str(e)}")
                errores += 1
                continue
        
        print(f"\n" + "=" * 80)
        print("RESUMEN:")
        print("=" * 80)
        print(f"Profesores REALES creados: {profesores_creados}")
        print(f"Profesores existentes: {profesores_existentes}")
        print(f"Errores: {errores}")
        
        # Mostrar algunos ejemplos de profesores creados
        print(f"\n" + "=" * 50)
        print("EJEMPLOS DE PROFESORES CREADOS:")
        print("=" * 50)
        
        nuevos_profesores = Teacher.objects.filter(
            user__institutional_email__in=list(profesores_unicos)
        ).select_related('user')[:10]
        
        for teacher in nuevos_profesores:
            print(f"• {teacher.user.first_name} {teacher.user.last_name}")
            print(f"  Email: {teacher.user.institutional_email}")
            print(f"  Contraseña: {teacher.user.first_name.lower()}123")
            print()
        
        total_profesores = Teacher.objects.count()
        print(f"TOTAL PROFESORES EN BD: {total_profesores}")
        
        # Asignar algunos profesores a cursos
        if profesores_creados > 0:
            asignar_profesores_reales()
        
        return True
        
    except Exception as e:
        print(f"ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def asignar_profesores_reales():
    """Asigna profesores REALES a cursos"""
    print(f"\n" + "=" * 50)
    print("ASIGNANDO PROFESORES REALES A CURSOS...")
    print("=" * 50)
    
    try:
        # Obtener profesores REALES (con emails reales de unsa.edu.pe)
        profesores_reales = Teacher.objects.filter(
            user__institutional_email__contains='@unsa.edu.pe'
        ).exclude(
            user__first_name__in=['Juan']  # Excluir el profesor de prueba
        )
        
        course_groups = CourseGroup.objects.all()
        
        print(f"Profesores REALES disponibles: {profesores_reales.count()}")
        print(f"Grupos de cursos: {course_groups.count()}")
        
        if profesores_reales.exists():
            # Asignar profesores de forma rotativa
            profesores_list = list(profesores_reales)
            for i, course_group in enumerate(course_groups):
                profesor = profesores_list[i % len(profesores_list)]
                course_group.teacher = profesor
                course_group.save()
                
                print(f"✓ {course_group.course.name} -> {profesor.user.first_name} {profesor.user.last_name}")
        
    except Exception as e:
        print(f"ERROR asignando profesores: {str(e)}")

if __name__ == '__main__':
    main()