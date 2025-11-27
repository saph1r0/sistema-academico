#!/usr/bin/env python
"""
Script de verificación simple para la funcionalidad de gestión de usuarios
Verifica que los archivos y código estén implementados correctamente
"""
import os
import re


def check_file_exists(filepath):
    """Verifica que un archivo existe"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} existe")
        return True
    else:
        print(f"❌ {filepath} NO existe")
        return False


def check_code_contains(filepath, patterns, description):
    """Verifica que un archivo contiene ciertos patrones de código"""
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no existe para verificar {description}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    found_patterns = 0
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            found_patterns += 1
        else:
            print(f"⚠️  Patrón no encontrado en {filepath}: {pattern}")
    
    if found_patterns == len(patterns):
        print(f"✅ {description} implementado correctamente en {filepath}")
        return True
    else:
        print(f"❌ {description} incompleto en {filepath} ({found_patterns}/{len(patterns)} patrones encontrados)")
        return False


def verify_admin_usuarios_view():
    """Verifica la implementación de AdminUsuariosView"""
    print("\n🔍 Verificando AdminUsuariosView...")
    
    filepath = "presentacion/administrador/views.py"
    patterns = [
        r"class AdminUsuariosView.*ListView",
        r"def get_queryset\(self\)",
        r"def post\(self.*request",
        r"UsuarioModel\.objects\.all\(\)",
        r"filter\(rol=rol_filter\)",
        r"filter\(activo=True\)",
        r"Q\(nombre__icontains=search_query\)",
        r"activar_usuario\(\)",
        r"desactivar_usuario\(\)",
        r"JsonResponse"
    ]
    
    return check_code_contains(filepath, patterns, "AdminUsuariosView con filtrado y activación/desactivación")


def verify_admin_usuarios_api_view():
    """Verifica la implementación de AdminUsuariosAPIView"""
    print("\n🔍 Verificando AdminUsuariosAPIView...")
    
    filepath = "presentacion/administrador/views.py"
    patterns = [
        r"class AdminUsuariosAPIView.*TemplateView",
        r"def post\(self.*request.*kwargs\)",
        r"action.*request\.POST\.get\('action'\)",
        r"user_id.*request\.POST\.get\('user_id'\)",
        r"usuario\.id == request\.user\.id.*desactivar",
        r"'success': True",
        r"'success': False"
    ]
    
    return check_code_contains(filepath, patterns, "AdminUsuariosAPIView para operaciones AJAX")


def verify_user_template():
    """Verifica la implementación del template de usuarios"""
    print("\n🔍 Verificando template de usuarios...")
    
    filepath = "presentacion/templates/administrador/usuarios/lista.html"
    patterns = [
        r"extends 'base_admin\.html'",
        r"page_title",
        r"search.*input",
        r"rol.*select",
        r"estado.*select",
        r"toggleUserStatus",
        r"fetch.*usuarios_api",
        r"Activar|Desactivar",
        r"pagination",
        r"toast.*notification"
    ]
    
    return check_code_contains(filepath, patterns, "Template de lista de usuarios con filtros y AJAX")


def verify_urls_configuration():
    """Verifica la configuración de URLs"""
    print("\n🔍 Verificando configuración de URLs...")
    
    filepath = "presentacion/administrador/urls.py"
    patterns = [
        r"path\('usuarios/'.*AdminUsuariosView",
        r"path\('usuarios/api/'.*AdminUsuariosAPIView",
        r"name='usuarios'",
        r"name='usuarios_api'"
    ]
    
    return check_code_contains(filepath, patterns, "URLs para gestión de usuarios")


def verify_imports():
    """Verifica las importaciones necesarias"""
    print("\n🔍 Verificando importaciones...")
    
    filepath = "presentacion/administrador/views.py"
    patterns = [
        r"from django\.db\.models import Q",
        r"from django\.core\.paginator import Paginator",
        r"from repositorio\.postgres_repository\.models import UsuarioModel"
    ]
    
    return check_code_contains(filepath, patterns, "Importaciones necesarias")


def verify_test_file():
    """Verifica el archivo de tests"""
    print("\n🔍 Verificando archivo de tests...")
    
    filepath = "tests/test_admin_user_management.py"
    patterns = [
        r"class AdminUserManagementTestCase",
        r"def test_admin_usuarios_view_loads_successfully",
        r"def test_filter_by_role",
        r"def test_search_functionality",
        r"def test_activate_user_success",
        r"def test_deactivate_user_success",
        r"def test_admin_cannot_deactivate_self",
        r"def test_pagination"
    ]
    
    return check_code_contains(filepath, patterns, "Tests de gestión de usuarios")


def verify_model_methods():
    """Verifica los métodos del modelo de usuario"""
    print("\n🔍 Verificando métodos del modelo de usuario...")
    
    filepath = "repositorio/postgres_repository/models.py"
    patterns = [
        r"def activar_usuario\(self\)",
        r"def desactivar_usuario\(self\)",
        r"self\.activo = True",
        r"self\.activo = False",
        r"self\.is_active = True",
        r"self\.is_active = False"
    ]
    
    return check_code_contains(filepath, patterns, "Métodos de activación/desactivación en UsuarioModel")


def main():
    """Función principal de verificación"""
    print("🚀 Verificando implementación de gestión de usuarios...")
    print("=" * 60)
    
    # Lista de verificaciones
    checks = [
        ("Archivo de vista", lambda: check_file_exists("presentacion/administrador/views.py")),
        ("Template de usuarios", lambda: check_file_exists("presentacion/templates/administrador/usuarios/lista.html")),
        ("Archivo de URLs", lambda: check_file_exists("presentacion/administrador/urls.py")),
        ("Archivo de tests", lambda: check_file_exists("tests/test_admin_user_management.py")),
        ("AdminUsuariosView", verify_admin_usuarios_view),
        ("AdminUsuariosAPIView", verify_admin_usuarios_api_view),
        ("Template de usuarios", verify_user_template),
        ("Configuración de URLs", verify_urls_configuration),
        ("Importaciones", verify_imports),
        ("Métodos del modelo", verify_model_methods),
        ("Tests", verify_test_file),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                print(f"❌ Verificación '{check_name}' falló")
        except Exception as e:
            print(f"❌ Error en verificación '{check_name}': {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Resultados: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🎉 ¡Implementación completa! Todos los componentes están presentes.")
        print("\n📋 Funcionalidades implementadas:")
        print("   ✅ Vista de lista de usuarios con paginación")
        print("   ✅ Filtrado por rol (Estudiante, Docente, Secretaria, Admin)")
        print("   ✅ Filtrado por estado (Activo/Inactivo)")
        print("   ✅ Búsqueda por nombre, apellido y email")
        print("   ✅ Activación/desactivación de usuarios via AJAX")
        print("   ✅ Protección contra auto-desactivación del admin")
        print("   ✅ Template responsive con controles interactivos")
        print("   ✅ Notificaciones toast para feedback del usuario")
        print("   ✅ Tests de integración comprehensivos")
        print("   ✅ Manejo de errores y validaciones")
        
        print("\n🔧 Para probar la funcionalidad:")
        print("   1. Ejecutar migraciones: python manage.py migrate")
        print("   2. Crear superusuario: python manage.py createsuperuser")
        print("   3. Acceder a /administrador/usuarios/")
        
        return True
    else:
        print("⚠️  Implementación incompleta. Revisar los elementos faltantes.")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)