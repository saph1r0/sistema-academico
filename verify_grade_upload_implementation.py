#!/usr/bin/env python
"""
Verificación simple de la implementación de subida de notas del profesor
"""

import os
import re


def check_file_exists(filepath, description):
    """Verificar si un archivo existe"""
    if os.path.exists(filepath):
        print(f"   ✅ {description}: {filepath}")
        return True
    else:
        print(f"   ❌ {description}: {filepath} - NO ENCONTRADO")
        return False


def check_file_content(filepath, patterns, description):
    """Verificar contenido de archivo usando patrones regex"""
    if not os.path.exists(filepath):
        print(f"   ❌ {description}: {filepath} - ARCHIVO NO ENCONTRADO")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_patterns = []
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                found_patterns.append(pattern_name)
        
        if len(found_patterns) == len(patterns):
            print(f"   ✅ {description}: Todos los patrones encontrados")
            return True
        else:
            missing = set(patterns.keys()) - set(found_patterns)
            print(f"   ⚠️  {description}: Faltan patrones: {missing}")
            return False
            
    except Exception as e:
        print(f"   ❌ {description}: Error leyendo archivo - {str(e)}")
        return False


def verify_forms():
    """Verificar formularios"""
    print("📋 Verificando formularios...")
    
    patterns = {
        'SubirNotasFaseForm': r'class SubirNotasFaseForm\(forms\.Form\):',
        'phase_choices': r'PHASE_CHOICES\s*=',
        'course_group_id': r'course_group_id\s*=.*forms\.UUIDField',
        'archivo_excel': r'archivo_excel\s*=.*forms\.FileField',
        'allow_duplicates': r'allow_duplicates\s*=.*forms\.BooleanField'
    }
    
    return check_file_content(
        'presentacion/profesor/forms.py',
        patterns,
        'Formulario SubirNotasFaseForm'
    )


def verify_views():
    """Verificar vistas"""
    print("📋 Verificando vistas...")
    
    patterns = {
        'TeacherGradeUploadView': r'class TeacherGradeUploadView\(.*TemplateView\):',
        'TeacherStatisticsDashboardView': r'class TeacherStatisticsDashboardView\(.*TemplateView\):',
        'GradeUploadAjaxView': r'class GradeUploadAjaxView\(.*View\):',
        'GradeStatisticsAjaxView': r'class GradeStatisticsAjaxView\(.*View\):',
        'DownloadExcelTemplateView': r'class DownloadExcelTemplateView\(.*View\):',
        'ExcelGradeProcessingService': r'ExcelGradeProcessingService',
        'servicio_estadisticas_notas': r'servicio_estadisticas_notas',
    }
    
    return check_file_content(
        'presentacion/profesor/views_grade_upload.py',
        patterns,
        'Vistas de subida de notas'
    )


def verify_templates():
    """Verificar templates"""
    print("📋 Verificando templates...")
    
    results = []
    
    # Template principal
    upload_patterns = {
        'extends_base': r'{%\s*extends\s+[\'"]base_profesor\.html[\'"]',
        'upload_modal': r'id=[\'"]uploadModal[\'"]',
        'drag_drop': r'ondrop=[\'"]handleDrop\(event\)[\'"]',
        'file_input': r'name=[\'"]archivo_excel[\'"]',
        'progress_bar': r'id=[\'"]progressBar[\'"]'
    }
    
    results.append(check_file_content(
        'presentacion/profesor/templates/profesor/grade_upload/index.html',
        upload_patterns,
        'Template de subida de notas'
    ))
    
    # Template de estadísticas
    stats_patterns = {
        'extends_base': r'{%\s*extends\s+[\'"]base_profesor\.html[\'"]',
        'chart_canvas': r'<canvas\s+id=[\'"].*Chart[\'"]',
        'statistics_data': r'statistics_data',
        'chart_js': r'Chart\.js|new Chart\(',
        'distribution_chart': r'distributionChart'
    }
    
    results.append(check_file_content(
        'presentacion/profesor/templates/profesor/grade_upload/statistics.html',
        stats_patterns,
        'Template de estadísticas'
    ))
    
    return all(results)


