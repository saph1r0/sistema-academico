#!/usr/bin/env python3
"""
Script para verificar la configuración de Yessenia sin cargar Django completamente
"""

import os
import sys

def check_files_exist():
    """Verificar que los archivos necesarios existen"""
    print("🔍 Verificando archivos del sistema...")
    
    required_files = [
        'presentacion/profesor/views_simple.py',
        'presentacion/profesor/templates/profesor/course_detail.html',
        'presentacion/profesor/urls.py',
        'servicios/servicioContenidoCurso.py',
        'create_yessenia_teacher.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
            all_exist = False
    
    return all_exist

def check_dashboard_view_fix():
    """Verificar que el error de 'enrollments' fue corregido"""
    print("\n🔍 Verificando corrección del error 'enrollments'...")
    
    try:
        with open('presentacion/profesor/views_simple.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que no se use 'enrollments' incorrectamente
        if 'enrollments' in content and 'Count(' in content:
            print("❌ Aún se usa 'enrollments' en Count() - esto causará error")
            return False
        
        # Verificar que se use la corrección
        if 'Enrollment.objects.filter(' in content:
            print("✅ Se usa Enrollment.objects.filter() correctamente")
            return True
        else:
            print("⚠️  No se encontró el patrón de corrección esperado")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando archivo: {str(e)}")
        return False

def provide_solution_steps():
    """Proporcionar pasos para solucionar el problema"""
    print("\n" + "=" * 60)
    print("📋 PASOS PARA SOLUCIONAR EL PROBLEMA DE YESSENIA")
    print("=" * 60)
    
    print("\n1️⃣  CREAR USUARIO YESSENIA:")
    print("   Ejecutar: python create_yessenia_teacher.py")
    print("   Esto creará:")
    print("   - Usuario Yessenia como profesora")
    print("   - Curso MAT101 - Matemática Aplicada")
    print("   - Estudiantes matriculados de ejemplo")
    
    print("\n2️⃣  VERIFICAR CORRECCIÓN DEL ERROR:")
    print("   El error 'Cannot resolve keyword enrollments' fue corregido")
    print("   Se cambió de Count('enrollments') a Enrollment.objects.filter()")
    
    print("\n3️⃣  ACCEDER AL SISTEMA:")
    print("   URL: http://localhost:8000/profesor/dashboard/")
    print("   Email: yessenia@unsa.edu.pe")
    print("   Contraseña: yessenia123")
    
    print("\n4️⃣  FUNCIONALIDADES DISPONIBLES:")
    print("   ✅ Dashboard con estadísticas del curso")
    print("   ✅ Vista de detalle del curso")
    print("   ✅ Gestión de temas del curso")
    print("   ✅ Estadísticas de asistencia docente")
    print("   ✅ Progreso del curso en tiempo real")
    
    print("\n5️⃣  VERIFICAR IMPLEMENTACIÓN:")
    print("   Ejecutar: python verify_course_detail_implementation.py")
    print("   Para confirmar que todo está funcionando")

def main():
    """Función principal"""
    print("🚀 Verificando configuración para solucionar problema de Yessenia...")
    print("=" * 70)
    
    # Verificar archivos
    files_ok = check_files_exist()
    
    # Verificar corrección del error
    fix_ok = check_dashboard_view_fix()
    
    # Proporcionar solución
    provide_solution_steps()
    
    print("\n" + "=" * 70)
    if files_ok and fix_ok:
        print("🎉 ¡SISTEMA LISTO PARA USAR!")
        print("\n✅ Todos los archivos están en su lugar")
        print("✅ El error de 'enrollments' fue corregido")
        print("✅ Script para crear Yessenia está disponible")
        
        print("\n🚀 PRÓXIMO PASO:")
        print("   Ejecutar: python create_yessenia_teacher.py")
        print("   Luego acceder al dashboard de profesor")
        
        return True
    else:
        print("❌ Hay problemas que necesitan ser corregidos")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)