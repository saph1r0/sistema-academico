#!/usr/bin/env python
"""
Script simple para resetear la base de datos usando Django
"""

import os
import sys
import subprocess

def run_command_with_poetry(command, description):
    """Ejecuta un comando usando poetry run"""
    print(f"\n🔄 {description}...")
    try:
        full_command = f"poetry run {command}"
        result = subprocess.run(full_command, shell=True, check=True, capture_output=True, text=True)
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

def main():
    print("🚀 CONFIGURACIÓN SIMPLE DE LA BASE DE DATOS")
    print("=" * 50)
    
    print("\n⚠️ IMPORTANTE: Asegúrate de que PostgreSQL esté ejecutándose")
    print("⚠️ Y que la base de datos 'modelsistak' exista")
    
    # Limpiar migraciones de Django
    print("\n🧹 Limpiando migraciones de Django...")
    if not run_command_with_poetry("python manage.py migrate --fake postgres_repository zero", "Limpiando migraciones de postgres_repository"):
        print("ℹ️ No hay migraciones previas para limpiar")
    
    # Crear migraciones
    if not run_command_with_poetry("python manage.py makemigrations postgres_repository", "Creando migraciones"):
        print("\n❌ Error al crear migraciones")
        return False
    
    # Aplicar migraciones
    if not run_command_with_poetry("python manage.py migrate", "Aplicando migraciones"):
        print("\n❌ Error al aplicar migraciones")
        return False
    
    # Crear usuarios de prueba
    if not run_command_with_poetry("python create_test_users.py", "Creando usuarios de prueba"):
        print("\n❌ Error al crear usuarios")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ¡BASE DE DATOS CONFIGURADA!")
    print("=" * 50)
    print("\n📋 Credenciales de prueba:")
    print("- Administrador: admin@unsa.edu.pe / admin123")
    print("- Estudiante: sesteba@unsa.edu.pe / 20241234")
    print("- Profesor: jperez@unsa.edu.pe / profesor123")
    print("- Secretario: mgarcia@unsa.edu.pe / secretario123")
    print("\n🚀 Para iniciar el servidor ejecuta:")
    print("poetry run python manage.py runserver")
    print("\n🌐 Luego accede a: http://127.0.0.1:8000")
    
    return True

if __name__ == '__main__':
    main()