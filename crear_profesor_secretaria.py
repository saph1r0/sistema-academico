#!/usr/bin/env python
"""
Script para crear profesor y secretaria desde Excel
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
from repositorio.postgres_repository.models import User, Student, Teacher

def extraer_info_profesor_curso(df):
    """Extrae información del profesor y curso del Excel"""
    profesor_nombre = None
    curso_nombre = None
    
    # Buscar en las primeras filas la información del curso y profesor
    for i, row in df.iterrows():
        if i > 10:  # Solo revisar las primeras filas
            break
            
        for col in df.columns:
            valor = str(row[col]).strip() if pd.notna(row[col]) else ''
            
            # Buscar asignatura
            if 'ASIGNATURA' in valor.upper():
                # Formato: "ASIGNATURA : TRABAJO INTERDISCIPLINAR II"
                if ':' in valor:
                    curso_nombre = valor.split(':', 1)[1].strip()
                    print(f"📚 Curso encontrado: {curso_nombre}")
            
            # Buscar profesor (puede estar en diferentes formatos)
            if 'PROFESOR' in valor.upper() or 'DOCENTE' in valor.upper():
                if ':' in valor:
                    profesor_nombre = valor.split(':', 1)[1].strip()
                    print(f"👨‍🏫 Profesor encontrado: {profesor_nombre}")
    
    return profesor_nombre, curso_nombre

def generar_email_profesor(nombre_completo):
    """Genera email para profesor: [primer_nombre]edu@unsa.edu.pe"""
    if not nombre_completo:
        return "profesoredu@unsa.edu.pe"
    
    # Limpiar y normalizar nombre
    nombre_limpio = re.sub(r'[^a-zA-Z\s]', '', nombre_completo).strip().lower()
    
    # Tomar el primer nombre
    primer_nombre = nombre_limpio.split()[0] if nombre_limpio.split() else 'profesor'
    
    # Generar email
    email = f"{primer_nombre}edu@unsa.edu.pe"
    
    return email

def main():
    try:
        # Leer el archivo Excel
        print('📖 Leyendo archivo Excel para extraer información del profesor...')
        df = pd.read_excel('alumnos_450_1703240_B_A (1).xlsx')
        
        # Extraer información del profesor y curso
        profesor_nombre, curso_nombre = extraer_info_profesor_curso(df)
        
        if not profesor_nombre:
            # Si no se encuentra, usar un nombre por defecto
            profesor_nombre = "Juan Carlos Profesor"
            print("⚠️  No se encontró nombre del profesor, usando nombre por defecto")
        
        if not curso_nombre:
            curso_nombre = "Trabajo Interdisciplinar II"
            print("⚠️  No se encontró nombre del curso, usando nombre por defecto")
        
        # Separar nombres y apellidos del profesor
        partes_nombre = profesor_nombre.split()
        if len(partes_nombre) >= 2:
            nombres = ' '.join(partes_nombre[:2])  # Primeros dos nombres
            apellidos = ' '.join(partes_nombre[2:]) if len(partes_nombre) > 2 else partes_nombre[-1]
        else:
            nombres = partes_nombre[0] if partes_nombre else "Profesor"
            apellidos = "Sistema"
        
        # Generar credenciales
        email_profesor = generar_email_profesor(nombres)
        password_profesor = f"{nombres.split()[0].lower()}123"
        
        print(f"\n👨‍🏫 CREANDO PROFESOR:")
        print(f"   Nombre completo: {nombres} {apellidos}")
        print(f"   Email: {email_profesor}")
        print(f"   Contraseña: {password_profesor}")
        print(f"   Curso: {curso_nombre}")
        
        with transaction.atomic():
            # Crear usuario profesor
            profesor_user, profesor_created = User.objects.get_or_create(
                institutional_email=email_profesor,
                defaults={
                    'first_name': nombres,
                    'last_name': apellidos,
                    'role': 'teacher',
                    'password': make_password(password_profesor),
                    'is_active': True
                }
            )
            
            if profesor_created:
                print(f"✅ Usuario profesor creado: {email_profesor}")
            else:
                print(f"ℹ️  Usuario profesor ya existe: {email_profesor}")
            
            # Crear perfil de profesor
            profesor_profile, profile_created = Teacher.objects.get_or_create(
                user=profesor_user,
                defaults={
                    'teacher_code': f"DOC{profesor_user.id.hex[:6].upper()}",
                    'department': 'Ciencia de la Computación',
                    'specialty': curso_nombre,
                    'hours_per_week': 20
                }
            )
            
            if profile_created:
                print(f"✅ Perfil de profesor creado: {profesor_profile.teacher_code}")
            else:
                print(f"ℹ️  Perfil de profesor ya existe: {profesor_profile.teacher_code}")
        
        # Crear secretaria como superusuario
        print(f"\n👩‍💼 CREANDO SECRETARIA:")
        
        with transaction.atomic():
            secretaria_user, secretaria_created = User.objects.get_or_create(
                institutional_email='secretaria@unsa.edu.pe',
                defaults={
                    'first_name': 'María',
                    'last_name': 'Secretaria',
                    'role': 'secretary',
                    'password': make_password('secretaria123'),
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True  # Superusuario por ahora
                }
            )
            
            if secretaria_created:
                print(f"✅ Usuario secretaria creado: secretaria@unsa.edu.pe")
                print(f"   Contraseña: secretaria123")
                print(f"   Permisos: Superusuario")
            else:
                print(f"ℹ️  Usuario secretaria ya existe: secretaria@unsa.edu.pe")
        
        print(f"\n🎉 RESUMEN DE USUARIOS CREADOS:")
        print(f"📋 CREDENCIALES ACTUALIZADAS:")
        print(f"- Administrador: admin@unsa.edu.pe / admin123")
        print(f"- Profesor: {email_profesor} / {password_profesor}")
        print(f"- Secretaria: secretaria@unsa.edu.pe / secretaria123 (SUPERUSUARIO)")
        print(f"- Estudiantes: [nombre]@unsa.edu.pe / [CUI]")
        
        print(f"\n📚 INFORMACIÓN DEL CURSO:")
        print(f"- Curso: {curso_nombre}")
        print(f"- Profesor asignado: {nombres} {apellidos}")
        
        print(f"\n🚀 Para probar el sistema:")
        print(f"poetry run python manage.py runserver")
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()