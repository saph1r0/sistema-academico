#!/usr/bin/env python
"""
Script simple para probar la conexión a la base de datos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Conexión a PostgreSQL exitosa")
            return True
    except Exception as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        return False

def test_user_table():
    """Prueba la tabla de usuarios"""
    try:
        with connection.cursor() as cursor:
            # Verificar si la tabla users existe
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            if columns:
                print("✅ Tabla 'users' encontrada con columnas:")
                for col_name, col_type in columns:
                    print(f"   - {col_name}: {col_type}")
            else:
                print("❌ Tabla 'users' no encontrada")
            
            return len(columns) > 0
    except Exception as e:
        print(f"❌ Error al verificar tabla users: {e}")
        return False

def create_simple_user():
    """Intenta crear un usuario simple usando SQL directo"""
    try:
        with connection.cursor() as cursor:
            # Verificar si ya existe un usuario admin
            cursor.execute("SELECT COUNT(*) FROM users WHERE institutional_email = 'admin@unsa.edu.pe'")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Crear usuario admin simple
                cursor.execute("""
                    INSERT INTO users (id, institutional_email, first_name, last_name, role, is_active, date_joined)
                    VALUES (gen_random_uuid(), 'admin@unsa.edu.pe', 'Administrador', 'Sistema', 'admin', true, NOW())
                """)
                print("✅ Usuario admin creado con SQL directo")
            else:
                print("ℹ️ Usuario admin ya existe")
            
            return True
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return False

def main():
    print("🔍 Probando Sistema Académico UNSA")
    print("=" * 40)
    
    # Probar conexión
    if not test_database_connection():
        print("\n❌ No se puede continuar sin conexión a la base de datos")
        return False
    
    # Probar tabla users
    if not test_user_table():
        print("\n❌ Problema con la tabla users")
        return False
    
    # Crear usuario simple
    if not create_simple_user():
        print("\n❌ Error al crear usuario")
        return False
    
    print("\n✅ ¡Pruebas básicas completadas!")
    print("\n📋 Credenciales de prueba:")
    print("- Administrador: admin@unsa.edu.pe")
    print("\n🚀 Para iniciar el servidor ejecuta:")
    print("poetry run python manage.py runserver")
    
    return True

if __name__ == '__main__':
    main()