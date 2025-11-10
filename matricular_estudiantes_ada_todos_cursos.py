#!/usr/bin/env python
"""
Script para matricular a todos los estudiantes ADA en todos los cursos existentes
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import Student, CourseGroup, Enrollment, AcademicPeriod

def matricular_estudiantes_ada():
    """Matricula a todos los estudiantes ADA en todos los cursos"""
    
    print("=== MATRICULANDO ESTUDIANTES ADA EN TODOS LOS CURSOS ===")
    
    # Obtener todos los estudiantes ADA (asumiendo que tienen códigos que empiezan con ciertos números)
    estudiantes_ada = Student.objects.filter(
        student_code__regex=r'^[0-9]+'  # Códigos que empiezan con números
    )
    
    print(f"Estudiantes ADA encontrados: {estudiantes_ada.count()}")
    
    # Obtener todos los grupos de curso
    course_groups = CourseGroup.objects.all()
    print(f"Grupos de curso encontrados: {course_groups.count()}")
    
    # Obtener el período académico activo
    periodo = AcademicPeriod.objects.filter(is_active=True).first()
    if not periodo:
        periodo = AcademicPeriod.objects.first()
    
    if not periodo:
        print("Error: No hay períodos académicos disponibles")
        return
    
    print(f"Usando período académico: {periodo.name}")
    
    # Matricular cada estudiante en cada grupo de curso
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
    print(f"Total de matrículas: {Enrollment.objects.count()}")
    
    # Verificar matrículas por curso
    print(f"\n=== MATRÍCULAS POR CURSO ===")
    for course_group in course_groups:
        count = Enrollment.objects.filter(
            course_group=course_group,
            academic_period=periodo
        ).count()
        print(f"{course_group.course.name} - Grupo {course_group.group_code}: {count} estudiantes")

if __name__ == "__main__":
    matricular_estudiantes_ada()