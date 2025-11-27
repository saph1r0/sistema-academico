#!/usr/bin/env python
"""
Script para verificar la estructura de la tabla teacher_attendance
"""

import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def check_table_structure():
    """Verifica la estructura de la tabla teacher_attendance"""
    
    print("🔍 Verificando estructura de la tabla teacher_attendance...\n")
    
    with connection.cursor() as cursor:
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'teacher_attendance'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ La tabla teacher_attendance no existe")
            return False
        
        print("✅ La tabla teacher_attendance existe")
        
        # Obtener estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'teacher_attendance'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print("\n📋 Estructura de la tabla:")
        print("Columna | Tipo | Nullable")
        print("-" * 40)
        
        for column_name, data_type, is_nullable in columns:
            print(f"{column_name:<20} | {data_type:<15} | {is_nullable}")
        
        # Verificar columnas específicas que necesitamos
        required_columns = ['login_time', 'logout_time', 'teacher_id', 'course_group_id']
        existing_columns = [col[0] for col in columns]
        
        print(f"\n🔍 Verificando columnas requeridas:")
        for col in required_columns:
            if col in existing_columns:
                print(f"✅ {col} - Existe")
            else:
                print(f"❌ {col} - No existe")
        
        return True


def check_data():
    """Verifica si hay datos en la tabla"""
    
    print("\n📊 Verificando datos en teacher_attendance...")
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM teacher_attendance;")
        count = cursor.fetchone()[0]
        
        print(f"Total de registros: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT teacher_id, login_time, logout_time 
                FROM teacher_attendance 
                ORDER BY login_time DESC 
                LIMIT 5;
            """)
            
            records = cursor.fetchall()
            print("\nÚltimos 5 registros:")
            for record in records:
                print(f"  Teacher: {record[0]}, Login: {record[1]}, Logout: {record[2]}")


def create_sample_data():
    """Crea datos de ejemplo para testing"""
    
    print("\n🔧 Creando datos de ejemplo...")
    
    from repositorio.postgres_repository.models import Teacher, TeacherAttendance
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtener un profesor
    teacher = Teacher.objects.first()
    
    if not teacher:
        print("❌ No hay profesores en el sistema")
        return
    
    print(f"Creando datos para: {teacher.user.get_full_name()}")
    
    # Crear algunos registros de asistencia
    now = timezone.now()
    
    for i in range(5):
        login_time = now - timedelta(days=i, hours=2)
        logout_time = login_time + timedelta(hours=3)
        
        attendance, created = TeacherAttendance.objects.get_or_create(
            teacher=teacher,
            login_time=login_time,
            defaults={
                'logout_time': logout_time,
                'ip_address': '192.168.1.100',
                'access_type': 'presential',
                'user_agent': 'Test Browser'
            }
        )
        
        if created:
            print(f"✅ Creado registro para {login_time.date()}")
        else:
            print(f"ℹ️  Ya existe registro para {login_time.date()}")


if __name__ == "__main__":
    try:
        if check_table_structure():
            check_data()
            
            # Preguntar si crear datos de ejemplo
            response = input("\n¿Crear datos de ejemplo? (y/n): ")
            if response.lower() == 'y':
                create_sample_data()
        
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        import traceback
        traceback.print_exc()