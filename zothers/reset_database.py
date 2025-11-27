#!/usr/bin/env python
"""
Script para resetear completamente la base de datos
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def drop_and_create_database():
    """Elimina y recrea la base de datos"""
    print("🗑️ Eliminando y recreando la base de datos...")
    
    try:
        # Conectar a PostgreSQL (a la base de datos por defecto)
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password='131070',
            database='postgres'  # Conectar a la BD por defecto
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Terminar todas las conexiones a la base de datos
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'modelsistak' AND pid <> pg_backend_pid()
        """)
        
        # Eliminar la base de datos si existe
        cursor.execute("DROP DATABASE IF EXISTS modelsistak")
        print("✅ Base de datos eliminada")
        
        # Crear la base de datos nuevamente
        cursor.execute("CREATE DATABASE modelsistak")
        print("✅ Base de datos creada")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al resetear la base de datos: {e}")
        return False

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
    print("🚀 RESETEO COMPLETO DE LA BASE DE DATOS")
    print("=" * 50)
    
    # Resetear la base de datos
    if not drop_and_create_database():
        print("\n❌ Error al resetear la base de datos")
        return False
    
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
    print("✅ ¡BASE DE DATOS RESETEADA Y CONFIGURADA!")
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