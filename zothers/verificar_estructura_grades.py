#!/usr/bin/env python3
"""
Script para verificar la estructura completa del sistema de notas
"""
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verificar_estructura_completa():
    """Verifica la estructura completa del sistema de notas"""
    
    tablas_adicionales = ['course_groups', 'enrollments', 'academic_periods']
    
    try:
        with connection.cursor() as cursor:
            print("🔍 Verificando tablas adicionales del sistema de notas")
            print("=" * 60)
            
            for tabla in tablas_adicionales:
                print(f"\n📋 Verificando tabla: {tabla}")
                print("-" * 40)
                
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
            
            # Verificar relaciones entre tablas
            print(f"\n🔗 Verificando relaciones entre tablas")
            print("=" * 50)
            
            # Ver qué course_group_id existe en evaluation_types
            cursor.execute("SELECT DISTINCT course_group_id FROM evaluation_types;")
            course_groups = cursor.fetchall()
            print(f"📋 course_group_id en evaluation_types: {len(course_groups)} únicos")
            for cg in course_groups:
                print(f"  - {cg[0]}")
                        
    except Exception as e:
        print(f"❌ Error al verificar estructura: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_estructura_completa()