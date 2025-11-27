#!/usr/bin/env python
"""
Script de verificación para la funcionalidad de gestión de usuarios
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from repositorio.postgres_repository.models import UsuarioModel
import json


def create_test_users():
    """Crear usuarios de prueba"""
    print("🔧 Creando usuarios de prueba...")
    
    # Limpiar usuarios existentes (solo para testing)
    UsuarioModel.objects.filter(email__contains='@test.com').delete()
    
    # Crear admin
    admin = UsuarioModel.objects.create_user(
        email='admin@test.com',
        password='admin123',
        nombre='Admin',
        apellido='Test',
        rol='admin',
        activo=True
    )
    
    # Crear usuarios de diferentes roles
    users = [
        ('estudiante@test.com', 'Juan', 'Pérez', 'estudiante', True),
        ('docente@test.com', 'María', 'García', 'docente', True),
        ('secretaria@test.com', 'Ana', 'López', 'secretaria', False),
        ('inactive@test.com', 'Pedro', 'Martín', 'estudiante', False),
    ]
    
    created_users = [admin]
    for email, nombre, apellido, rol, activo in users:
        user = UsuarioModel.objects.create_user(
            email=email,
            password='test123',
            nombre=nombre,
            apellido=apellido,
            rol=rol,
            activo=activo
        )
        created_users.append(user)
    
    print(f"✅ Creados {len(created_users)} usuarios de prueba")
    return created_users


def test_user_list_view():
    """Test de la vista de lista de usuarios"""
    print("\n🧪 Probando vista de lista de usuarios...")
    
    client = Client()
    
    # Login como admin
    login_success = client.login(email='admin@test.com', password='admin123')
    if not login_success:
        print("❌ Error: No se pudo hacer login como admin")
        return False
    
    # Probar carga de la vista
    url = reverse('administrador:usuarios')
    response = client.get(url)
    
    if response.status_code != 200:
        print(f"❌ Error: Vista retornó código {response.status_code}")
        return False
    
    print("✅ Vista de usuarios carga correctamente")
    
    # Probar filtros
    response = client.get(url, {'rol': 'estudiante'})
    if response.status_code != 200:
        print("❌ Error: Filtro por rol falló")
        return False
    
    print("✅ Filtro por rol funciona")
    
    # Probar búsqueda
    response = client.get(url, {'search': 'Juan'})
    if response.status_code != 200:
        print("❌ Error: Búsqueda falló")
        return False
    
    print("✅ Búsqueda funciona")
    
    return True


def test_user_activation():
    """Test de activación/desactivación de usuarios"""
    print("\n🧪 Probando activación/desactivación de usuarios...")
    
    client = Client()
    client.login(email='admin@test.com', password='admin123')
    
    # Obtener usuario inactivo
    inactive_user = UsuarioModel.objects.get(email='inactive@test.com')
    
    # Probar activación
    url = reverse('administrador:usuarios_api')
    response = client.post(url, {
        'action': 'activar',
        'user_id': inactive_user.id
    })
    
    if response.status_code != 200:
        print(f"❌ Error: API retornó código {response.status_code}")
        return False
    
    try:
        data = json.loads(response.content)
        if not data.get('success'):
            print(f"❌ Error: {data.get('error', 'Error desconocido')}")
            return False
    except json.JSONDecodeError:
        print("❌ Error: Respuesta no es JSON válido")
        return False
    
    # Verificar que el usuario fue activado
    inactive_user.refresh_from_db()
    if not inactive_user.activo:
        print("❌ Error: Usuario no fue activado en la base de datos")
        return False
    
    print("✅ Activación de usuario funciona")
    
    # Probar desactivación
    active_user = UsuarioModel.objects.get(email='estudiante@test.com')
    response = client.post(url, {
        'action': 'desactivar',
        'user_id': active_user.id
    })
    
    if response.status_code != 200:
        print(f"❌ Error: Desactivación retornó código {response.status_code}")
        return False
    
    data = json.loads(response.content)
    if not data.get('success'):
        print(f"❌ Error: {data.get('error', 'Error desconocido')}")
        return False
    
    # Verificar que el usuario fue desactivado
    active_user.refresh_from_db()
    if active_user.activo:
        print("❌ Error: Usuario no fue desactivado en la base de datos")
        return False
    
    print("✅ Desactivación de usuario funciona")
    
    return True


def test_admin_self_protection():
    """Test que el admin no puede desactivarse a sí mismo"""
    print("\n🧪 Probando protección de auto-desactivación...")
    
    client = Client()
    client.login(email='admin@test.com', password='admin123')
    
    admin_user = UsuarioModel.objects.get(email='admin@test.com')
    
    url = reverse('administrador:usuarios_api')
    response = client.post(url, {
        'action': 'desactivar',
        'user_id': admin_user.id
    })
    
    if response.status_code != 400:
        print(f"❌ Error: Debería retornar 400, retornó {response.status_code}")
        return False
    
    data = json.loads(response.content)
    if data.get('success'):
        print("❌ Error: No debería permitir auto-desactivación")
        return False
    
    print("✅ Protección de auto-desactivación funciona")
    return True


def test_permission_protection():
    """Test de protección de permisos"""
    print("\n🧪 Probando protección de permisos...")
    
    client = Client()
    
    # Intentar acceder sin login
    url = reverse('administrador:usuarios')
    response = client.get(url)
    
    if response.status_code != 302:
        print(f"❌ Error: Debería redirigir (302), retornó {response.status_code}")
        return False
    
    print("✅ Protección sin login funciona")
    
    # Intentar acceder con usuario no admin
    client.login(email='estudiante@test.com', password='test123')
    response = client.get(url)
    
    if response.status_code != 302:
        print(f"❌ Error: Debería redirigir (302), retornó {response.status_code}")
        return False
    
    print("✅ Protección de rol funciona")
    
    return True


def main():
    """Función principal de verificación"""
    print("🚀 Iniciando verificación de gestión de usuarios...")
    
    try:
        # Crear usuarios de prueba
        users = create_test_users()
        
        # Ejecutar tests
        tests = [
            test_permission_protection,
            test_user_list_view,
            test_user_activation,
            test_admin_self_protection,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    print(f"❌ Test {test.__name__} falló")
            except Exception as e:
                print(f"❌ Test {test.__name__} falló con excepción: {e}")
        
        print(f"\n📊 Resultados: {passed}/{total} tests pasaron")
        
        if passed == total:
            print("🎉 ¡Todos los tests pasaron! La funcionalidad está implementada correctamente.")
            return True
        else:
            print("⚠️  Algunos tests fallaron. Revisar implementación.")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        return False
    finally:
        # Limpiar usuarios de prueba
        print("\n🧹 Limpiando usuarios de prueba...")
        UsuarioModel.objects.filter(email__contains='@test.com').delete()
        print("✅ Limpieza completada")


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)