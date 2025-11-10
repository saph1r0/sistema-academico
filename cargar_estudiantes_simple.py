#!/usr/bin/env python
"""
Script simple para cargar estudiantes desde Excel
"""
import os
import sys
import pandas as pd
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.hashers import make_password
from django.db import transaction
from repositorio.postgres_repository.models import User, Student

def generate_institutional_email(nombres, apellidos):
    """
    Genera el email institucional basado en el formato:
    inicial_nombre + apellido + @unsa.edu.pe
    """
    # Limpiar y normalizar nombres
    nombres = re.sub(r'[^a-zA-Z\s]', '', nombres).strip().lower()
    apellidos = re.sub(r'[^a-zA-Z\s]', '', apellidos).strip().lower()
    
    # Tomar la primera letra del primer nombre
    primer_nombre = nombres.split()[0] if nombres.split() else 'x'
    inicial_nombre = primer_nombre[0] if primer_nombre else 'x'
    
    # Tomar el primer apellido
    primer_apellido = apellidos.split()[0] if apellidos.split() else 'apellido'
    
    # Generar email
    email = f"{inicial_nombre}{primer_apellido}@unsa.edu.pe"
    
    return email

def main():
    try:
        # Leer el archivo Excel
        print('Leyendo archivo: alumnos_450_1703240_B_A (1).xlsx')
        df = pd.read_excel('alumnos_450_1703240_B_A (1).xlsx')
        
        print(f'Archivo cargado exitosamente')
        print(f'Número de filas: {len(df)}')
        print(f'Columnas: {list(df.columns)}')
        
        # Buscar la fila donde empiezan los datos
        start_row = None
        for i, row in df.iterrows():
            if str(row.iloc[0]).strip() == "Nro" and str(row.iloc[1]).strip() == "CUI":
                start_row = i + 1  # Los datos empiezan en la siguiente fila
                break
        
        if start_row is None:
            print('❌ No se encontró la fila de encabezados')
            return
        
        print(f'✅ Datos de estudiantes empiezan en la fila {start_row + 1}')
        
        created_users = 0
        created_students = 0
        errors = 0
        
        # Procesar cada fila del DataFrame desde start_row
        for index in range(start_row, len(df)):
            try:
                row = df.iloc[index]
                
                # Extraer datos de la fila usando posiciones
                nro = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                cui = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
                apellidos_nombres = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
                
                # Verificar que tenemos datos válidos
                if not cui or not apellidos_nombres or cui == 'nan' or apellidos_nombres == 'nan':
                    continue
                
                # Separar apellidos y nombres
                # Formato: "APELLIDO1/APELLIDO2, NOMBRE1 NOMBRE2"
                if ',' in apellidos_nombres:
                    apellidos_part, nombres_part = apellidos_nombres.split(',', 1)
                    apellidos = apellidos_part.replace('/', ' ').strip()
                    nombres = nombres_part.strip()
                else:
                    # Si no hay coma, asumir que todo son apellidos
                    apellidos = apellidos_nombres.replace('/', ' ').strip()
                    nombres = 'Estudiante'
                
                if not cui or not apellidos or not nombres:
                    print(f'⚠️  Fila {index + 1}: Datos incompletos - CUI: {cui}, Apellidos: {apellidos}, Nombres: {nombres}')
                    errors += 1
                    continue
                
                # Generar email institucional
                institutional_email = generate_institutional_email(nombres, apellidos)
                
                with transaction.atomic():
                    # Crear usuario
                    user, user_created = User.objects.get_or_create(
                        institutional_email=institutional_email,
                        defaults={
                            'first_name': nombres,
                            'last_name': apellidos,
                            'role': 'student',
                            'password': make_password(cui),  # CUI como contraseña
                            'is_active': True,
                            'dni': cui if len(cui) == 8 else None
                        }
                    )
                    
                    if user_created:
                        created_users += 1
                        print(f'✅ Usuario creado: {institutional_email}')
                    
                    # Crear estudiante
                    student, student_created = Student.objects.get_or_create(
                        user=user,
                        defaults={
                            'student_code': cui,
                            'academic_status': 'active'
                        }
                    )
                    
                    if student_created:
                        created_students += 1
                        print(f'✅ Estudiante creado: {cui} - {nombres} {apellidos}')
                
            except Exception as e:
                print(f'❌ Error en fila {index + 1}: {str(e)}')
                errors += 1
                continue
        
        # Crear usuario administrador por defecto
        admin_user, admin_created = User.objects.get_or_create(
            institutional_email='admin@unsa.edu.pe',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'role': 'admin',
                'password': make_password('admin123'),
                'is_active': True
            }
        )
        if admin_created:
            print('✅ Usuario administrador creado: admin@unsa.edu.pe (contraseña: admin123)')
        
        # Mostrar resumen
        print(f'''
🎉 RESUMEN DE LA CARGA:
- Usuarios creados: {created_users}
- Estudiantes creados: {created_students}
- Errores: {errors}

📋 CREDENCIALES DE EJEMPLO:
- Administrador: admin@unsa.edu.pe / admin123
- Estudiante (Sophia Esteba): sesteba@unsa.edu.pe / {cui if 'sesteba' in locals() else '20230585'}

🚀 Para probar el sistema:
poetry run python manage.py runserver
''')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()