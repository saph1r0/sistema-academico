#!/usr/bin/env python
"""
Script completo de configuración del sistema
"""

import os
import sys
import subprocess
import django

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        if result.stdout:
            print(f"   Salida: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}")
        if e.stdout:
            print(f"   Salida: {e.stdout.strip()}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def setup_django():
    """Configura Django y ejecuta migraciones"""
    print("🚀 Configurando Django...")
    
    # Crear migraciones
    if not run_command("python manage.py makemigrations postgres_repository", "Creando migraciones"):
        return False
    
    # Aplicar migraciones
    if not run_command("python manage.py migrate", "Aplicando migraciones"):
        return False
    
    return True

def create_users():
    """Crea usuarios de prueba usando Django"""
    print("\n👥 Creando usuarios de prueba...")
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from repositorio.postgres_repository.models import User, Student, Teacher
    
    try:
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
            print("✅ Usuario administrador creado")
        else:
            print("ℹ️ Usuario administrador ya existe")

        # Crear estudiante
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
            student_user.set_password('20241234')
            student_user.save()
            print("✅ Usuario estudiante creado")
            
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
        else:
            print("ℹ️ Usuario estudiante ya existe")

        # Crear profesor
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
            print("✅ Usuario profesor creado")
            
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
        else:
            print("ℹ️ Usuario profesor ya existe")

        # Crear secretario
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
            print("✅ Usuario secretario creado")
        else:
            print("ℹ️ Usuario secretario ya existe")

        return True
    except Exception as e:
        print(f"❌ Error al crear usuarios: {e}")
        return False

def main():
    print("🚀 Sistema Académico UNSA - Configuración Completa")
    print("=" * 50)
    
    # Configurar Django
    if not setup_django():
        print("\n❌ Error en la configuración de Django")
        return False
    
    # Crear usuarios
    if not create_users():
        print("\n❌ Error al crear usuarios")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
    print("=" * 50)
    print("\n📋 Credenciales de prueba:")
    print("- Administrador: admin@unsa.edu.pe / admin123")
    print("- Estudiante: sesteba@unsa.edu.pe / 20241234")
    print("- Profesor: jperez@unsa.edu.pe / profesor123")
    print("- Secretario: mgarcia@unsa.edu.pe / secretario123")
    print("\n🚀 Para iniciar el servidor ejecuta:")
    print("python manage.py runserver")
    print("\n🌐 Luego accede a: http://127.0.0.1:8000")
    
    return True

if __name__ == '__main__':
    main()