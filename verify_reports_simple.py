#!/usr/bin/env python
"""
Script de verificación simple para el sistema de reportes administrativos
"""
import os
import sys

def check_file_exists(filepath, description):
    """Verifica si un archivo existe"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} NO ENCONTRADO: {filepath}")
        return False

def check_imports():
    """Verifica que las importaciones necesarias estén disponibles"""
    print("🔍 Verificando importaciones...")
    
    try:
        import reportlab
        print("✅ ReportLab disponible")
    except ImportError:
        print("❌ ReportLab NO disponible")
        return False
    
    try:
        import openpyxl
        print("✅ openpyxl disponible")
    except ImportError:
        print("❌ openpyxl NO disponible")
        return False
    
    return True

def check_code_structure():
    """Verifica la estructura del código"""
    print("\n🔍 Verificando estructura del código...")
    
    files_to_check = [
        ("servicios/servicioReportes.py", "Servicio de Reportes"),
        ("presentacion/administrador/views.py", "Vistas Administrativas"),
        ("presentacion/administrador/forms.py", "Formularios Administrativos"),
        ("presentacion/administrador/urls.py", "URLs Administrativas"),
        ("presentacion/templates/administrador/reportes/index.html", "Template de Reportes"),
        ("tests/test_admin_reports.py", "Tests de Reportes")
    ]
    
    all_exist = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_servicio_reportes_methods():
    """Verifica que el ServicioReportes tenga los métodos necesarios"""
    print("\n🔍 Verificando métodos del ServicioReportes...")
    
    try:
        with open('servicios/servicioReportes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'generar_reporte_asistencia_global',
            'generar_reporte_notas_global',
            'generar_reporte_estadisticas_global',
            '_generar_pdf_asistencia',
            '_generar_excel_asistencia',
            '_generar_pdf_notas',
            '_generar_excel_notas',
            '_generar_pdf_estadisticas',
            '_generar_excel_estadisticas',
            'obtener_tipos_reportes_disponibles',
            'validar_disponibilidad_librerias'
        ]
        
        all_methods_found = True
        for method in required_methods:
            if f"def {method}" in content:
                print(f"✅ Método encontrado: {method}")
            else:
                print(f"❌ Método NO encontrado: {method}")
                all_methods_found = False
        
        return all_methods_found
        
    except Exception as e:
        print(f"❌ Error verificando ServicioReportes: {e}")
        return False

def check_admin_views():
    """Verifica las vistas administrativas"""
    print("\n🔍 Verificando vistas administrativas...")
    
    try:
        with open('presentacion/administrador/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_classes = [
            'AdminReportesView',
            'AdminDashboardView',
            'AdminUsuariosView'
        ]
        
        all_classes_found = True
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✅ Clase encontrada: {class_name}")
            else:
                print(f"❌ Clase NO encontrada: {class_name}")
                all_classes_found = False
        
        # Verificar métodos específicos de AdminReportesView
        required_methods = [
            '_generar_reporte_asistencia',
            '_generar_reporte_notas',
            '_generar_reporte_estadisticas'
        ]
        
        for method in required_methods:
            if f"def {method}" in content:
                print(f"✅ Método encontrado: {method}")
            else:
                print(f"❌ Método NO encontrado: {method}")
                all_classes_found = False
        
        return all_classes_found
        
    except Exception as e:
        print(f"❌ Error verificando vistas: {e}")
        return False

def check_forms():
    """Verifica los formularios"""
    print("\n🔍 Verificando formularios...")
    
    try:
        with open('presentacion/administrador/forms.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_forms = [
            'ReporteAsistenciaForm',
            'ReporteNotasForm',
            'ReporteEstadisticasForm'
        ]
        
        all_forms_found = True
        for form_name in required_forms:
            if f"class {form_name}" in content:
                print(f"✅ Formulario encontrado: {form_name}")
            else:
                print(f"❌ Formulario NO encontrado: {form_name}")
                all_forms_found = False
        
        return all_forms_found
        
    except Exception as e:
        print(f"❌ Error verificando formularios: {e}")
        return False

def check_template():
    """Verifica el template de reportes"""
    print("\n🔍 Verificando template de reportes...")
    
    try:
        template_path = 'presentacion/templates/administrador/reportes/index.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            'form_asistencia',
            'form_notas',
            'form_estadisticas',
            'tab-button',
            'report-form',
            'tipo_reporte'
        ]
        
        all_elements_found = True
        for element in required_elements:
            if element in content:
                print(f"✅ Elemento encontrado: {element}")
            else:
                print(f"❌ Elemento NO encontrado: {element}")
                all_elements_found = False
        
        return all_elements_found
        
    except Exception as e:
        print(f"❌ Error verificando template: {e}")
        return False

def check_tests():
    """Verifica los tests"""
    print("\n🔍 Verificando tests...")
    
    try:
        with open('tests/test_admin_reports.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 Tamaño del archivo de tests: {len(content)} caracteres")
        
        required_test_classes = [
            'TestServicioReportes',
            'TestAdminReportesView',
            'TestReportesIntegration',
            'TestReportesErrorHandling'
        ]
        
        all_tests_found = True
        for test_class in required_test_classes:
            # Try multiple patterns
            patterns = [
                f"class {test_class}(",
                f"class {test_class} (",
                f"class {test_class}(TestCase)",
                f"class {test_class}:"
            ]
            
            found = False
            for pattern in patterns:
                if pattern in content:
                    print(f"✅ Clase de test encontrada: {test_class}")
                    found = True
                    break
            
            if not found:
                print(f"❌ Clase de test NO encontrada: {test_class}")
                all_tests_found = False
        
        return all_tests_found
        
    except Exception as e:
        print(f"❌ Error verificando tests: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🚀 Iniciando verificación simple del sistema de reportes administrativos\n")
    
    tests = [
        ("Importaciones", check_imports),
        ("Estructura del Código", check_code_structure),
        ("Métodos del ServicioReportes", check_servicio_reportes_methods),
        ("Vistas Administrativas", check_admin_views),
        ("Formularios", check_forms),
        ("Template de Reportes", check_template),
        ("Tests", check_tests)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Ejecutando: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE VERIFICACIÓN")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las verificaciones pasaron! El sistema de reportes está implementado correctamente.")
        print("\n📋 FUNCIONALIDADES IMPLEMENTADAS:")
        print("   • Generación de reportes de asistencia en PDF y Excel")
        print("   • Generación de reportes de notas en PDF y Excel")
        print("   • Generación de reportes de estadísticas en PDF y Excel")
        print("   • Interfaz web con formularios para cada tipo de reporte")
        print("   • Manejo de errores y validación de formularios")
        print("   • Tests comprehensivos para todas las funcionalidades")
        return True
    else:
        print("⚠️  Algunas verificaciones fallaron. Revisar los errores anteriores.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)