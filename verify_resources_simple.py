#!/usr/bin/env python
"""
Script simple para verificar la funcionalidad de recursos y laboratorios
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

def verificar_importaciones():
    """Verifica que las importaciones funcionen correctamente"""
    try:
        from repositorio.postgres_repository.models import LaboratorioModel, ReservaModel, UsuarioModel
        from servicios.servicioReservas import ServicioReservas
        from presentacion.administrador.views import AdminRecursosView
        print("✅ Importaciones exitosas")
        return True
    except ImportError as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def verificar_modelos():
    """Verifica que los modelos estén correctamente definidos"""
    try:
        from repositorio.postgres_repository.models import LaboratorioModel, ReservaModel
        
        # Verificar campos del modelo Laboratorio
        laboratorio_fields = [field.name for field in LaboratorioModel._meta.fields]
        expected_lab_fields = ['id', 'nombre', 'codigo', 'tipo', 'capacidad', 'ubicacion', 'equipamiento', 'activo', 'fecha_creacion', 'fecha_actualizacion']
        
        for field in expected_lab_fields:
            if field not in laboratorio_fields:
                print(f"❌ Campo faltante en LaboratorioModel: {field}")
                return False
        
        # Verificar campos del modelo Reserva
        reserva_fields = [field.name for field in ReservaModel._meta.fields]
        expected_res_fields = ['id', 'laboratorio', 'docente', 'fecha_reserva', 'hora_inicio', 'hora_fin', 'proposito', 'estado', 'aprobada_automaticamente', 'motivo_rechazo', 'fecha_solicitud', 'fecha_actualizacion', 'procesada_por']
        
        for field in expected_res_fields:
            if field not in reserva_fields:
                print(f"❌ Campo faltante en ReservaModel: {field}")
                return False
        
        print("✅ Modelos correctamente definidos")
        return True
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        return False

def verificar_servicio_reservas():
    """Verifica que el servicio de reservas tenga los métodos necesarios"""
    try:
        from servicios.servicioReservas import ServicioReservas
        
        servicio = ServicioReservas()
        
        # Verificar métodos principales
        metodos_esperados = [
            'consultar_disponibilidad',
            'reservar_ambiente', 
            'verificar_conflicto',
            'obtener_laboratorios_activos',
            'obtener_reservas_recientes',
            'obtener_conflictos_activos',
            'obtener_estadisticas_uso'
        ]
        
        for metodo in metodos_esperados:
            if not hasattr(servicio, metodo):
                print(f"❌ Método faltante en ServicioReservas: {metodo}")
                return False
        
        print("✅ ServicioReservas correctamente implementado")
        return True
    except Exception as e:
        print(f"❌ Error verificando ServicioReservas: {e}")
        return False

def verificar_vista_admin():
    """Verifica que la vista de administrador esté correctamente implementada"""
    try:
        from presentacion.administrador.views import AdminRecursosView
        
        vista = AdminRecursosView()
        
        # Verificar que tenga los métodos necesarios
        if not hasattr(vista, 'get_context_data'):
            print("❌ AdminRecursosView no tiene método get_context_data")
            return False
        
        if not hasattr(vista, '_generar_alertas_recursos'):
            print("❌ AdminRecursosView no tiene método _generar_alertas_recursos")
            return False
        
        print("✅ AdminRecursosView correctamente implementada")
        return True
    except Exception as e:
        print(f"❌ Error verificando AdminRecursosView: {e}")
        return False

def verificar_template():
    """Verifica que el template exista"""
    try:
        template_path = 'presentacion/templates/administrador/recursos/index.html'
        if os.path.exists(template_path):
            print("✅ Template de recursos existe")
            return True
        else:
            print(f"❌ Template no encontrado: {template_path}")
            return False
    except Exception as e:
        print(f"❌ Error verificando template: {e}")
        return False

def verificar_urls():
    """Verifica que las URLs estén configuradas"""
    try:
        from presentacion.administrador.urls import urlpatterns
        
        # Buscar la URL de recursos
        recursos_url_found = False
        for pattern in urlpatterns:
            if hasattr(pattern, 'name') and pattern.name == 'recursos':
                recursos_url_found = True
                break
        
        if recursos_url_found:
            print("✅ URL de recursos configurada")
            return True
        else:
            print("❌ URL de recursos no encontrada")
            return False
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DE RECURSOS Y LABORATORIOS")
    print("=" * 50)
    
    verificaciones = [
        ("Importaciones", verificar_importaciones),
        ("Modelos", verificar_modelos),
        ("Servicio de Reservas", verificar_servicio_reservas),
        ("Vista de Administrador", verificar_vista_admin),
        ("Template", verificar_template),
        ("URLs", verificar_urls),
    ]
    
    resultados = []
    
    for nombre, verificacion in verificaciones:
        print(f"\n🔍 Verificando {nombre}...")
        resultado = verificacion()
        resultados.append((nombre, resultado))
    
    # Resumen
    print("\n" + "=" * 50)
    print("🎯 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        estado = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{estado} - {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n🔍 Resultado final: {exitosos}/{len(verificaciones)} verificaciones pasaron")
    
    if exitosos == len(verificaciones):
        print("🎉 ¡Todas las verificaciones pasaron!")
        return True
    else:
        print("⚠️  Algunas verificaciones fallaron. Revisar los errores anteriores.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)