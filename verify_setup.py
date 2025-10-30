#!/usr/bin/env python
"""
Script para verificar que la configuración esté funcionando correctamente
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import User, Student
from presentacion.permisos import get_user_role, is_admin, is_student

def main():
    """Verificar la configuración"""
    
    print("=== Verificación del Sistema ===")
    
    # 1. Verificar conexión a la base de datos
    print("\n1. Verificando conexión a la base de datos...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Conexión a PostgreSQL exitosa")
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        return False
    
    # 2. Verificar modelos
    print("\n2. Verificando modelos...")
    try:
        user_count = User.objects.count()
        student_count = Student.objects.count()
        print(f"✓ Usuarios en la base de datos: {user_count}")
        print(f"✓ Estudiantes en la base de datos: {student_count}")
    except Exception as e:
        print(f"✗ Error al consultar modelos: {e}")
        return False
    
    # 3. Verificar sistema de permisos
    print("\n3. Verificando sistema de permisos...")
    try:
        # Buscar un usuario administrador
        admin_user = User.objects.filter(role='admin').first()
        if admin_user:
            role = get_user_role(admin_user)
            is_admin_check = is_admin(admin_user)
            print(f"✓ Usuario admin encontrado: {admin_user.institutional_email}")
            print(f"✓ Rol detectado: {role}")
            print(f"✓ Verificación is_admin: {is_admin_check}")
        else:
            print("⚠ No se encontró usuario administrador")
        
        # Buscar un estudiante
        student_user = User.objects.filter(role='student').first()
        if student_user:
            role = get_user_role(student_user)
            is_student_check = is_student(student_user)
            print(f"✓ Usuario estudiante encontrado: {student_user.institutional_email}")
            print(f"✓ Rol detectado: {role}")
            print(f"✓ Verificación is_student: {is_student_check}")
        else:
            print("⚠ No se encontró usuario estudiante")
            
    except Exception as e:
        print(f"✗ Error en sistema de permisos: {e}")
        return False
    
    # 4. Verificar URLs
    print("\n4. Verificando configuración de URLs...")
    try:
        from django.urls import reverse
        
        # Verificar URLs principales
        urls_to_check = [
            'login:login',
            'administrador:dashboard',
            'estudiante:dashboard',
            'profesor:dashboard',
            'secretario:dashboard'
        ]
        
        for url_name in urls_to_check:
            try:
                url = reverse(url_name)
                print(f"✓ URL {url_name}: {url}")
            except Exception as e:
                print(f"✗ Error en URL {url_name}: {e}")
                
    except Exception as e:
        print(f"✗ Error al verificar URLs: {e}")
    
    print("\n=== Verificación Completada ===")
    print("\nSi todo está correcto, puedes:")
    print("1. Ejecutar: python manage.py runserver")
    print("2. Ir a: http://127.0.0.1:8000/login/")
    print("3. Probar login con admin@unsa.edu.pe / admin123")
    
    return True

if __name__ == '__main__':
    main()