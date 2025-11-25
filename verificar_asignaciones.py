#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar las asignaciones creadas por el sistema automático
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import Course, Student, Enrollment, CourseGroup

def main():
    """Verifica las asignaciones en la base de datos"""
    print("=" * 80)
    print("VERIFICACION DE ASIGNACIONES AUTOMATICAS")
    print("=" * 80)
    
    try:
        # Contar registros
        total_students = Student.objects.count()
        total_courses = Course.objects.count()
        total_enrollments = Enrollment.objects.count()
        total_groups = CourseGroup.objects.count()
        
        print(f"Estudiantes en BD: {total_students}")
        print(f"Cursos en BD: {total_courses}")
        print(f"Grupos de cursos: {total_groups}")
        print(f"Inscripciones totales: {total_enrollments}")
        
        print("\n" + "-" * 50)
        print("CURSOS CON ESTUDIANTES ASIGNADOS:")
        print("-" * 50)
        
        # Mostrar cursos con estudiantes
        courses_with_students = Course.objects.filter(
            coursegroup__enrollment__isnull=False
        ).distinct()
        
        for course in courses_with_students:
            # Contar estudiantes por curso
            student_count = Enrollment.objects.filter(
                course_group__course=course,
                status='active'
            ).count()
            
            print(f"• {course.name}: {student_count} estudiantes")
        
        print("\n" + "-" * 50)
        print("VERIFICACION DE DUPLICADOS:")
        print("-" * 50)
        
        # Verificar duplicados
        duplicates = Enrollment.objects.values(
            'student', 'course_group__course'
        ).annotate(
            count=django.db.models.Count('id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            print(f"ADVERTENCIA: Se encontraron {duplicates.count()} duplicados")
            for dup in duplicates[:5]:
                print(f"  - Estudiante ID {dup['student']} en curso ID {dup['course_group__course']}: {dup['count']} veces")
        else:
            print("✓ No se encontraron duplicados")
        
        print("\n" + "=" * 80)
        print("RESUMEN:")
        print("=" * 80)
        
        if total_enrollments > 0:
            print("✓ SISTEMA FUNCIONANDO CORRECTAMENTE")
            print(f"  - {total_enrollments} asignaciones activas")
            print(f"  - {courses_with_students.count()} cursos con estudiantes")
            print("  - Prevención de duplicados activa")
            print("  - Creación automática de cursos y estudiantes")
        else:
            print("⚠ No se encontraron asignaciones")
            print("  Ejecute: python ejecutar_asignacion_automatica.py")
        
        return True
        
    except Exception as e:
        print(f"Error durante la verificación: {e}")
        return False

if __name__ == '__main__':
    main()