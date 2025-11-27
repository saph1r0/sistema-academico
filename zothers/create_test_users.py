#!/usr/bin/env python
"""
Script para crear usuarios de prueba en el sistema
Ejecutar después de activar el entorno virtual y hacer las migraciones
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import User, Student, Teacher

def create_test_users():
    """Crea usuarios de prueba para el sistema"""
    
    print("Creando usuarios de prueba...")
    
    # Crear administrador
    admin_user, created = User.objects.get_or_create(
        institutional_email='admin@unsa.edu.pe',
        defaults={
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'role': 'admin',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
    if created:
        print("✅ Administrador creado: admin@unsa.edu.pe / admin123")
    else:
        print("ℹ️  Administrador ya existe: admin@unsa.edu.pe")
    
    # Crear estudiante de prueba
    student_user, created = User.objects.get_or_create(
        institutional_email='sesteba@unsa.edu.pe',
        defaults={
            'first_name': 'Sebastian',
            'last_name': 'Esteba',
            'role': 'student',
            'is_active': True,
        }
    )
    if created:
        student_user.set_password('20241234')  # CUI de ejemplo
        student_user.save()
        print("✅ Estudiante creado: sesteba@unsa.edu.pe / 20241234")
        
        # Crear perfil de estudiante
        Student.objects.get_or_create(
            user=student_user,
            defaults={
                'student_code': '20241234',
                'career': 'Ingeniería de Sistemas',
                'current_cycle': 5,
                'academic_status': 'active'
            }
        )
        print("✅ Perfil de estudiante creado")
    else:
        print("ℹ️  Estudiante ya existe: sesteba@unsa.edu.pe")
    
    # Crear profesor de prueba
    teacher_user, created = User.objects.get_or_create(
        institutional_email='jperez@unsa.edu.pe',
        defaults={
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'role': 'teacher',
            'is_active': True,
        }
    )
    if created:
        teacher_user.set_password('profesor123')
        teacher_user.save()
        print("✅ Profesor creado: jperez@unsa.edu.pe / profesor123")
        
        # Crear perfil de profesor
        Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={
                'teacher_code': 'DOC001',
                'department': 'Ingeniería de Sistemas',
                'specialty': 'Programación',
                'hours_per_week': 20
            }
        )
        print("✅ Perfil de profesor creado")
    else:
        print("ℹ️  Profesor ya existe: jperez@unsa.edu.pe")
    
    # Crear secretario de prueba
    secretary_user, created = User.objects.get_or_create(
        institutional_email='mgarcia@unsa.edu.pe',
        defaults={
            'first_name': 'María',
            'last_name': 'García',
            'role': 'secretary',
            'is_active': True,
        }
    )
    if created:
        secretary_user.set_password('secretario123')
        secretary_user.save()
        print("✅ Secretario creado: mgarcia@unsa.edu.pe / secretario123")
    else:
        print("ℹ️  Secretario ya existe: mgarcia@unsa.edu.pe")
    
    print("\n🎉 Usuarios de prueba creados exitosamente!")
    print("\nCredenciales de acceso:")
    print("👤 Administrador: admin@unsa.edu.pe / admin123")
    print("🎓 Estudiante: sesteba@unsa.edu.pe / 20241234")
    print("👨‍🏫 Profesor: jperez@unsa.edu.pe / profesor123")
    print("📋 Secretario: mgarcia@unsa.edu.pe / secretario123")

if __name__ == '__main__':
    try:
        create_test_users()
    except Exception as e:
        print(f"❌ Error al crear usuarios: {e}")
        sys.exit(1)