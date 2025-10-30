#!/usr/bin/env python
"""
Script para limpiar las migraciones usando Django
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def clean_migrations():
    """Limpia las migraciones de la base de datos"""
    print("🧹 Limpiando migraciones de Django...")
    
    try:
        with connection.cursor() as cursor:
            # Eliminar migraciones de postgres_repository
            cursor.execute("DELETE FROM django_migrations WHERE app = 'postgres_repository'")
            deleted_count = cursor.rowcount
            print(f"✅ Eliminadas {deleted_count} migraciones de postgres_repository")
            
            # Mostrar migraciones restantes
            cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
            remaining = cursor.fetchall()
            print(f"ℹ️ Migraciones restantes: {len(remaining)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al limpiar migraciones: {e}")
        return False

def main():
    print("🚀 LIMPIEZA DE MIGRACIONES")
    print("=" * 30)
    
    if clean_migrations():
        print("\n✅ ¡Migraciones limpiadas exitosamente!")
        print("\nAhora puedes ejecutar:")
        print("poetry run python manage.py makemigrations postgres_repository")
        print("poetry run python manage.py migrate")
    else:
        print("\n❌ Error al limpiar migraciones")

if __name__ == '__main__':
    main()