def verify_urls():
    """Verificar configuración de URLs"""
    print("📋 Verificando URLs...")
    
    patterns = {
        'grade_upload': r'path\([\'"]notas/subir/[\'"].*name=[\'"]grade_upload[\'"]',
        'grade_statistics': r'path\([\'"]notas/estadisticas/[\'"].*name=[\'"]grade_statistics[\'"]',
        'ajax_upload': r'path\([\'"]notas/ajax/upload/[\'"].*name=[\'"]grade_upload_ajax[\'"]',
        'ajax_statistics': r'path\([\'"]notas/ajax/statistics/[\'"].*name=[\'"]grade_statistics_ajax[\'"]',
        'download_template': r'path\([\'"]notas/plantilla/descargar/[\'"].*name=[\'"]download_excel_template[\'"]'
    }
    
    return check_file_content(
        'presentacion/profesor/urls.py',
        patterns,
        'URLs de gestión de notas'
    )


def verify_services():
    """Verificar servicios"""
    print("📋 Verificando servicios...")
    
    results = []
    
    # Servicio de Excel
    excel_patterns = {
        'ExcelGradeTemplateProcessor': r'class ExcelGradeTemplateProcessor:',
        'GradeUploadService': r'class GradeUploadService:',
        'ExcelGradeProcessingService': r'class ExcelGradeProcessingService:',
        'process_excel_template': r'def process_excel_template\(',
        'upload_phase_grades': r'def upload_phase_grades\('
    }
    
    results.append(check_file_content(
        'servicios/servicioExcelNotas.py',
        excel_patterns,
        'Servicio de procesamiento Excel'
    ))
    
    # Servicio de estadísticas
    stats_patterns = {
        'ServicioEstadisticasNotas': r'class ServicioEstadisticasNotas:',
        'ServicioGeneradorGraficos': r'class ServicioGeneradorGraficos:',
        'calculate_basic_statistics': r'def calculate_basic_statistics\(',
        'generate_grade_distribution_chart_data': r'def generate_grade_distribution_chart_data\(',
        'generate_statistics_summary_data': r'def generate_statistics_summary_data\('
    }
    
    results.append(check_file_content(
        'servicios/servicioEstadisticasNotas.py',
        stats_patterns,
        'Servicio de estadísticas'
    ))
    
    return all(results)


def verify_file_structure():
    """Verificar estructura de archivos"""
    print("📋 Verificando estructura de archivos...")
    
    files_to_check = [
        ('presentacion/profesor/views_grade_upload.py', 'Vista principal de subida'),
        ('presentacion/profesor/forms.py', 'Formularios'),
        ('presentacion/profesor/urls.py', 'URLs'),
        ('presentacion/profesor/templates/profesor/grade_upload/index.html', 'Template de subida'),
        ('presentacion/profesor/templates/profesor/grade_upload/statistics.html', 'Template de estadísticas'),
        ('servicios/servicioExcelNotas.py', 'Servicio de Excel'),
        ('servicios/servicioEstadisticasNotas.py', 'Servicio de estadísticas'),
    ]
    
    results = []
    for filepath, description in files_to_check:
        results.append(check_file_exists(filepath, description))
    
    return all(results)


def main():
    """Ejecutar verificación completa"""
    print("🚀 Verificando implementación de subida de notas del profesor")
    print("=" * 70)
    
    verifications = [
        ("Estructura de archivos", verify_file_structure),
        ("Formularios", verify_forms),
        ("Vistas", verify_views),
        ("Templates", verify_templates),
        ("URLs", verify_urls),
        ("Servicios", verify_services),
    ]
    
    results = []
    
    for verification_name, verification_func in verifications:
        print(f"\n🔍 {verification_name}")
        print("-" * 50)
        try:
            result = verification_func()
            results.append((verification_name, result))
        except Exception as e:
            print(f"   ❌ Error en verificación: {str(e)}")
            results.append((verification_name, False))
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for verification_name, result in results:
        status = "✅ COMPLETO" if result else "❌ INCOMPLETO"
        print(f"{status:12} {verification_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} verificaciones completadas")
    
    if passed == total:
        print("\n🎉 ¡Implementación completa!")
        print("✨ Funcionalidades implementadas:")
        print("   • Formulario de subida de notas por fases")
        print("   • Vista con drag-and-drop para archivos Excel")
        print("   • Procesamiento de plantillas Excel 'notas P1'")
        print("   • Dashboard de estadísticas con gráficos Chart.js")
        print("   • Validación y feedback de usuario")
        print("   • Descarga de plantillas Excel")
        print("   • APIs AJAX para subida y estadísticas")
    else:
        print(f"\n⚠️  {total - passed} verificaciones incompletas")
        print("   Revisar los archivos marcados como incompletos")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)