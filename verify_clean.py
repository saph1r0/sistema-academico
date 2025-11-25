#!/usr/bin/env python
"""
Script de verificación limpio para la configuración de URLs y rutas del sistema
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


def check_url_patterns():
    """Verifica los patrones de URL en config/urls.py"""
    print("\n🔍 Verificando config/urls.py...")
    
    filepath = "config/urls.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no existe")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    patterns_to_check = [
        "path('', login_view, name='login')",
        "path('logout/'",
        "path('admin/', include('presentacion.administrador.urls'))",
        "from presentacion.controladores.admin import login_view"
    ]
    
    found = 0
    for pattern in patterns_to_check:
        if pattern in content:
            found += 1
        else:
            print(f"⚠️  Patrón no encontrado: {pattern}")
    
    if found == len(patterns_to_check):
        print("✅ config/urls.py configurado correctamente")
        return True
    else:
        print(f"❌ config/urls.py incompleto ({found}/{len(patterns_to_check)} patrones)")
        return False


def check_admin_urls():
    """Verifica las URLs del administrador"""
    print("\n🔍 Verificando presentacion/administrador/urls.py...")
    
    filepath = "presentacion/administrador/urls.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no existe")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    patterns_to_check = [
        "app_name = 'admin'",
        "name='dashboard'",
        "name='usuarios'",
        "name='reportes'",
        "name='recursos'",
        "name='configuracion'"
    ]
    
    found = 0
    for pattern in patterns_to_check:
        if pattern in content:
            found += 1
        else:
            print(f"⚠️  Patrón no encontrado: {pattern}")
    
    if found == len(patterns_to_check):
        print("✅ presentacion/administrador/urls.py configurado correctamente")
        return True
    else:
        print(f"❌ presentacion/administrador/urls.py incompleto ({found}/{len(patterns_to_check)} patrones)")
        return False


def check_admin_controller():
    """Verifica el controlador de admin"""
    print("\n🔍 Verificando presentacion/controladores/admin.py...")
    
    filepath = "presentacion/controladores/admin.py"
    if not os.path.exists(filepath):
        print(f"❌ {filepath} no existe")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    patterns_to_check = [
        "def login_view(request):",
        "redirect('admin:dashboard')",
        "from django.contrib.auth import authenticate, login",
        "@csrf_protect"
    ]
    
    found = 0
    for pattern in patterns_to_check:
        if pattern in content:
            found += 1
        else:
            print(f"⚠️  Patrón no encontrado: {pattern}")
    
    if found == len(patterns_to_check):
        print("✅ presentacion/controladores/admin.py configurado correctamente")
        return True
    else:
        print(f"❌ presentacion/controladores/admin.py incompleto ({found}/{len(patterns_to_check)} patrones)")
        return False


def check_templates():
    """Verifica los templates principales"""
    print("\n🔍 Verificando templates...")
    
    # Verificar base_admin.html
    base_admin_path = "presentacion/templates/base_admin.html"
    login_path = "presentacion/templates/auth/login.html"
    
    checks_passed = 0
    
    if os.path.exists(base_admin_path):
        with open(base_admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% url 'admin:dashboard' %}" in content and "{% url 'logout' %}" in content:
            print("✅ base_admin.html configurado correctamente")
            checks_passed += 1
        else:
            print("❌ base_admin.html tiene problemas con las URLs")
    else:
        print("❌ base_admin.html no existe")
    
    if os.path.exists(login_path):
        with open(login_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% url 'login' %}" in content and "{% csrf_token %}" in content:
            print("✅ login.html configurado correctamente")
            checks_passed += 1
        else:
            print("❌ login.html tiene problemas")
    else:
        print("❌ login.html no existe")
    
    return checks_passed == 2


def main():
    """Función principal de verificación"""
    print("🚀 Verificando configuración de URLs y rutas del sistema...")
    print("=" * 70)
    
    # Lista de verificaciones
    checks = [
        ("Archivos principales", lambda: all([
            check_file_exists("config/urls.py"),
            check_file_exists("presentacion/administrador/urls.py"),
            check_file_exists("presentacion/controladores/admin.py"),
            check_file_exists("presentacion/templates/base_admin.html"),
            check_file_exists("presentacion/templates/auth/login.html")
        ])),
        ("URLs principales", check_url_patterns),
        ("URLs del administrador", check_admin_urls),
        ("Controlador de admin", check_admin_controller),
        ("Templates", check_templates),
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
    
    print("\n" + "=" * 70)
    print(f"📊 Resultados: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🎉 ¡Configuración completa! El sistema debería funcionar correctamente.")
        
        print("\n📋 URLs esperadas del sistema:")
        print("   🏠 http://127.0.0.1:8000/ → Login")
        print("   🚪 http://127.0.0.1:8000/logout/ → Logout")
        print("   📊 http://127.0.0.1:8000/admin/dashboard/ → Dashboard")
        print("   👥 http://127.0.0.1:8000/admin/usuarios/ → Gestión de usuarios")
        print("   📄 http://127.0.0.1:8000/admin/reportes/ → Reportes")
        print("   💻 http://127.0.0.1:8000/admin/recursos/ → Recursos")
        print("   ⚙️  http://127.0.0.1:8000/admin/configuracion/ → Configuración")
        
        print("\n🔧 Para probar el sistema:")
        print("   1. Ejecutar migraciones: python manage.py migrate")
        print("   2. Crear superusuario: python manage.py createsuperuser")
        print("   3. Iniciar servidor: python manage.py runserver")
        print("   4. Abrir navegador en: http://127.0.0.1:8000/")
        
        return True
    else:
        print("⚠️  Configuración incompleta. Revisar los elementos faltantes.")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)