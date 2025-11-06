#!/usr/bin/env python3
"""
Script para arreglar el problema de migraciones pendientes
"""
import os
import django
from django.core.management import execute_from_command_line
from django.db import connection

def fix_migration_issue():
    """Arregla el problema de migraciones pendientes"""
    
    print("🔧 Arreglando problema de migraciones...")
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    try:
        # Verificar si la tabla course_topic_contents ya existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'course_topic_contents'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
        if table_exists:
            print("✅ La tabla 'course_topic_contents' ya existe")
            print("🔧 Marcando migración como aplicada...")
            
            # Marcar la migración como aplicada sin ejecutarla
            execute_from_command_line([
                'manage.py', 'migrate', 'postgres_repository', '0011', '--fake'
            ])
            
            print("✅ Migración marcada como aplicada")
        else:
            print("📝 La tabla no existe, aplicando migración normalmente...")
            execute_from_command_line(['manage.py', 'migrate'])
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_migration_issue()
    
    if success:
        print("\n✅ ¡Problema de migraciones solucionado!")
        print("🚀 Ahora puedes usar el sistema sin problemas")
    else:
        print("\n❌ No se pudo solucionar el problema")