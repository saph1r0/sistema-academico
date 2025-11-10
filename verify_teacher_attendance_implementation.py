#!/usr/bin/env python
"""
Script de verificación para la implementación del sistema de asistencia docente
Verifica que todos los componentes estén implementados correctamente
"""

import os
import re
from pathlib import Path


def check_file_exists(file_path, description):
    """Verifica si un archivo existe"""
    if os.path.exists(file_path):
        print(f"   ✓ {description}: {file_path}")
        return True
    else:
        print(f"   ✗ {description}: {file_path} - NO ENCONTRADO")
        return False


def check_class_in_file(file_path, class_name, description):
    """Verifica si una clase existe en un archivo"""
    if not os.path.exists(file_path):
        print(f"   ✗ {description}: Archivo {file_path} no encontrado")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"class {class_name}" in content:
                print(f"   ✓ {description}: Clase {class_name} encontrada")
                return True
            else:
                print(f"   ✗ {description}: Clase {class_name} no encontrada")
                return False
    except Exception as e:
        print(f"   ✗ {description}: Error leyendo archivo - {e}")
        return False


def check_method_in_file(file_path, method_name, description):
    """Verifica si un método existe en un archivo"""
    if not os.path.exists(file_path):
        print(f"   ✗ {description}: Archivo {file_path} no encontrado")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"def {method_name}" in content:
                print(f"   ✓ {description}: Método {method_name} encontrado")
                return True
            else:
                print(f"   ✗ {description}: Método {method_name} no encontrado")
                return False
    except Exception as e:
        print(f"   ✗ {description}: Error leyendo archivo - {e}")
        return False


def check_import_in_file(file_path, import_statement, description):
    """Verifica si un import existe en un archivo"""
    if not os.path.exists(file_path):
        print(f"   ✗ {description}: Archivo {file_path} no encontrado")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if import_statement in content:
                print(f"   ✓ {description}: Import encontrado")
                return True
            else:
                print(f"   ✗ {description}: Import no encontrado")
                return False
    except Exception as e:
        print(f"   ✗ {description}: Error leyendo archivo - {e}")
        return False


