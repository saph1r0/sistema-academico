#!/usr/bin/env python
"""
Script para matricular estudiantes ADA SOLO en:
- 5 cursos específicos
- Solo grupo A (no grupo B)
- Cursos exactos: MATEMÁTICA APLICADA A LA COMPUTACIÓN, SISTEMAS OPERATIVOS, 
  TRABAJO INTERDISCIPLINAR II, INGENIERÍA DE SOFTWARE II, ANÁLISIS Y DISEÑO DE ALGORITMOS
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import Student, CourseGroup, Enrollment, AcademicPeriod, Course

def matricular_ada_solo_grupo_a():
    """Matricula estudiantes ADA solo en grupo A de 5 cursos específicos"""
    
    print("=== MATRICULANDO ESTUDIANTES ADA SOLO EN GRUPO A ===")
    
    # Obtener todos los estudiantes ADA
    estudiantes_ada = Student.objects.filter(
        student_code__regex=r'^[0-9]+'  # Códigos que empiezan con números
    )
    
    print(f"Estudiantes ADA encontrados: {estudiantes_ada.count()}")
    
    # PASO 1: Eliminar todas las matrículas existentes de estudiantes ADA
    print("\n1. Eliminando matrículas existentes de estudiantes ADA...")
    matriculas_eliminadas = Enrollment.objects.filter(student__in=estudiantes_ada).delete()
    print(f"   ✓ Eliminadas {matriculas_eliminadas[0]} matrículas existentes")
    
    # PASO 2: Obtener período académico
    periodo = AcademicPeriod.objects.filter(is_active=True).first()
    if not periodo:
        periodo = AcademicPeriod.objects.first()
    
    if not periodo:
        print("Error: No hay períodos académicos disponibles")
        return
    
    print(f"Usando período académico: {periodo.name}")
    
    # PASO 3: Buscar cursos específicos EXACTOS
    cursos_objetivo = [
        "MATEMÁTICA APLICADA A LA COMPUTACIÓN",
        "SISTEMAS OPERATIVOS", 
        "TRABAJO INTERDISCIPLINAR II",  # Específicamente II, no III
        "INGENIERÍA DE SOFTWARE II",
        "ANÁLISIS Y DISEÑO DE ALGORITMOS"
    ]
    
    print(f"\nBuscando cursos específicos:")
    cursos_encontrados = []
    
    for curso_nombre in cursos_objetivo:
        print(f"\nBuscando: {curso_nombre}")
        
        # Buscar curso exacto o muy similar
        curso = None
        
        # Estrategia 1: Buscar por nombre exacto
        curso = Course.objects.filter(name__iexact=curso_nombre).first()
        if curso:
            print(f"  ✓ Encontrado exacto: {curso.name}")
            cursos_encontrados.append(curso)
            continue
        
        # Estrategia 2: Buscar por palabras clave específicas
        if "MATEMÁTICA" in curso_nombre:
            cursos_temp = Course.objects.filter(name__icontains="MATEMÁTICA")
            cursos_temp = cursos_temp.filterQ(name__icontains="APLICADA")
            curso = cursos_temp.filter(name__icontains="COMPUTACIÓN").first()
        elif "SISTEMAS OPERATIVOS" in curso_nombre:
            cursos_temp = Course.objects.filter(name__icontains="SISTEMAS")
            curso = cursos_temp.filter(name__icontains="OPERATIVOS").first()
        elif "TRABAJO INTERDISCIPLINAR II" in curso_nombre:
            # Buscar específicamente II, no III
            cursos_temp = Course.objects.filter(name__icontains="TRABAJO")
            cursos_temp = cursos_temp.filter(name__icontains="INTERDISCIPLINAR")
            cursos_temp = cursos_temp.filter(name__icontains="II")
            curso = cursos_temp.exclude(name__icontains="III").first()
        elif "INGENIERÍA DE SOFTWARE II" in curso_nombre:
            cursos_temp = Course.objects.filter(name__icontains="INGENIERÍA")
            cursos_temp = cursos_temp.filter(name__icontains="SOFTWARE")
            curso = cursos_temp.filter(name__icontains="II").first()
        elif "ANÁLISIS Y DISEÑO" in curso_nombre:
            cursos_temp = Course.objects.filter(name__icontains="ANÁLISIS")
            curso = cursos_temp.filter(name__icontains="DISEÑO").first()
        
        if curso:
            print(f"  ✓ Encontrado similar: {curso.name}")
            cursos_encontrados.append(curso)
        else:
            print(f"  ✗ NO encontrado: {curso_nombre}")
    
    if not cursos_encontrados:
        print("\nError: No se encontraron los cursos específicos")
        print("Cursos disponibles:")
        for curso in Course.objects.all():
            print(f"  - {curso.name}")
        return
    
    print(f"\nCursos encontrados: {len(cursos_encontrados)}")
    for curso in cursos_encontrados:
        print(f"  - {curso.name}")
    
    # PASO 4: Obtener SOLO grupos A de estos cursos
    course_groups_a = CourseGroup.objects.filter(
        course__in=cursos_encontrados,
        academic_period=periodo,
        group_code='A'  # SOLO GRUPO A
    )
    
    print(f"\nGrupos A encontrados: {course_groups_a.count()}")
    for group in course_groups_a:
        print(f"  - {group.course.name} - Grupo {group.group_code}")
    
    # PASO 5: Matricular cada estudiante ADA solo en grupos A
    matriculas_creadas = 0
    
    print(f"\n3. Matriculando estudiantes en grupos A...")
    for estudiante in estudiantes_ada:
        print(f"\nMatriculando: {estudiante.user.get_full_name()} ({estudiante.student_code})")
        
        for course_group in course_groups_a:
            enrollment, created = Enrollment.objects.get_or_create(
                student=estudiante,
                course_group=course_group,
                academic_period=periodo,
                defaults={
                    'enrollment_date': '2024-03-01',
                    'enrollment_type': 'regular',
                    'status': 'active'
                }
            )
            
            if created:
                matriculas_creadas += 1
                print(f"  ✓ Matriculado en {course_group.course.name} - Grupo {course_group.group_code}")
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Matrículas eliminadas: {matriculas_eliminadas[0]}")
    print(f"Matrículas nuevas creadas: {matriculas_creadas}")
    print(f"Cursos únicos: {len(cursos_encontrados)}")
    print(f"Solo grupos A: {course_groups_a.count()}")
    
    # Verificar resultado final
    print(f"\n=== VERIFICACIÓN FINAL ===")
    for course_group in course_groups_a:
        count = Enrollment.objects.filter(
            course_group=course_group,
            academic_period=periodo
        ).count()
        print(f"{course_group.course.name} - Grupo {course_group.group_code}: {count} estudiantes")

if __name__ == "__main__":
    matricular_ada_solo_grupo_a()