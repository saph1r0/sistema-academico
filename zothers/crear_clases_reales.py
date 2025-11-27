#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear clases reales leyendo Excel de profesores y estudiantes
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioClasesReales import ServicioClasesReales


def main():
    """Ejecuta el proceso de creación de clases reales"""
    print("=" * 80)
    print("CREANDO CLASES REALES DESDE EXCEL")
    print("=" * 80)
    
    try:
        # Crear instancia del servicio
        servicio = ServicioClasesReales()
        
        # Procesar archivos Excel
        resultado = servicio.procesar_excel_completo("EXELS")
        
        # Mostrar resultados
        print(f"\nResultado: {'ÉXITO' if resultado.success else 'ERROR'}")
        print(f"Mensaje: {resultado.message}")
        
        if resultado.data:
            print("\nDatos procesados:")
            for key, value in resultado.data.items():
                print(f"  {key}: {value}")
        
        if resultado.warnings:
            print(f"\nAdvertencias ({len(resultado.warnings)}):")
            for warning in resultado.warnings[:10]:  # Mostrar solo las primeras 10
                print(f"  - {warning}")
            if len(resultado.warnings) > 10:
                print(f"  ... y {len(resultado.warnings) - 10} más")
        
        if resultado.errors:
            print(f"\nErrores ({len(resultado.errors)}):")
            for error in resultado.errors:
                print(f"  - {error}")
        
        print("\n" + "=" * 80)
        
        if resultado.success:
            print("✓ Clases reales creadas exitosamente")
            print("\nPuedes verificar los datos en:")
            print("- Usuarios y profesores en la base de datos")
            print("- Cursos y grupos de cursos")
            print("- Matrículas de estudiantes")
            print("- Registros de asistencia simulados")
            print("- Notas simuladas")
        else:
            print("✗ Error creando clases reales")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)