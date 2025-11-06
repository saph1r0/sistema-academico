#!/usr/bin/env python
"""
Script para:
1. Eliminar todas las matrículas existentes de estudiantes ADA
2. Matricular a estudiantes ADA solo en cursos específicos:
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

def limpiar_y_matricular_ada():
    """Limpia matrículas existentes y matricula solo en cursos específicos"""
    
    print("=== LIMPIANDO Y MATRICULANDO ESTUDIANTES ADA ===")
    
    # Obtener todos los estudiantes ADA
    estudiantes_ada = Student.objects.filter(
        student_code__regex=r'^[0-9]+'  # Códigos que empiezan con números
    )
    
    print(f"Estudiantes ADA encontrados: {estudiantes_ada.count()}")
    
    # PASO 1: Eliminar todas las matrículas existentes de estudiantes ADA
    print("\n1. Eliminando matrículas existentes de estudiantes ADA...")
    matriculas_eliminadas = Enrollment.objects.filter(student__in=estudiantes_ada).delete()
    print(f"   ✓ Eliminadas {matriculas_eliminadas[0]} matrículas existentes")
    
    # PASO 2: Matricular solo en cursos específicos
    print("\n2. Matriculando en cursos específicos...")
    
    # Cursos específicos donde matricular a los estudiantes ADA
    cursos_ada = [
        "MATEMÁTICA APLICADA A LA COMPUTACIÓN",
        "SISTEMAS OPERATIVOS", 
        "TRABAJO INTERDISCIPLINAR II",
        "INGENIERÍA DE SOFTWARE II",
        "ANÁLISIS Y DISEÑO DE ALGORITMOS"
    ]
    
    print(f"Cursos objetivo: {cursos_ada}")
    
    # Obtener el período académico activo
    periodo = AcademicPeriod.objects.filter(is_active=True).first()
    if not periodo:
        periodo = AcademicPeriod.objects.first()
    
    if not periodo:
        print("Error: No hay períodos académicos disponibles")
        return
    
    print(f"Usando período académico: {periodo.name}")
    
    # Buscar los cursos específicos usando diferentes estrategias
    cursos_encontrados = []
    
    # Estrategia 1: Buscar por palabras clave específicas
    palabras_clave = {
        "MATEMÁTICA APLICADA A LA COMPUTACIÓN": ["MATEMÁTICA", "APLICADA", "COMPUTACIÓN"],
        "SISTEMAS OPERATIVOS": ["SISTEMAS", "OPERATIVOS"],
        "TRABAJO INTERDISCIPLINAR II": ["TRABAJO", "INTERDISCIPLINAR", "II"],
        "INGENIERÍA DE SOFTWARE II": ["INGENIERÍA", "SOFTWARE", "II"],
        "ANÁLISIS Y DISEÑO DE ALGORITMOS": ["ANÁLISIS", "DISEÑO", "ALGORITMOS"]
    }
    
    for curso_nombre, palabras in palabras_clave.items():
        # Buscar cursos que contengan las palabras clave
        cursos = Course.objects.all()
        for palabra in palabras:
            cursos = cursos.filter(name__icontains=palabra)
        
        if cursos.exists():
            print(f"✓ Encontrado curso: {cursos.first().name} (buscando: {curso_nombre})")
            cursos_encontrados.extend(cursos)
        else:
            # Buscar con menos restricciones
            for palabra in palabras[:2]:  # Solo primeras 2 palabras
                cursos_alternativos = Course.objects.filter(name__icontains=palabra)
                if cursos_alternativos.exists():
                    print(f"? Posible curso: {cursos_alternativos.first().name} (buscando: {curso_nombre})")
                    cursos_encontrados.extend(cursos_alternativos[:1])  # Solo el primero
                    break
    
    if not cursos_encontrados:
        print("Error: No se encontraron los cursos específicos")
        print("Cursos disponibles en la base de datos:")
        for curso in Course.objects.all():
            print(f"  - {curso.name}")
        return
    
    # Eliminar duplicados
    cursos_encontrados = list(set(cursos_encontrados))
    print(f"\nCursos únicos encontrados para matrícula: {len(cursos_encontrados)}")
    for curso in cursos_encontrados:
        print(f"  - {curso.name}")
    
    # Obtener grupos de curso para los cursos encontrados
    course_groups = CourseGroup.objects.filter(
        course__in=cursos_encontrados,
        academic_period=periodo
    )
    
    print(f"\nGrupos de curso encontrados: {course_groups.count()}")
    
    # Matricular cada estudiante ADA en cada grupo de curso específico
    matriculas_creadas = 0
    
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
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Matrículas eliminadas: {matriculas_eliminadas[0]}")
    print(f"Matrículas nuevas creadas: {matriculas_creadas}")
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
    limpiar_y_matricular_ada()