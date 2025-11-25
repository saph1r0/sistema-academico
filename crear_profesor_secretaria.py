#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para crear usuarios profesor y secretaria para pruebas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import User, Teacher

def main():
    """Crea usuarios de prueba para profesor y secretaria"""
    print("=" * 80)
    print("CREANDO USUARIOS DE PRUEBA")
    print("=" * 80)
    
    try:
        # Crear profesor de prueba
        email_profesor = "profesor@unsa.edu.pe"
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
        else:
            print(f"Profesor ya existe: {email_profesor}")
        
        # Crear secretaria de prueba
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
        
        # Asignar profesor a cursos existentes
        from repositorio.postgres_repository.models import CourseGroup
        
        # Obtener el profesor creado
        teacher = Teacher.objects.filter(user__institutional_email=email_profesor).first()
        if teacher:
            # Asignar a todos los grupos de curso que no tengan profesor
            course_groups = CourseGroup.objects.filter(teacher__isnull=True)
            asignaciones = 0
            
            for course_group in course_groups:
                course_group.teacher = teacher
                course_group.save()
                print(f"✓ Asignado a: {course_group.course.name}")
                asignaciones += 1
            
            print(f"\nTotal asignaciones: {asignaciones}")
        
        print("\n" + "=" * 80)
        print("USUARIOS CREADOS EXITOSAMENTE")
        print("=" * 80)
        print("Para probar el sistema:")
        print("1. Inicia el servidor: python manage.py runserver")
        print("2. Ve a: http://127.0.0.1:8000/")
        print("3. Prueba con:")
        print(f"   - Profesor: {email_profesor} / juan123")
        print(f"   - Secretaria: {email_secretaria} / maria123")
        print("   - Estudiante: jhuertas@unsa.edu.pe / (contraseña del sistema)")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == '__main__':
    main()