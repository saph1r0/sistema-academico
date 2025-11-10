#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de configuración inicial para el sistema automático de asignación de cursos
Este script configura automáticamente todo lo necesario para que el sistema
funcione sin intervención manual.
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import AcademicPeriod

def main():
    """Configura el sistema automáticamente"""
    print("=" * 80)
    print("CONFIGURACION AUTOMATICA DEL SISTEMA")
    print("=" * 80)
    
    try:
        # 1. Verificar/crear período académico
        setup_academic_period()
        
        # 2. Verificar directorio de archivos
        setup_excel_directory()
        
        # 3. Mostrar instrucciones finales
        show_final_instructions()
        
        print("\nCONFIGURACION COMPLETADA")
        print("El sistema está listo para funcionar automáticamente")
        return True
        
    except Exception as e:
        print(f"\nError durante la configuración: {e}")
        return False

def setup_academic_period():
    """Configura el período académico actual"""
    print("\nConfigurando período académico...")
    
    try:
        # Buscar período activo
        active_period = AcademicPeriod.objects.filter(is_active=True).first()
        
        if active_period:
            print(f"Período académico activo encontrado: {active_period.name}")
        else:
            # Crear período por defecto
            today = date.today()
            year = today.year
            semester = "I" if today.month <= 6 else "II"
            
            period = AcademicPeriod.objects.create(
                name=f"{year}-{semester}",
                start_date=today,
                end_date=today + timedelta(days=120),
                laboratory_enrollment_start=today,
                laboratory_enrollment_end=today + timedelta(days=30),
                enrollment_change_deadline=today + timedelta(days=15),
                is_active=True
            )
            print(f"Período académico creado: {period.name}")
            
    except Exception as e:
        print(f"Error configurando período académico: {e}")
        raise

def setup_excel_directory():
    """Verifica y configura el directorio de archivos Excel"""
    print("\nVerificando directorio de archivos Excel...")
    
    excel_dir = 'EXELS'
    if not os.path.exists(excel_dir):
        print(f"Directorio {excel_dir} no encontrado")
        print("   Creando directorio...")
        os.makedirs(excel_dir)
        print(f"Directorio {excel_dir} creado")
        
        # Crear archivo de instrucciones
        instructions_file = os.path.join(excel_dir, 'INSTRUCCIONES.txt')
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write("""INSTRUCCIONES PARA ARCHIVOS EXCEL

Para que el sistema funcione automáticamente, coloque los siguientes archivos en este directorio:

1. bdtotall.xlsx - Archivo principal con todos los estudiantes
   Debe contener las columnas:
   - Columna B: CUI (código del estudiante)
   - Columna D: APELLIDO_PATERNO
   - Columna E: APELLIDO_MATERNO  
   - Columna F: NOMBRES
   - Columna G: CORREO

2. alumnos_*.xlsx - Archivos de cursos específicos
   Ejemplos:
   - alumnos_matematica.xlsx
   - alumnos_programacion.xlsx
   - alumnos_base_de_datos.xlsx
   
   Cada archivo debe contener:
   - Columna A: CODIGO (código del estudiante)

EJECUCIÓN AUTOMÁTICA:
Una vez que tenga los archivos, ejecute:
python ejecutar_asignacion_automatica.py

El sistema procesará automáticamente todos los archivos y creará las asignaciones.
""")
        print(f"Archivo de instrucciones creado: {instructions_file}")
    else:
        print(f"Directorio {excel_dir} encontrado")
        
        # Verificar archivos existentes
        files = os.listdir(excel_dir)
        excel_files = [f for f in files if f.endswith('.xlsx')]
        
        if excel_files:
            print(f"   Archivos Excel encontrados: {len(excel_files)}")
            for file in sorted(excel_files):
                print(f"      • {file}")
        else:
            print("   No se encontraron archivos Excel")

def show_final_instructions():
    """Muestra las instrucciones finales"""
    print("\n" + "=" * 80)
    print("INSTRUCCIONES PARA USO AUTOMATICO")
    print("=" * 80)
    print("""
PASOS PARA USAR EL SISTEMA:

1. Coloque sus archivos Excel en el directorio EXELS/:
   • bdtotall.xlsx (archivo principal con estudiantes)
   • alumnos_*.xlsx (archivos de cursos específicos)

2. Ejecute el proceso automático:
   python ejecutar_asignacion_automatica.py

3. El sistema procesará automáticamente:
   - Leerá todos los archivos Excel
   - Creará cursos automáticamente si no existen
   - Creará estudiantes si no existen
   - Asignará estudiantes a cursos
   - Evitará duplicados
   - Generará reportes detallados

4. Revise el archivo de log:
   asignacion_automatica.log

EJECUCION PERIODICA:
Para automatizar completamente, puede agregar al crontab:
# Ejecutar cada día a las 2:00 AM
0 2 * * * cd /ruta/al/proyecto && python ejecutar_asignacion_automatica.py

IMPORTANTE:
- El sistema es completamente automático
- No requiere intervención manual
- Maneja errores automáticamente
- Genera logs detallados para auditoría
""")

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nConfiguración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)