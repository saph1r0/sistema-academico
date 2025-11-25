#!/usr/bin/env python
"""
Script para matricular a todos los estudiantes ADA solo en cursos específicos:
- MATEMÁTICA APLICADA A LA COMPUTACIÓN
- SISTEMAS OPERATIVOS
- TRABAJO INTERDISCIPLINAR II
- INGENIERÍA DE SOFTWARE II
- ANÁLISIS Y DISEÑO DE ALGORITMOS
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

def matricular_estudiantes_ada_cursos_especificos():
    """Matricula a todos los estudiantes ADA solo en los cursos específicos"""
    
    print("=== MATRICULANDO ESTUDIANTES ADA EN CURSOS ESPECÍFICOS ===")
    
    # Cursos específicos donde matricular a los estudiantes ADA
    cursos_ada = [
        "MATEMÁTICA APLICADA A LA COMPUTACIÓN",
        "SISTEMAS OPERATIVOS", 
        "TRABAJO INTERDISCIPLINAR II",
        "INGENIERÍA DE SOFTWARE II",
        "ANÁLISIS Y DISEÑO DE ALGORITMOS"
    ]
    
    print(f"Cursos objetivo: {cursos_ada}")
    
    # Obtener todos los estudiantes ADA
    estudiantes_ada = Student.objects.filter(
        student_code__regex=r'^[0-9]+'  # Códigos que empiezan con números
    )
    
    print(f"Estudiantes ADA encontrados: {estudiantes_ada.count()}")
    
    # Obtener el período académico activo
    periodo = AcademicPeriod.objects.filter(is_active=True).first()
    if not periodo:
        periodo = AcademicPeriod.objects.first()
    
    if not periodo:
        print("Error: No hay períodos académicos disponibles")
        return
    
    print(f"Usando período académico: {periodo.name}")
    
    # Buscar los cursos específicos (usando búsqueda parcial por si hay diferencias en los nombres)
    cursos_encontrados = []
    for curso_nombre in cursos_ada:
        # Buscar cursos que contengan el nombre (para manejar variaciones)
        cursos = Course.objects.filter(name__icontains=curso_nombre.split()[0])  # Buscar por primera palabra
        if not cursos.exists():
            # Intentar búsqueda más flexible
            palabras_clave = curso_nombre.split()[:2]  # Primeras 2 palabras
            for palabra in palabras_clave:
                cursos = Course.objects.filter(name__icontains=palabra)
                if cursos.exists():
                    break
        
        if cursos.exists():
            print(f"✓ Encontrado curso: {cursos.first().name} (buscando: {curso_nombre})")
            cursos_encontrados.extend(cursos)
        else:
            print(f"✗ No encontrado curso: {curso_nombre}")
    
    if not cursos_encontrados:
        print("Error: No se encontraron los cursos específicos")
        print("Cursos disponibles en la base de datos:")
        for curso in Course.objects.all()[:10]:
            print(f"  - {curso.name}")
        return
    
    print(f"\nCursos encontrados para matrícula: {len(cursos_encontrados)}")
    
    # Obtener grupos de curso para los cursos encontrados
    course_groups = CourseGroup.objects.filter(
        course__in=cursos_encontrados,
        academic_period=periodo
    )
    
    print(f"Grupos de curso encontrados: {course_groups.count()}")
    
    # Matricular cada estudiante ADA en cada grupo de curso específico
    matriculas_creadas = 0
    matriculas_existentes = 0
    
    for estudiante in estudiantes_ada:
        print(f"\nMatriculando estudiante: {estudiante.user.get_full_name()} ({estudiante.student_code})")
        
        for course_group in course_groups:
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
            else:
                matriculas_existentes += 1
    
    print(f"\n=== RESUMEN DE MATRÍCULAS ===")
    print(f"Matrículas nuevas creadas: {matriculas_creadas}")
    print(f"Matrículas que ya existían: {matriculas_existentes}")
    print(f"Total de matrículas en el sistema: {Enrollment.objects.count()}")
    
    # Verificar matrículas por curso específico
    print(f"\n=== MATRÍCULAS EN CURSOS ESPECÍFICOS ===")
    for course_group in course_groups:
        count = Enrollment.objects.filter(
            course_group=course_group,
            academic_period=periodo
        ).count()
        print(f"{course_group.course.name} - Grupo {course_group.group_code}: {count} estudiantes")

if __name__ == "__main__":
    matricular_estudiantes_ada_cursos_especificos()