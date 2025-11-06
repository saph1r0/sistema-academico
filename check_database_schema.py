#!/usr/bin/env python3
"""
Script para verificar el esquema de la base de datos
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection


def check_users_table():
    """Verifica la estructura de la tabla users"""
    print("=== Estructura de la tabla 'users' ===\n")
    
    try:
        with connection.cursor() as cursor:
            # Obtener información de las columnas
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            print("Columnas de la tabla 'users':")
            print("-" * 60)
            for col in columns:
                column_name, data_type, is_nullable, column_default = col
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default = f"DEFAULT {column_default}" if column_default else ""
                print(f"{column_name:<20} {data_type:<15} {nullable:<10} {default}")
            
            print(f"\nTotal de columnas: {len(columns)}")
            
    except Exception as e:
        print(f"Error verificando tabla users: {str(e)}")


def check_existing_test_user():
    """Verifica si existe un usuario de prueba"""
    print("\n=== Verificando usuarios existentes ===\n")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, institutional_email, first_name, last_name, role
                FROM users 
                WHERE institutional_email LIKE '%test%' OR first_name LIKE '%Test%'
                LIMIT 5;
            """)
            
            users = cursor.fetchall()
            
            if users:
                print("Usuarios de prueba encontrados:")
                for user in users:
                    print(f"  - {user[1]} ({user[2]} {user[3]}) - {user[4]}")
            else:
                print("No se encontraron usuarios de prueba")
                
    except Exception as e:
        print(f"Error verificando usuarios: {str(e)}")


if __name__ == "__main__":
    check_users_table()
    check_existing_test_user()