#!/usr/bin/env python
"""
Script para agregar las columnas faltantes a la base de datos
"""
import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection

def main():
    try:
        with connection.cursor() as cursor:
            print("🔧 Agregando columnas faltantes a la tabla users...")
            
            # Agregar is_staff si no existe
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN is_staff BOOLEAN DEFAULT FALSE;")
                print("✅ Columna is_staff agregada")
            except Exception as e:
                if "already exists" in str(e) or "ya existe" in str(e):
                    print("ℹ️  Columna is_staff ya existe")
                else:
                    print(f"❌ Error agregando is_staff: {e}")
            
            # Agregar is_superuser si no existe
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE;")
                print("✅ Columna is_superuser agregada")
            except Exception as e:
                if "already exists" in str(e) or "ya existe" in str(e):
                    print("ℹ️  Columna is_superuser ya existe")
                else:
                    print(f"❌ Error agregando is_superuser: {e}")
            
            # Verificar que las columnas existen
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('is_staff', 'is_superuser')
                ORDER BY column_name;
            """)
            
            columns = cursor.fetchall()
            print(f"\n📋 Columnas encontradas: {[col[0] for col in columns]}")
            
            if len(columns) == 2:
                print("✅ ¡Todas las columnas necesarias están presentes!")
            else:
                print("❌ Faltan columnas")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()