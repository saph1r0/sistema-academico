#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script de verificación del sistema de monitoreo administrativo.
Verifica que todos los componentes del sistema de monitoreo estén funcionando correctamente.
"""

import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_importaciones():
    """Verifica que todas las importaciones necesarias funcionen"""
    print("🔍 Verificando importaciones del sistema de monitoreo...")
    
    try:
        from dominio.modelo.admin_sistema.inconsistencia_sistema import (
            DetectorInconsistencias, InconsistenciaSistema, TipoInconsistencia, SeveridadInconsistencia
        )
        print("✅ Detector de inconsistencias importado correctamente")
        
        from dominio.modelo.admin_sistema.sistema_alertas import (
            GestorAlertas, AlertaSistema, TipoAlerta, EstadoAlerta
        )
        print("✅ Sistema de alertas importado correctamente")
        
        from dominio.modelo.admin_sistema.auditoria_sistema import (
            SistemaAuditoria, RegistroAuditoria, TipoAccionAuditoria, NivelAuditoria
        )
        print("✅ Sistema de auditoría importado correctamente")
        
        from dominio.modelo.admin_sistema.metricas_rendimiento import (
            MonitorRendimiento, MetricaRendimiento, TipoMetricaRendimiento, EstadoRendimiento
        )
        print("✅ Monitor de rendimiento importado correctamente")
        
        from servicios.servicioMonitoreo import ServicioMonitoreo
        print("✅ Servicio de monitoreo importado correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False

def verificar_detector_inconsistencias():
    """Verifica el funcionamiento del detector de inconsistencias"""
    print("\n🔍 Verificando detector de inconsistencias...")
    
    try:
        from dominio.modelo.admin_sistema.inconsistencia_sistema import (
            DetectorInconsistencias, TipoInconsistencia, SeveridadInconsistencia
        )
        
        detector = DetectorInconsistencias()
        
        # Datos de prueba con inconsistencias
        datos_test = {
            'usuarios': [
                {'id': 1, 'correo_institucional': 'test@universidad.edu', 'nombre': 'Juan', 'apellido': 'Pérez', 'rol': 'estudiante'},
                {'id': 2, 'correo_institucional': 'test@universidad.edu', 'nombre': 'María', 'apellido': '', 'rol': 'estudiante'},  # Duplicado + dato faltante
                {'id': 3, 'correo_institucional': 'valido@universidad.edu', 'nombre': 'Pedro', 'apellido': 'López', 'rol': 'docente'}
            ],
            'cursos': [
                {'id': 1, 'nombre': 'Curso 1'},
                {'id': 2, 'nombre': 'Curso 2'}
            ],
            'matriculas': [
                {'id': 1, 'usuario_id': 1, 'curso_id': 1},  # Válida
                {'id': 2, 'usuario_id': 999, 'curso_id': 1},  # Usuario inexistente
            ],
            'reservas': [
                {
                    'id': 1, 'laboratorio_id': 1, 'fecha': '2024-01-15',
                    'hora_inicio': '08:00', 'hora_fin': '10:00', 'estado': 'aprobada',
                    'numero_participantes': 15
                },
                {
                    'id': 2, 'laboratorio_id': 1, 'fecha': '2024-01-15',
                    'hora_inicio': '09:00', 'hora_fin': '11:00', 'estado': 'aprobada',  # Conflicto
                    'numero_participantes': 35  # Excede capacidad
                }
            ],
            'laboratorios': [
                {'id': 1, 'nombre': 'Lab 1', 'capacidad_maxima': 20}
            ]
        }
        
        # Ejecutar detección
        inconsistencias = detector.ejecutar_deteccion_completa(datos_test)
        
        print(f"✅ Detección ejecutada: {len(inconsistencias)} inconsistencias encontradas")
        
        # Verificar tipos de inconsistencias detectadas
        tipos_encontrados = set(inc.tipo for inc in inconsistencias)
        print(f"   Tipos detectados: {[tipo.value for tipo in tipos_encontrados]}")
        
        # Obtener resumen
        resumen = detector.obtener_resumen_inconsistencias()
        print(f"   Resumen: {resumen['total']} total, por severidad: {resumen['por_severidad']}")
        
        return len(inconsistencias) > 0
        
    except Exception as e:
        print(f"❌ Error en detector de inconsistencias: {e}")
        return False

def verificar_gestor_alertas():
    """Verifica el funcionamiento del gestor de alertas"""
    print("\n🔍 Verificando gestor de alertas...")
    
    try:
        from dominio.modelo.admin_sistema.sistema_alertas import (
            GestorAlertas, TipoAlerta, EstadoAlerta
        )
        from dominio.modelo.admin_sistema.inconsistencia_sistema import (
            InconsistenciaSistema, TipoInconsistencia, SeveridadInconsistencia
        )
        
        gestor = GestorAlertas()
        
        # Crear alerta por error de carga
        alerta_error = gestor.crear_alerta_error_carga(
            "TestModule", 
            "Error de prueba",
            {'codigo': 'TEST_001'}
        )
        gestor.agregar_alerta(alerta_error)
        print("✅ Alerta de error creada y agregada")
        
        # Crear alerta por rendimiento
        alerta_rendimiento = gestor.crear_alerta_rendimiento(
            "tiempo_respuesta", 250.0, 200.0
        )
        gestor.agregar_alerta(alerta_rendimiento)
        print("✅ Alerta de rendimiento creada y agregada")
        
        # Crear alerta desde inconsistencia
        inconsistencia = InconsistenciaSistema()
        inconsistencia.tipo = TipoInconsistencia.USUARIO_DUPLICADO
        inconsistencia.severidad = SeveridadInconsistencia.ALTA
        inconsistencia.titulo = "Usuario duplicado"
        inconsistencia.descripcion = "Correo duplicado detectado"
        
        alerta_inconsistencia = gestor.crear_alerta_desde_inconsistencia(inconsistencia)
        gestor.agregar_alerta(alerta_inconsistencia)
        print("✅ Alerta desde inconsistencia creada y agregada")
        
        # Obtener alertas activas
        alertas_activas = gestor.obtener_alertas_activas()
        print(f"✅ Alertas activas: {len(alertas_activas)}")
        
        # Obtener resumen
        resumen = gestor.obtener_resumen_alertas()
        print(f"   Resumen: {resumen['total_activas']} activas, {resumen['por_severidad']}")
        
        # Resolver una alerta
        if alertas_activas:
            primera_alerta = alertas_activas[0]
            primera_alerta.id = "test_001"  # Asignar ID para prueba
            resultado = gestor.resolver_alerta("test_001", "admin_test", "Problema resuelto")
            print(f"✅ Alerta resuelta: {resultado}")
        
        return len(alertas_activas) >= 2
        
    except Exception as e:
        print(f"❌ Error en gestor de alertas: {e}")
        return False

def verificar_sistema_auditoria():
    """Verifica el funcionamiento del sistema de auditoría"""
    print("\n🔍 Verificando sistema de auditoría...")
    
    try:
        from dominio.modelo.admin_sistema.auditoria_sistema import (
            SistemaAuditoria, TipoAccionAuditoria, NivelAuditoria
        )
        
        sistema = SistemaAuditoria()
        
        # Registrar login exitoso
        registro_login = sistema.registrar_login_admin(
            "admin_001", "Admin Test", "192.168.1.100", exitoso=True
        )
        print("✅ Login administrativo registrado")
        
        # Registrar login fallido
        registro_login_fail = sistema.registrar_login_admin(
            "admin_002", "Admin Fail", "192.168.1.101", 
            exitoso=False, error="Credenciales inválidas"
        )
        print("✅ Login fallido registrado")
        
        # Registrar cambio de usuario
        registro_cambio = sistema.registrar_cambio_usuario(
            "admin_001", "Admin Test", "user_123",
            TipoAccionAuditoria.USUARIO_ACTIVADO,
            datos_anteriores={'activo': False},
            datos_nuevos={'activo': True}
        )
        print("✅ Cambio de usuario registrado")
        
        # Registrar generación de reporte
        registro_reporte = sistema.registrar_generacion_reporte(
            "admin_001", "Admin Test", "asistencia",
            {'fecha_inicio': '2024-01-01', 'fecha_fin': '2024-01-31'},
            exitoso=True
        )
        print("✅ Generación de reporte registrada")
        
        # Obtener registros por usuario
        registros_admin = sistema.obtener_registros_usuario("admin_001")
        print(f"✅ Registros de admin_001: {len(registros_admin)}")
        
        # Obtener estadísticas
        estadisticas = sistema.obtener_estadisticas_auditoria(30)
        print(f"✅ Estadísticas: {estadisticas['total_acciones']} acciones, {estadisticas['errores_detectados']} errores")
        
        return len(sistema.registros) >= 4
        
    except Exception as e:
        print(f"❌ Error en sistema de auditoría: {e}")
        return False

def verificar_monitor_rendimiento():
    """Verifica el funcionamiento del monitor de rendimiento"""
    print("\n🔍 Verificando monitor de rendimiento...")
    
    try:
        from dominio.modelo.admin_sistema.metricas_rendimiento import (
            MonitorRendimiento, EstadoRendimiento
        )
        
        monitor = MonitorRendimiento()
        
        # Verificar inicialización de métricas
        print(f"✅ Métricas inicializadas: {len(monitor.metricas)}")
        
        # Actualizar algunas métricas
        monitor.actualizar_metrica('tiempo_respuesta_db', 120.5)
        monitor.actualizar_metrica('memoria_utilizada', 75.0)
        monitor.actualizar_metrica('cpu_utilizada', 45.0)
        print("✅ Métricas actualizadas")
        
        # Obtener métricas para dashboard
        metricas_dashboard = monitor.obtener_metricas_dashboard()
        print(f"✅ Métricas dashboard: {len(metricas_dashboard)} métricas")
        
        # Obtener métricas en alerta
        alertas_rendimiento = monitor.obtener_metricas_en_alerta()
        print(f"✅ Métricas en alerta: {len(alertas_rendimiento)}")
        
        # Obtener resumen de rendimiento
        resumen = monitor.obtener_resumen_rendimiento()
        print(f"✅ Estado general: {resumen['estado_general']}, {resumen['porcentaje_saludable']}% saludable")
        
        # Simular medición completa
        monitor.simular_medicion_sistema()
        print("✅ Simulación de métricas ejecutada")
        
        return len(metricas_dashboard) > 0
        
    except Exception as e:
        print(f"❌ Error en monitor de rendimiento: {e}")
        return False

def verificar_servicio_monitoreo():
    """Verifica el funcionamiento del servicio de monitoreo integrado"""
    print("\n🔍 Verificando servicio de monitoreo integrado...")
    
    try:
        from servicios.servicioMonitoreo import ServicioMonitoreo
        
        servicio = ServicioMonitoreo()
        
        # Verificar inicialización
        print("✅ Servicio de monitoreo inicializado")
        
        # Registrar acción administrativa
        registro = servicio.registrar_accion_administrativa(
            usuario_id="admin_test",
            usuario_nombre="Admin Test",
            accion="consulta_realizada",
            descripcion="Verificación del sistema",
            contexto_request={'ip': '127.0.0.1'}
        )
        print("✅ Acción administrativa registrada")
        
        # Obtener estado del sistema
        estado = servicio.obtener_estado_sistema()
        print(f"✅ Estado del sistema obtenido: {estado['estado_general']}")
        
        # Obtener alertas para dashboard
        alertas_dashboard = servicio.obtener_alertas_dashboard(limite=5)
        print(f"✅ Alertas dashboard: {len(alertas_dashboard)} alertas")
        
        # Obtener métricas de rendimiento
        metricas_rendimiento = servicio.obtener_metricas_rendimiento_dashboard()
        print(f"✅ Métricas rendimiento: {metricas_rendimiento['estado_general']}")
        
        # Simular métricas
        servicio.simular_metricas_rendimiento()
        print("✅ Métricas de rendimiento simuladas")
        
        # Obtener historial de auditoría
        historial = servicio.obtener_historial_auditoria(limite=10)
        print(f"✅ Historial auditoría: {len(historial)} registros")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en servicio de monitoreo: {e}")
        return False

def verificar_integracion_django():
    """Verifica la integración con Django"""
    print("\n🔍 Verificando integración con Django...")
    
    try:
        # Verificar que las vistas se pueden importar
        from presentacion.administrador.views import AdminMonitoreoView, AdminMonitoreoAPIView
        print("✅ Vistas de monitoreo importadas correctamente")
        
        # Verificar que las URLs están configuradas
        from presentacion.administrador.urls import urlpatterns
        urls_monitoreo = [url for url in urlpatterns if 'monitoreo' in str(url.pattern)]
        print(f"✅ URLs de monitoreo configuradas: {len(urls_monitoreo)} rutas")
        
        return len(urls_monitoreo) > 0
        
    except ImportError as e:
        print(f"❌ Error de integración Django: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🚀 Iniciando verificación del sistema de monitoreo administrativo")
    print("=" * 70)
    
    verificaciones = [
        ("Importaciones", verificar_importaciones),
        ("Detector de Inconsistencias", verificar_detector_inconsistencias),
        ("Gestor de Alertas", verificar_gestor_alertas),
        ("Sistema de Auditoría", verificar_sistema_auditoria),
        ("Monitor de Rendimiento", verificar_monitor_rendimiento),
        ("Servicio de Monitoreo", verificar_servicio_monitoreo),
        ("Integración Django", verificar_integracion_django),
    ]
    
    resultados = []
    
    for nombre, funcion in verificaciones:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error inesperado en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    
    exitosos = 0
    for nombre, resultado in resultados:
        estado = "✅ EXITOSO" if resultado else "❌ FALLIDO"
        print(f"{nombre:<30} {estado}")
        if resultado:
            exitosos += 1
    
    print(f"\n🎯 Resultado: {exitosos}/{len(resultados)} verificaciones exitosas")
    
    if exitosos == len(resultados):
        print("🎉 ¡Sistema de monitoreo verificado correctamente!")
        print("\n📋 Funcionalidades implementadas:")
        print("   • Detección automática de inconsistencias")
        print("   • Sistema de alertas con diferentes severidades")
        print("   • Auditoría completa de acciones administrativas")
        print("   • Monitoreo de métricas de rendimiento en tiempo real")
        print("   • Servicio integrado de monitoreo")
        print("   • Vistas y APIs para el panel administrativo")
        print("   • Templates responsive para visualización")
        
        print("\n🔧 Para usar el sistema:")
        print("   1. Accede a /admin/monitoreo/ para ver el panel completo")
        print("   2. El dashboard en /admin/dashboard/ muestra métricas resumidas")
        print("   3. Las APIs están disponibles en /admin/monitoreo/api/")
        print("   4. Los tests están en tests/test_monitoring_system.py")
        
        return True
    else:
        print("⚠️  Algunas verificaciones fallaron. Revisa los errores anteriores.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)