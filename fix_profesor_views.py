#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para arreglar las vistas del profesor y crear usuarios de prueba
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import User, Teacher, CourseGroup

def main():
    """Crea usuarios de prueba y arregla las vistas"""
    print("=" * 80)
    print("ARREGLANDO SISTEMA DE PROFESORES")
    print("=" * 80)
    
    try:
        # 1. Crear profesor de prueba
        email_profesor = "profesor@unsa.edu.pe"
        profesor_creado = False
        
        if not User.objects.filter(institutional_email=email_profesor).exists():
            # Crear usuario profesor
            user_profesor = User.objects.create(
                institutional_email=email_profesor,
                first_name="Juan",
                last_name="Pérez García",
                role='teacher',
                is_active=True
            )
            user_profesor.set_password("juan123")
            user_profesor.save()
            
            # Crear registro de profesor
            teacher = Teacher.objects.create(
                user=user_profesor,
                teacher_code="PROF001",
                department="Ingeniería de Sistemas",
                specialty="Programación",
                hours_per_week=20
            )
            
            print(f"✓ Profesor creado: {email_profesor} (contraseña: juan123)")
            profesor_creado = True
        else:
            print(f"Profesor ya existe: {email_profesor}")
        
        # 2. Crear secretaria de prueba
        email_secretaria = "secretaria@unsa.edu.pe"
        if not User.objects.filter(institutional_email=email_secretaria).exists():
            user_secretaria = User.objects.create(
                institutional_email=email_secretaria,
                first_name="María",
                last_name="González López",
                role='secretary',
                is_active=True
            )
            user_secretaria.set_password("maria123")
            user_secretaria.save()
            
            print(f"✓ Secretaria creada: {email_secretaria} (contraseña: maria123)")
        else:
            print(f"Secretaria ya existe: {email_secretaria}")
        
        # 3. Asignar profesor a cursos
        teacher = Teacher.objects.filter(user__institutional_email=email_profesor).first()
        if teacher:
            # Obtener cursos sin profesor asignado
            course_groups = CourseGroup.objects.filter(teacher__isnull=True)
            asignaciones = 0
            
            for course_group in course_groups:
                course_group.teacher = teacher
                course_group.save()
                print(f"✓ Asignado a: {course_group.course.name} - Grupo {course_group.group_code}")
                asignaciones += 1
            
            if asignaciones > 0:
                print(f"\nTotal asignaciones: {asignaciones}")
            else:
                print("Todos los cursos ya tienen profesor asignado")
        
        # 4. Mostrar resumen
        total_teachers = Teacher.objects.count()
        total_course_groups = CourseGroup.objects.count()
        assigned_groups = CourseGroup.objects.filter(teacher__isnull=False).count()
        
        print(f"\n" + "=" * 80)
        print("RESUMEN DEL SISTEMA:")
        print("=" * 80)
        print(f"Profesores en sistema: {total_teachers}")
        print(f"Grupos de cursos: {total_course_groups}")
        print(f"Grupos asignados: {assigned_groups}")
        print(f"Grupos sin asignar: {total_course_groups - assigned_groups}")
        
        print(f"\n" + "=" * 80)
        print("INSTRUCCIONES PARA PROBAR:")
        print("=" * 80)
        print("1. Inicia el servidor: python manage.py runserver")
        print("2. Ve a: http://127.0.0.1:8000/")
        print("3. Prueba con estos usuarios:")
        print(f"   - Profesor: {email_profesor} / juan123")
        print(f"   - Secretaria: {email_secretaria} / maria123")
        print("   - Estudiante: jhuertas@unsa.edu.pe / (usar contraseña del sistema)")
        print("\n4. El profesor debería ver sus cursos asignados")
        print("5. El estudiante debería ver sus cursos matriculados")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()