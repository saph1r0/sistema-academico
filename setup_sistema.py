#!/usr/bin/env python
"""
Script de configuración inicial del sistema académico
Ejecutar después de activar el entorno virtual
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"Salida del error: {e.stderr}")
        return False

def setup_database():
    """Configura la base de datos"""
    print("\n📊 Configurando base de datos...")
    
    # Hacer migraciones
    if not run_command("python manage.py makemigrations", "Creando migraciones"):
        return False
    
    if not run_command("python manage.py migrate", "Aplicando migraciones"):
        return False
    
    return True

def create_users():
    """Crea usuarios de prueba"""
    print("\n👥 Creando usuarios de prueba...")
    
    if not run_command("python create_test_users.py", "Creando usuarios de prueba"):
        return False
    
    return True

def main():
    """Función principal de configuración"""
    print("🚀 Configuración inicial del Sistema Académico UNSA")
    print("=" * 50)
    
    # Verificar que Django esté disponible
    try:
        import django
        print(f"✅ Django {django.get_version()} detectado")
    except ImportError:
        print("❌ Django no está instalado. Activa el entorno virtual primero.")
        sys.exit(1)
    
    # Configurar base de datos
    if not setup_database():
        print("❌ Error en la configuración de la base de datos")
        sys.exit(1)
    
    # Crear usuarios de prueba
    if not create_users():
        print("❌ Error al crear usuarios de prueba")
        sys.exit(1)
    
    print("\n🎉 ¡Configuración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar: python manage.py runserver")
    print("2. Abrir: http://127.0.0.1:8000")
    print("3. Usar las credenciales de prueba para acceder")
    print("\n👤 Credenciales de acceso:")
    print("   Administrador: admin@unsa.edu.pe / admin123")
    print("   Estudiante: sesteba@unsa.edu.pe / 20241234")
    print("   Profesor: jperez@unsa.edu.pe / profesor123")
    print("   Secretario: mgarcia@unsa.edu.pe / secretario123")

if __name__ == '__main__':
    main()