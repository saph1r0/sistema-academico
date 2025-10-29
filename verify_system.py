#!/usr/bin/env python
"""
Script de verificación completa del sistema
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.contrib.auth import authenticate
from repositorio.postgres_repository.models import User, Student, Teacher
from presentacion.permisos import get_user_role, is_admin, is_student, is_teacher, is_secretary

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("🔍 Probando conexión a PostgreSQL...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Conexión exitosa - PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_user_model():
    """Prueba el modelo de usuario"""
    print("\n🔍 Probando modelo de usuario...")
    try:
        # Contar usuarios
        user_count = User.objects.count()
        print(f"✅ Usuarios en la base de datos: {user_count}")
        
        # Verificar usuarios específicos
        test_users = [
            'admin@unsa.edu.pe',
            'sesteba@unsa.edu.pe', 
            'jperez@unsa.edu.pe',
            'mgarcia@unsa.edu.pe'
        ]
        
        for email in test_users:
            try:
                user = User.objects.get(institutional_email=email)
                print(f"✅ Usuario encontrado: {email} - Rol: {user.role}")
            except User.DoesNotExist:
                print(f"⚠️ Usuario no encontrado: {email}")
        
        return True
    except Exception as e:
        print(f"❌ Error en modelo de usuario: {e}")
        return False

def test_authentication():
    """Prueba el sistema de autenticación"""
    print("\n🔍 Probando autenticación...")
    
    test_credentials = [
        ('admin@unsa.edu.pe', 'admin123', 'admin'),
        ('sesteba@unsa.edu.pe', '20241234', 'student'),
        ('jperez@unsa.edu.pe', 'profesor123', 'teacher'),
        ('mgarcia@unsa.edu.pe', 'secretario123', 'secretary')
    ]
    
    success_count = 0
    for email, password, expected_role in test_credentials:
        try:
            user = authenticate(username=email, password=password)
            if user:
                print(f"✅ Autenticación exitosa: {email} - Rol: {user.role}")
                if user.role == expected_role:
                    print(f"   ✅ Rol correcto: {expected_role}")
                else:
                    print(f"   ⚠️ Rol esperado: {expected_role}, obtenido: {user.role}")
                success_count += 1
            else:
                print(f"❌ Autenticación fallida: {email}")
        except Exception as e:
            print(f"❌ Error autenticando {email}: {e}")
    
    print(f"\n📊 Autenticaciones exitosas: {success_count}/{len(test_credentials)}")
    return success_count == len(test_credentials)

def test_permissions():
    """Prueba el sistema de permisos"""
    print("\n🔍 Probando sistema de permisos...")
    
    try:
        # Obtener usuarios de prueba
        admin_user = User.objects.get(institutional_email='admin@unsa.edu.pe')
        student_user = User.objects.get(institutional_email='sesteba@unsa.edu.pe')
        teacher_user = User.objects.get(institutional_email='jperez@unsa.edu.pe')
        secretary_user = User.objects.get(institutional_email='mgarcia@unsa.edu.pe')
        
        # Probar funciones de rol
        tests = [
            (admin_user, 'admin', is_admin),
            (student_user, 'student', is_student),
            (teacher_user, 'teacher', is_teacher),
            (secretary_user, 'secretary', is_secretary)
        ]
        
        success_count = 0
        for user, expected_role, role_func in tests:
            user_role = get_user_role(user)
            role_check = role_func(user)
            
            if user_role == expected_role and role_check:
                print(f"✅ Permisos correctos para {user.institutional_email}: {expected_role}")
                success_count += 1
            else:
                print(f"❌ Error en permisos para {user.institutional_email}")
                print(f"   Rol obtenido: {user_role}, esperado: {expected_role}")
                print(f"   Función de rol: {role_check}")
        
        print(f"\n📊 Pruebas de permisos exitosas: {success_count}/{len(tests)}")
        return success_count == len(tests)
        
    except Exception as e:
        print(f"❌ Error en sistema de permisos: {e}")
        return False

def test_profiles():
    """Prueba los perfiles de estudiante y profesor"""
    print("\n🔍 Probando perfiles de usuario...")
    
    try:
        # Verificar perfil de estudiante
        try:
            student_user = User.objects.get(institutional_email='sesteba@unsa.edu.pe')
            student_profile = Student.objects.get(user=student_user)
            print(f"✅ Perfil de estudiante: {student_profile.student_code}")
        except Student.DoesNotExist:
            print("⚠️ Perfil de estudiante no encontrado")
        
        # Verificar perfil de profesor
        try:
            teacher_user = User.objects.get(institutional_email='jperez@unsa.edu.pe')
            teacher_profile = Teacher.objects.get(user=teacher_user)
            print(f"✅ Perfil de profesor: {teacher_profile.teacher_code}")
        except Teacher.DoesNotExist:
            print("⚠️ Perfil de profesor no encontrado")
        
        return True
    except Exception as e:
        print(f"❌ Error en perfiles: {e}")
        return False

def main():
    print("🚀 VERIFICACIÓN COMPLETA DEL SISTEMA")
    print("=" * 50)
    
    tests = [
        ("Conexión a Base de Datos", test_database_connection),
        ("Modelo de Usuario", test_user_model),
        ("Sistema de Autenticación", test_authentication),
        ("Sistema de Permisos", test_permissions),
        ("Perfiles de Usuario", test_profiles)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed_tests += 1
        else:
            print(f"❌ Falló: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN: {passed_tests}/{total_tests} pruebas exitosas")
    
    if passed_tests == total_tests:
        print("✅ ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("\n🚀 Para iniciar el servidor ejecuta:")
        print("python manage.py runserver")
        print("\n🌐 Luego accede a: http://127.0.0.1:8000")
        print("\n📋 Credenciales de prueba:")
        print("- Administrador: admin@unsa.edu.pe / admin123")
        print("- Estudiante: sesteba@unsa.edu.pe / 20241234")
        print("- Profesor: jperez@unsa.edu.pe / profesor123")
        print("- Secretario: mgarcia@unsa.edu.pe / secretario123")
    else:
        print("❌ SISTEMA CON PROBLEMAS")
        print("Revisa los errores anteriores y ejecuta setup_complete.py")
    
    print("=" * 50)

if __name__ == '__main__':
    main()