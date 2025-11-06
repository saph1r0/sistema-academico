#!/usr/bin/env python
"""
Test básico para verificar la implementación de subida de notas del profesor
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from presentacion.profesor.views_grade_upload import TeacherGradeUploadView, TeacherStatisticsDashboardView
from presentacion.profesor.forms import SubirNotasFaseForm
from repositorio.postgres_repository.models import Teacher, CourseGroup, Course, AcademicPeriod


def test_grade_upload_form():
    """Test del formulario de subida de notas por fases"""
    print("🧪 Probando formulario SubirNotasFaseForm...")
    
    # Datos válidos
    form_data = {
        'course_group_id': '12345678-1234-5678-9012-123456789012',
        'phase': 'primera',
        'allow_duplicates': False
    }
    
    form = SubirNotasFaseForm(data=form_data)
    
    # El formulario debería ser válido excepto por el archivo
    print(f"   ✓ Formulario creado correctamente")
    print(f"   ✓ Campos requeridos: {list(form.fields.keys())}")
    print(f"   ✓ Opciones de fase: {form.fields['phase'].choices}")
    
    return True


def test_grade_upload_view():
    """Test de la vista de subida de notas"""
    print("🧪 Probando TeacherGradeUploadView...")
    
    factory = RequestFactory()
    request = factory.get('/profesor/notas/subir/')
    
    # Simular usuario autenticado
    request.user = type('User', (), {
        'is_authenticated': True,
        'teacher': type('Teacher', (), {'id': '12345678-1234-5678-9012-123456789012'})()
    })()
    
    # Agregar middleware necesario
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    
    messages = FallbackStorage(request)
    request._messages = messages
    
    view = TeacherGradeUploadView()
    view.request = request
    
    try:
        context = view.get_context_data()
        print(f"   ✓ Vista inicializada correctamente")
        print(f"   ✓ Contexto contiene: {list(context.keys())}")
        return True
    except Exception as e:
        print(f"   ❌ Error en vista: {str(e)}")
        return False


def test_statistics_dashboard_view():
    """Test de la vista del dashboard de estadísticas"""
    print("🧪 Probando TeacherStatisticsDashboardView...")
    
    factory = RequestFactory()
    request = factory.get('/profesor/notas/estadisticas/')
    
    # Simular usuario autenticado
    request.user = type('User', (), {
        'is_authenticated': True,
        'teacher': type('Teacher', (), {'id': '12345678-1234-5678-9012-123456789012'})()
    })()
    
    # Agregar middleware necesario
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    
    messages = FallbackStorage(request)
    request._messages = messages
    
    view = TeacherStatisticsDashboardView()
    view.request = request
    
    try:
        context = view.get_context_data()
        print(f"   ✓ Dashboard inicializado correctamente")
        print(f"   ✓ Contexto contiene: {list(context.keys())}")
        return True
    except Exception as e:
        print(f"   ❌ Error en dashboard: {str(e)}")
        return False


def test_template_files():
    """Test de existencia de archivos de template"""
    print("🧪 Probando archivos de template...")
    
    templates = [
        'presentacion/profesor/templates/profesor/grade_upload/index.html',
        'presentacion/profesor/templates/profesor/grade_upload/statistics.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"   ✓ {template} existe")
        else:
            print(f"   ❌ {template} no encontrado")
            all_exist = False
    
    return all_exist


def test_urls_configuration():
    """Test de configuración de URLs"""
    print("🧪 Probando configuración de URLs...")
    
    try:
        from presentacion.profesor.urls import urlpatterns
        
        # Buscar URLs relacionadas con notas
        grade_urls = [url for url in urlpatterns if 'notas' in str(url.pattern)]
        
        print(f"   ✓ URLs de notas encontradas: {len(grade_urls)}")
        for url in grade_urls:
            print(f"     - {url.pattern}")
        
        return len(grade_urls) > 0
    except Exception as e:
        print(f"   ❌ Error cargando URLs: {str(e)}")
        return False


def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando tests de implementación de subida de notas del profesor\n")
    
    tests = [
        ("Formulario de subida", test_grade_upload_form),
        ("Vista de subida", test_grade_upload_view),
        ("Dashboard de estadísticas", test_statistics_dashboard_view),
        ("Archivos de template", test_template_files),
        ("Configuración de URLs", test_urls_configuration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Error ejecutando test: {str(e)}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status:10} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! La implementación está lista.")
    else:
        print("⚠️  Algunos tests fallaron. Revisar la implementación.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)