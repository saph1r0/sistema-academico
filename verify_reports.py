#!/usr/bin/env python
"""
Script de verificación para el sistema de reportes administrativos
"""
import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_servicio_reportes():
    """Test básico del servicio de reportes"""
    print("🔍 Verificando ServicioReportes...")
    
    try:
        from servicios.servicioReportes import ServicioReportes, ReporteGeneracionException
        servicio = ServicioReportes()
        print("✅ ServicioReportes importado correctamente")
        
        # Test validación de librerías
        disponibilidad = servicio.validar_disponibilidad_librerias()
        print(f"📚 Librerías disponibles: {disponibilidad}")
        
        # Test tipos de reportes
        tipos = servicio.obtener_tipos_reportes_disponibles()
        print(f"📊 Tipos de reportes disponibles: {list(tipos.keys())}")
        
        # Test generación de reporte PDF
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
        
        print("🔄 Generando reporte de asistencia PDF...")
        response = servicio.generar_reporte_asistencia_global(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            formato='pdf',
            incluir_detalle=False
        )
        print(f"✅ Reporte PDF generado: {response['Content-Type']}")
        
        # Test generación de reporte Excel
        print("🔄 Generando reporte de asistencia Excel...")
        response = servicio.generar_reporte_asistencia_global(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            formato='excel',
            incluir_detalle=True
        )
        print(f"✅ Reporte Excel generado: {response['Content-Type']}")
        
        # Test reporte de notas
        print("🔄 Generando reporte de notas...")
        response = servicio.generar_reporte_notas_global(
            ciclo='2024-1',
            tipo_reporte='global',
            formato='pdf',
            incluir_estadisticas=True
        )
        print(f"✅ Reporte de notas generado: {response['Content-Type']}")
        
        # Test reporte de estadísticas
        print("🔄 Generando reporte de estadísticas...")
        response = servicio.generar_reporte_estadisticas_global(
            periodo='mensual',
            formato='excel',
            incluir_graficos=False
        )
        print(f"✅ Reporte de estadísticas generado: {response['Content-Type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en ServicioReportes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_views():
    """Test básico de las vistas administrativas"""
    print("\n🔍 Verificando vistas administrativas...")
    
    try:
        from presentacion.administrador.views import AdminReportesView
        from presentacion.administrador.forms import (
            ReporteAsistenciaForm, 
            ReporteNotasForm, 
            ReporteEstadisticasForm
        )
        
        print("✅ AdminReportesView importada correctamente")
        print("✅ Formularios de reportes importados correctamente")
        
        # Test instanciación de formularios
        form_asistencia = ReporteAsistenciaForm()
        form_notas = ReporteNotasForm()
        form_estadisticas = ReporteEstadisticasForm()
        
        print("✅ Formularios instanciados correctamente")
        
        # Verificar campos de formularios
        print(f"📝 Campos formulario asistencia: {list(form_asistencia.fields.keys())}")
        print(f"📝 Campos formulario notas: {list(form_notas.fields.keys())}")
        print(f"📝 Campos formulario estadísticas: {list(form_estadisticas.fields.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en vistas administrativas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_urls():
    """Test de URLs administrativas"""
    print("\n🔍 Verificando URLs administrativas...")
    
    try:
        from django.urls import reverse
        
        # Test URLs principales
        urls_to_test = [
            'admin:dashboard',
            'admin:usuarios',
            'admin:reportes',
            'admin:recursos',
            'admin:configuracion'
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ URL {url_name}: {url}")
            except Exception as e:
                print(f"❌ Error en URL {url_name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error en URLs: {e}")
        return False

def test_templates():
    """Test de templates administrativos"""
    print("\n🔍 Verificando templates administrativos...")
    
    try:
        import os
        from django.conf import settings
        
        # Verificar que existan los templates
        templates_to_check = [
            'administrador/reportes/index.html',
            'administrador/dashboard.html',
            'administrador/usuarios/lista.html',
            'base_admin.html'
        ]
        
        for template in templates_to_check:
            template_path = None
            for template_dir in settings.TEMPLATES[0]['DIRS']:
                full_path = os.path.join(template_dir, template)
                if os.path.exists(full_path):
                    template_path = full_path
                    break
            
            if template_path:
                print(f"✅ Template encontrado: {template}")
            else:
                print(f"❌ Template no encontrado: {template}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando templates: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🚀 Iniciando verificación del sistema de reportes administrativos\n")
    
    tests = [
        ("Servicio de Reportes", test_servicio_reportes),
        ("Vistas Administrativas", test_admin_views),
        ("URLs", test_urls),
        ("Templates", test_templates)
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
    
    print(f"\n🎯 Resultado final: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! El sistema de reportes está funcionando correctamente.")
        return True
    else:
        print("⚠️  Algunos tests fallaron. Revisar los errores anteriores.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)