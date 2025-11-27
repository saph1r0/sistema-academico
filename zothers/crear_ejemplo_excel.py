#!/usr/bin/env python
"""
Script para crear archivos Excel de ejemplo para demostrar el sistema de asignación

Este script crea archivos Excel de prueba que pueden usarse para demostrar
el funcionamiento del sistema de asignación automática de cursos.
"""

import os
import pandas as pd
from pathlib import Path


def main():
    """Crea archivos Excel de ejemplo"""
    
    print("=" * 70)
    print("📝 CREANDO ARCHIVOS EXCEL DE EJEMPLO")
    print("=" * 70)
    
    # Crear directorio de ejemplo si no existe
    example_dir = Path("EJEMPLO_EXCEL")
    example_dir.mkdir(exist_ok=True)
    
    # Crear archivo principal de estudiantes
    create_students_file(example_dir)
    
    # Crear archivos de cursos
    create_course_files(example_dir)
    
    print(f"\n✅ Archivos de ejemplo creados en: {example_dir.absolute()}")
    print("\n📋 Para probar el sistema:")
    print(f"   python manage.py assign_courses --directory {example_dir}")
    print(f"   python demo_assign_courses.py")


def create_students_file(example_dir: Path):
    """Crea el archivo principal bdtotall.xlsx con estudiantes de ejemplo"""
    
    print("\n📄 Creando bdtotall.xlsx...")
    
    # Datos de estudiantes de ejemplo con formato correcto
    # Columnas: A=?, B=CUI, C=?, D=APELLIDO PATERNO, E=APELLIDO MATERNO, F=NOMBRES, G=CORREO
    students_data = [
        {"A": "", "CUI": "20210001", "C": "", "APELLIDO_PATERNO": "Pérez", "APELLIDO_MATERNO": "García", "NOMBRES": "Juan Carlos", "CORREO": "jperez@unsa.edu.pe"},
        {"A": "", "CUI": "20210002", "C": "", "APELLIDO_PATERNO": "López", "APELLIDO_MATERNO": "Vargas", "NOMBRES": "María Elena", "CORREO": "mlopez@unsa.edu.pe"},
        {"A": "", "CUI": "20210003", "C": "", "APELLIDO_PATERNO": "Rodríguez", "APELLIDO_MATERNO": "Silva", "NOMBRES": "Carlos Alberto", "CORREO": "crodriguez@unsa.edu.pe"},
        {"A": "", "CUI": "20210004", "C": "", "APELLIDO_PATERNO": "Martínez", "APELLIDO_MATERNO": "Flores", "NOMBRES": "Ana Sofía", "CORREO": "amartinez@unsa.edu.pe"},
        {"A": "", "CUI": "20210005", "C": "", "APELLIDO_PATERNO": "González", "APELLIDO_MATERNO": "Herrera", "NOMBRES": "Luis Fernando", "CORREO": "lgonzalez@unsa.edu.pe"},
        {"A": "", "CUI": "20210006", "C": "", "APELLIDO_PATERNO": "Sánchez", "APELLIDO_MATERNO": "Morales", "NOMBRES": "Carmen Rosa", "CORREO": "csanchez@unsa.edu.pe"},
        {"A": "", "CUI": "20210007", "C": "", "APELLIDO_PATERNO": "Torres", "APELLIDO_MATERNO": "Castillo", "NOMBRES": "Roberto Miguel", "CORREO": "rtorres@unsa.edu.pe"},
        {"A": "", "CUI": "20210008", "C": "", "APELLIDO_PATERNO": "Ramírez", "APELLIDO_MATERNO": "Vega", "NOMBRES": "Patricia Isabel", "CORREO": "pramirez@unsa.edu.pe"},
        {"A": "", "CUI": "20210009", "C": "", "APELLIDO_PATERNO": "Mendoza", "APELLIDO_MATERNO": "Ruiz", "NOMBRES": "Diego Alejandro", "CORREO": "dmendoza@unsa.edu.pe"},
        {"A": "", "CUI": "20210010", "C": "", "APELLIDO_PATERNO": "Jiménez", "APELLIDO_MATERNO": "Castro", "NOMBRES": "Lucía Fernanda", "CORREO": "ljimenez@unsa.edu.pe"},
    ]
    
    # Crear DataFrame y guardar
    df = pd.DataFrame(students_data)
    file_path = example_dir / "bdtotall.xlsx"
    
    # Crear archivo Excel con encabezados en fila 2
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Escribir una fila vacía primero
        empty_df = pd.DataFrame([[""] * len(df.columns)], columns=df.columns)
        empty_df.to_excel(writer, index=False, header=False, startrow=0)
        
        # Escribir encabezados en fila 2
        header_df = pd.DataFrame([df.columns.tolist()], columns=df.columns)
        header_df.to_excel(writer, index=False, header=False, startrow=1)
        
        # Escribir datos desde fila 3
        df.to_excel(writer, index=False, header=False, startrow=2)
    
    print(f"   ✅ Creado con {len(students_data)} estudiantes")


def create_course_files(example_dir: Path):
    """Crea archivos de cursos de ejemplo"""
    
    print("\n📚 Creando archivos de cursos...")
    
    # Definir cursos y sus estudiantes
    courses = {
        "matematica_aplicada": ["20210001", "20210002", "20210003", "20210004", "20210005"],
        "programacion_web": ["20210003", "20210004", "20210005", "20210006", "20210007"],
        "base_de_datos": ["20210005", "20210006", "20210007", "20210008", "20210009"],
        "ingenieria_software": ["20210001", "20210007", "20210008", "20210009", "20210010"],
    }
    
    for course_name, student_codes in courses.items():
        # Crear DataFrame con códigos de estudiantes
        df = pd.DataFrame({"CODIGO": student_codes})
        
        # Guardar archivo
        file_path = example_dir / f"alumnos_{course_name}.xlsx"
        df.to_excel(file_path, index=False)
        
        print(f"   ✅ alumnos_{course_name}.xlsx ({len(student_codes)} estudiantes)")


if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Error: pandas no está instalado")
        print("   Instalar con: pip install pandas openpyxl")
    except Exception as e:
        print(f"❌ Error creando archivos: {e}")