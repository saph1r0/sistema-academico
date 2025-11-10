#!/usr/bin/env python
"""
Script para asignar cursos a profesores desde Excel
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod
)
from django.utils import timezone

def asignar_cursos_desde_excel():
    """Asignar cursos a profesores desde el Excel"""
    print("🔧 ASIGNANDO CURSOS DESDE EXCEL")
    print("=" * 40)
    
    # Leer Excel
    excel_path = "EXELS/profesores.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"❌ No se encontró: {excel_path}")
        return
    
    try:
        df = pd.read_excel(excel_path)
        print(f"📊 Leyendo {len(df)} filas del Excel")
        
        # Obtener o crear período académico
        period, created = AcademicPeriod.objects.get_or_create(
            name='2024-I',
            defaults={
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date(),
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Período académico creado: {period.name}")
        
        asignaciones_creadas = 0
        errores = 0
        
        for index, row in df.iterrows():
            try:
                # Obtener datos de la fila
                profesor_nombre = str(row.iloc[0]).strip()
                curso_nombre = str(row.iloc[1]).strip()
                
                if pd.isna(profesor_nombre) or pd.isna(curso_nombre):
                    continue
                
                print(f"\n📝 Procesando: {profesor_nombre} -> {curso_nombre}")
                
                # Buscar profesor por nombre
                teacher = None
                for t in Teacher.objects.all():
                    if profesor_nombre.lower() in t.user.get_full_name().lower():
                        teacher = t
                        break
                
                if not teacher:
                    print(f"   ⚠️ Profesor no encontrado: {profesor_nombre}")
                    errores += 1
                    continue
                
                # Crear o obtener curso
                course, created = Course.objects.get_or_create(
                    name=curso_nombre,
                    defaults={
                        'code': f'CURSO_{index+1:03d}',
                        'credits': 3,
                        'theory_hours': 4,
                        'practice_hours': 2
                    }
                )
                
                if created:
                    print(f"   ✅ Curso creado: {course.name}")
                
                # Crear grupo de curso
                course_group, created = CourseGroup.objects.get_or_create(
                    course=course,
                    teacher=teacher,
                    academic_period=period,
                    group_code='A',
                    defaults={
                        'capacity': 30,
                        'total_planned_classes': 68,
                        'classes_attended_by_teacher': 0,
                        'course_progress_percentage': 0.0
                    }
                )
                
                if created:
                    print(f"   ✅ Asignación creada: {teacher.user.get_full_name()} -> {course.name}")
                    asignaciones_creadas += 1
                else:
                    print(f"   ℹ️ Asignación ya existe")
                
            except Exception as e:
                print(f"   ❌ Error procesando fila {index}: {str(e)}")
                errores += 1
        
        print(f"\n📊 RESUMEN:")
        print(f"   ✅ Asignaciones creadas: {asignaciones_creadas}")
        print(f"   ❌ Errores: {errores}")
        print(f"   📋 Total profesores: {Teacher.objects.count()}")
        print(f"   📋 Total cursos: {Course.objects.count()}")
        print(f"   📋 Total asignaciones: {CourseGroup.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    asignar_cursos_desde_excel()
