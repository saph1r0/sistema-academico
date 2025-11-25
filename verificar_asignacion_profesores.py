#!/usr/bin/env python
"""
Script para verificar y corregir la asignación de cursos a profesores
"""

import os
import sys
import pandas as pd

def verificar_excel_profesores():
    """Verificar el contenido del Excel de profesores"""
    print("🔍 VERIFICANDO EXCEL DE PROFESORES")
    print("=" * 50)
    
    excel_path = "EXELS/profesores.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"❌ No se encontró el archivo: {excel_path}")
        return False
    
    try:
        # Leer el Excel
        df = pd.read_excel(excel_path)
        
        print(f"📊 Archivo encontrado: {excel_path}")
        print(f"📋 Filas en el Excel: {len(df)}")
        print(f"📋 Columnas: {list(df.columns)}")
        
        print("\n📝 PRIMERAS 10 FILAS:")
        print(df.head(10).to_string())
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   - Total de filas: {len(df)}")
        print(f"   - Profesores únicos: {df.iloc[:, 0].nunique() if len(df) > 0 else 0}")
        print(f"   - Cursos únicos: {df.iloc[:, 1].nunique() if len(df.columns) > 1 else 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo Excel: {str(e)}")
        return False


def crear_script_asignacion():
    """Crear script para asignar cursos correctamente"""
    script_content = '''#!/usr/bin/env python
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
                
                print(f"\\n📝 Procesando: {profesor_nombre} -> {curso_nombre}")
                
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
        
        print(f"\\n📊 RESUMEN:")
        print(f"   ✅ Asignaciones creadas: {asignaciones_creadas}")
        print(f"   ❌ Errores: {errores}")
        print(f"   📋 Total profesores: {Teacher.objects.count()}")
        print(f"   📋 Total cursos: {Course.objects.count()}")
        print(f"   📋 Total asignaciones: {CourseGroup.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    asignar_cursos_desde_excel()
'''
    
    with open('asignar_cursos_profesores.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de asignación creado: asignar_cursos_profesores.py")


def main():
    """Función principal"""
    print("🎯 DIAGNÓSTICO Y SOLUCIÓN DE ASIGNACIÓN DE CURSOS")
    print("=" * 60)
    
    # 1. Verificar Excel
    excel_ok = verificar_excel_profesores()
    
    if excel_ok:
        # 2. Crear script de asignación
        crear_script_asignacion()
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Ejecutar: python asignar_cursos_profesores.py")
        print("2. Verificar que los cursos se asignaron correctamente")
        print("3. Continuar con la implementación de funcionalidades")
    
    print("\n📋 FUNCIONALIDADES A IMPLEMENTAR:")
    print("✓ Módulo del Alumno:")
    print("  - Ver notas por fases (primera, segunda, tercera)")
    print("  - Matrícula de laboratorio (opciones A y B con horarios)")
    print("  - Barra de navegación lateral izquierda")
    
    print("✓ Módulo del Docente:")
    print("  - Tomar asistencia (PRESENTE/FALTA)")
    print("  - Ingresar notas por períodos via Excel")
    print("  - Ver estadísticas (mayor, menor, promedio)")
    print("  - Gráficos de estadísticas de notas")
    print("  - Reserva automática de ambientes (9 aulas/labs)")
    
    print("✓ Control de fechas:")
    print("  - Secretaria habilita fechas para subir notas")
    print("  - Profesores solo pueden subir cuando esté habilitado")


if __name__ == "__main__":
    main()