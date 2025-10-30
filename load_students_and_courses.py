#!/usr/bin/env python
"""
Script completo para cargar estudiantes, cursos, grupos y matrículas desde Excel
"""
import os
import sys
import re
import pandas as pd

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth.hashers import make_password
from django.db import transaction
from repositorio.postgres_repository.models import (
    User, Student, Course, CourseGroup, Enrollment, AcademicPeriod
)

# ------------------------------- FUNCIONES -------------------------------

def generate_institutional_email(nombres, apellidos):
    """Genera el email institucional basado en inicial + apellido"""
    nombres = re.sub(r'[^a-zA-Z\s]', '', nombres).strip().lower()
    apellidos = re.sub(r'[^a-zA-Z\s]', '', apellidos).strip().lower()
    inicial_nombre = nombres[0] if nombres else 'x'
    primer_apellido = apellidos.split()[0] if apellidos else 'apellido'
    return f"{inicial_nombre}{primer_apellido}@unsa.edu.pe"

def extract_course_info(file_name):
    """
    Extrae nombre del curso y grupo a partir del nombre del archivo.
    Ejemplo: alumnos_450_1703240_B_A (1).xlsx → ("Trabajo Interdisciplinar II", "A")
    """
    parts = file_name.replace(".xlsx", "").replace(".xls", "").split("_")
    group_code = parts[-1].replace("(1)", "").replace("-", "").strip() if len(parts) > 1 else "A"
    course_name = "Trabajo Interdisciplinar II"
    return course_name, group_code

# ------------------------------- PROCESAMIENTO -------------------------------

def process_excel(file_path, period):
    file_name = os.path.basename(file_path)
    print(f"\n📄 Procesando archivo: {file_name}")

    df = pd.read_excel(file_path)
    start_row = None

    for i, row in df.iterrows():
        if str(row.iloc[0]).strip() == "Nro" and str(row.iloc[1]).strip() == "CUI":
            start_row = i + 1
            break

    if start_row is None:
        print("❌ No se encontró encabezado válido (Nro / CUI)")
        return

    # Determinar curso y grupo
    course_name, group_code = extract_course_info(file_name)

    # Crear curso
    course, _ = Course.objects.get_or_create(
        name=course_name,
        defaults={
            "code": f"C-{course_name.upper().replace(' ', '-')}",
            "credits": 4,
            "theory_hours": 2,
            "practice_hours": 2,
            "is_active": True
        }
    )

    # Crear grupo del curso
    course_group, _ = CourseGroup.objects.get_or_create(
        course=course,
        academic_period=period,
        group_code=group_code,
        defaults={"capacity": 50}
    )

    created_users = created_students = created_enrollments = 0

    for index in range(start_row, len(df)):
        row = df.iloc[index]
        cui = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        apellidos_nombres = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''

        if not cui or not apellidos_nombres:
            continue

        if ',' in apellidos_nombres:
            apellidos_part, nombres_part = apellidos_nombres.split(',', 1)
            apellidos = apellidos_part.replace('/', ' ').strip()
            nombres = nombres_part.strip()
        else:
            apellidos = apellidos_nombres.replace('/', ' ').strip()
            nombres = "Estudiante"

        institutional_email = generate_institutional_email(nombres, apellidos)

        with transaction.atomic():
            # Crear o recuperar usuario
            user, user_created = User.objects.get_or_create(
                institutional_email=institutional_email,
                defaults={
                    'first_name': nombres,
                    'last_name': apellidos,
                    'role': 'student',
                    'password': make_password(cui),
                    'is_active': True,
                    'dni': cui if len(cui) == 8 else None
                }
            )
            if user_created:
                created_users += 1

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

            # Crear matrícula
            from datetime import date

            enrollment, enroll_created = Enrollment.objects.get_or_create(
                student=student,
                course_group=course_group,
                academic_period=period,
                defaults={
                    'status': 'active',
                    'enrollment_type': 'regular',
                    'enrollment_date': date.today()
                }
            )

            if enroll_created:
                created_enrollments += 1

    print(f"✅ Usuarios nuevos: {created_users} | Estudiantes: {created_students} | Matrículas: {created_enrollments}")

# ------------------------------- SCRIPT PRINCIPAL -------------------------------

def main():
    base_path = "."
    academic_period_name = "2024-I"

    period, _ = AcademicPeriod.objects.get_or_create(
        name=academic_period_name,
        defaults={
            "is_active": True,
            "start_date": "2024-03-01",
            "end_date": "2024-07-30"
        }
    )

    print(f"📘 Período académico activo: {period.name}")
    print(f"📂 Buscando archivos en: {os.path.abspath(base_path)}")

    for file_name in os.listdir(base_path):
        if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            process_excel(os.path.join(base_path, file_name), period)

    # Crear usuario administrador
    admin_user, created = User.objects.get_or_create(
        institutional_email="admin@unsa.edu.pe",
        defaults={
            "first_name": "Administrador",
            "last_name": "Sistema",
            "role": "admin",
            "password": make_password("admin123"),
            "is_active": True
        }
    )
    if created:
        print("✅ Usuario administrador creado: admin@unsa.edu.pe / admin123")

    print("\n🎉 CARGA COMPLETADA EXITOSAMENTE")

if __name__ == "__main__":
    main()
