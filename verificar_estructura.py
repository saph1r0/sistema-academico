#!/usr/bin/env python3
"""
Script para verificar la estructura de todas las tablas relevantes
"""
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verificar_estructura():
    """Verifica la estructura de las tablas relevantes"""
    
    tablas = ['students', 'courses', 'grades', 'evaluation_types', 'users', 'teachers']
    
    try:
        with connection.cursor() as cursor:
            for tabla in tablas:
                print(f"\n🔍 Verificando tabla: {tabla}")
                print("=" * 50)
                
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = %s;
                """, [tabla])
                
                if cursor.fetchone()[0] == 0:
                    print(f"❌ La tabla {tabla} no existe")
                    continue
                
                # Mostrar estructura de la tabla
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position;
                """, [tabla])
                
                columns = cursor.fetchall()
                print(f"📋 Estructura de {tabla}:")
                for col in columns:
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                    print(f"  - {col[0]}: {col[1]} ({nullable}){default}")
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {tabla};")
                count = cursor.fetchone()[0]
                print(f"📊 Registros: {count}")
                
                # Mostrar algunos registros si existen
                if count > 0 and count <= 5:
                    cursor.execute(f"SELECT * FROM {tabla} LIMIT 3;")
                    rows = cursor.fetchall()
                    print("📄 Primeros registros:")
                    for row in rows:
                        print(f"  {row}")
                        
    except Exception as e:
        print(f"❌ Error al verificar estructura: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_estructura()