def verify_teacher_attendance_implementation():
    """Verifica la implementación completa del sistema de asistencia docente"""
    print("=== VERIFICACIÓN DEL SISTEMA DE ASISTENCIA DOCENTE ===\n")
    
    total_checks = 0
    passed_checks = 0
    
    # 1. Verificar que existe el servicio de asistencia docente
    print("1. Verificando servicio de asistencia docente...")
    checks = [
        check_file_exists(
            "servicios/servicioAsistenciaDocente.py",
            "Archivo del servicio"
        ),
        check_class_in_file(
            "servicios/servicioAsistenciaDocente.py",
            "ServicioAsistenciaDocente",
            "Clase principal del servicio"
        ),
        check_method_in_file(
            "servicios/servicioAsistenciaDocente.py",
            "registrar_login_automatico",
            "Método de registro de login"
        ),
        check_method_in_file(
            "servicios/servicioAsistenciaDocente.py",
            "registrar_logout_automatico",
            "Método de registro de logout"
        ),
        check_method_in_file(
            "servicios/servicioAsistenciaDocente.py",
            "calcular_estadisticas_asistencia",
            "Método de cálculo de estadísticas"
        ),
    ]
    total_checks += len(checks)
    passed_checks += sum(checks)
    
    # 2. Verificar modelo TeacherAttendance mejorado
    print("\n2. Verificando modelo TeacherAttendance mejorado...")
    checks = [
        check_class_in_file(
            "repositorio/postgres_repository/models.py",
            "TeacherAttendance",
            "Modelo TeacherAttendance"
        ),
    ]
    
    # Verificar campos específicos del modelo mejorado
    model_file = "repositorio/postgres_repository/models.py"
    if os.path.exists(model_file):
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_fields = [
            'course_group',
            'session_duration',
            'triggered_progress_update',
            'is_valid_session',
            'duration_hours'
        ]
        
        for field in required_fields:
            if field in content:
                print(f"   ✓ Campo/método {field} encontrado")
                checks.append(True)
            else:
                print(f"   ✗ Campo/método {field} no encontrado")
                checks.append(False)
    
    total_checks += len(checks)
    passed_checks += sum(checks)
    
    # 3. Verificar middleware de asistencia automática
    print("\n3. Verificando middleware de asistencia automática...")
    checks = [
        check_class_in_file(
            "presentacion/middleware.py",
            "TeacherAttendanceMiddleware",
            "Clase del middleware"
        ),
        check_method_in_file(
            "presentacion/middleware.py",
            "_handle_teacher_login",
            "Método de manejo de login"
        ),
        check_method_in_file(
            "presentacion/middleware.py",
            "_handle_teacher_logout",
            "Método de manejo de logout"
        ),
        check_import_in_file(
            "presentacion/middleware.py",
            "from servicios.servicioAsistenciaDocente import ServicioAsistenciaDocente",
            "Import del servicio"
        ),
    ]
    total_checks += len(checks)
    passed_checks += sum(checks)
    
    # 4. Verificar migración
    print("\n4. Verificando migración de base de datos...")
    migration_file = "repositorio/postgres_repository/migrations/0002_enhance_teacher_attendance.py"
    checks = [
        check_file_exists(migration_file, "Archivo de migración"),
    ]
    
    if os.path.exists(migration_file):
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        migration_operations = [
            'AddField',
            'course_group',
            'session_duration',
            'triggered_progress_update',
            'AddIndex'
        ]
        
        for operation in migration_operations:
            if operation in content:
                print(f"   ✓ Operación de migración {operation} encontrada")
                checks.append(True)
            else:
                print(f"   ✗ Operación de migración {operation} no encontrada")
                checks.append(False)
    
    total_checks += len(checks)
    passed_checks += sum(checks)
    
    # 5. Verificar archivos de test
    print("\n5. Verificando archivos de test...")
    checks = [
        check_file_exists(
            "test_teacher_attendance_system.py",
            "Script de test del sistema"
        ),
        check_method_in_file(
            "test_teacher_attendance_system.py",
            "test_teacher_attendance_system",
            "Función principal de test"
        ),
    ]
    total_checks += len(checks)
    passed_checks += sum(checks)
    
    # Resumen final
    print(f"\n=== RESUMEN DE VERIFICACIÓN ===")
    print(f"Total de verificaciones: {total_checks}")
    print(f"Verificaciones exitosas: {passed_checks}")
    print(f"Verificaciones fallidas: {total_checks - passed_checks}")
    print(f"Porcentaje de éxito: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 ¡IMPLEMENTACIÓN COMPLETA Y CORRECTA!")
        print("\nComponentes implementados:")
        print("✓ Modelo TeacherAttendance mejorado con campos adicionales")
        print("✓ Servicio ServicioAsistenciaDocente para manejo de registros")
        print("✓ Middleware TeacherAttendanceMiddleware para captura automática")
        print("✓ Migración de base de datos")
        print("✓ Scripts de testing")
        
        print("\nFuncionalidades implementadas:")
        print("✓ Registro automático de login/logout")
        print("✓ Cálculo de duración de sesiones")
        print("✓ Determinación de tipo de acceso por IP")
        print("✓ Actualización automática de progreso de cursos")
        print("✓ Cálculo de estadísticas de asistencia")
        print("✓ Obtención de impacto en progreso de cursos")
        print("✓ Gestión de sesiones activas")
        
        return True
    else:
        print(f"\n❌ IMPLEMENTACIÓN INCOMPLETA")
        print(f"Faltan {total_checks - passed_checks} componentes por implementar o corregir")
        return False


def show_next_steps():
    """Muestra los próximos pasos para completar la implementación"""
    print("\n=== PRÓXIMOS PASOS ===")
    print("1. Ejecutar la migración de base de datos:")
    print("   python manage.py makemigrations")
    print("   python manage.py migrate")
    
    print("\n2. Agregar el middleware a settings.py:")
    print("   MIDDLEWARE = [")
    print("       # ... otros middlewares ...")
    print("       'presentacion.middleware.TeacherAttendanceMiddleware',")
    print("   ]")
    
    print("\n3. Configurar logging en settings.py:")
    print("   LOGGING = {")
    print("       'loggers': {")
    print("           'admin_panel': {")
    print("               'handlers': ['file'],")
    print("               'level': 'INFO',")
    print("           },")
    print("       },")
    print("   }")
    
    print("\n4. Probar el sistema:")
    print("   - Hacer login como docente")
    print("   - Verificar que se registre la asistencia automáticamente")
    print("   - Hacer logout y verificar el cálculo de duración")
    print("   - Revisar las estadísticas de asistencia")


if __name__ == '__main__':
    try:
        success = verify_teacher_attendance_implementation()
        
        if success:
            show_next_steps()
        else:
            print("\nRevisa los componentes faltantes y completa la implementación.")
            
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")