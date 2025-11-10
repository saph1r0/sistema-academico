#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Importar las clases del sistema de monitoreo
from dominio.modelo.admin_sistema.inconsistencia_sistema import (
    DetectorInconsistencias, InconsistenciaSistema, TipoInconsistencia, SeveridadInconsistencia
)
from dominio.modelo.admin_sistema.sistema_alertas import (
    GestorAlertas, AlertaSistema, TipoAlerta, EstadoAlerta
)
from dominio.modelo.admin_sistema.auditoria_sistema import (
    SistemaAuditoria, RegistroAuditoria, TipoAccionAuditoria, NivelAuditoria
)
from dominio.modelo.admin_sistema.metricas_rendimiento import (
    MonitorRendimiento, MetricaRendimiento, TipoMetricaRendimiento, EstadoRendimiento
)
from servicios.servicioMonitoreo import ServicioMonitoreo


class TestDetectorInconsistencias(unittest.TestCase):
    """Tests para el detector de inconsistencias del sistema"""
    
    def setUp(self):
        self.detector = DetectorInconsistencias()
    
    def test_detectar_usuarios_duplicados(self):
        """Test detección de usuarios con correos duplicados"""
        datos_test = {
            'usuarios': [
                {'id': 1, 'correo_institucional': 'test@universidad.edu', 'nombre': 'Juan', 'apellido': 'Pérez', 'rol': 'estudiante'},
                {'id': 2, 'correo_institucional': 'test@universidad.edu', 'nombre': 'María', 'apellido': 'García', 'rol': 'estudiante'},
                {'id': 3, 'correo_institucional': 'otro@universidad.edu', 'nombre': 'Pedro', 'apellido': 'López', 'rol': 'docente'}
            ]
        }
        
        inconsistencias = self.detector._detectar_usuarios_duplicados(datos_test)
        
        self.assertEqual(len(inconsistencias), 1)
        self.assertEqual(inconsistencias[0].tipo, TipoInconsistencia.USUARIO_DUPLICADO)
        self.assertEqual(inconsistencias[0].severidad, SeveridadInconsistencia.ALTA)
        self.assertIn('test@universidad.edu', inconsistencias[0].descripcion)
    
    def test_detectar_matriculas_invalidas(self):
        """Test detección de matrículas con referencias rotas"""
        datos_test = {
            'usuarios': [
                {'id': 1, 'correo_institucional': 'user1@universidad.edu'},
                {'id': 2, 'correo_institucional': 'user2@universidad.edu'}
            ],
            'cursos': [
                {'id': 1, 'nombre': 'Curso 1'},
                {'id': 2, 'nombre': 'Curso 2'}
            ],
            'matriculas': [
                {'id': 1, 'usuario_id': 1, 'curso_id': 1},  # Válida
                {'id': 2, 'usuario_id': 999, 'curso_id': 1},  # Usuario inexistente
                {'id': 3, 'usuario_id': 1, 'curso_id': 999}   # Curso inexistente
            ]
        }
        
        inconsistencias = self.detector._detectar_matriculas_invalidas(datos_test)
        
        self.assertEqual(len(inconsistencias), 2)
        self.assertTrue(all(inc.tipo == TipoInconsistencia.REFERENCIA_ROTA for inc in inconsistencias))
        self.assertTrue(all(inc.severidad == SeveridadInconsistencia.CRITICA for inc in inconsistencias))
    
    def test_detectar_conflictos_reservas(self):
        """Test detección de conflictos en reservas de laboratorios"""
        datos_test = {
            'reservas': [
                {
                    'id': 1, 'laboratorio_id': 1, 'fecha': '2024-01-15',
                    'hora_inicio': '08:00', 'hora_fin': '10:00', 'estado': 'aprobada'
                },
                {
                    'id': 2, 'laboratorio_id': 1, 'fecha': '2024-01-15',
                    'hora_inicio': '09:00', 'hora_fin': '11:00', 'estado': 'aprobada'  # Conflicto
                },
                {
                    'id': 3, 'laboratorio_id': 1, 'fecha': '2024-01-15',
                    'hora_inicio': '11:00', 'hora_fin': '13:00', 'estado': 'aprobada'  # Sin conflicto
                }
            ]
        }
        
        inconsistencias = self.detector._detectar_conflictos_reservas(datos_test)
        
        self.assertEqual(len(inconsistencias), 1)
        self.assertEqual(inconsistencias[0].tipo, TipoInconsistencia.RESERVA_CONFLICTO)
        self.assertEqual(inconsistencias[0].severidad, SeveridadInconsistencia.ALTA)
    
    def test_detectar_capacidad_excedida(self):
        """Test detección de capacidad excedida en laboratorios"""
        datos_test = {
            'laboratorios': [
                {'id': 1, 'nombre': 'Lab 1', 'capacidad_maxima': 20},
                {'id': 2, 'nombre': 'Lab 2', 'capacidad_maxima': 30}
            ],
            'reservas': [
                {
                    'id': 1, 'laboratorio_id': 1, 'numero_participantes': 15,
                    'estado': 'aprobada'  # OK
                },
                {
                    'id': 2, 'laboratorio_id': 1, 'numero_participantes': 25,
                    'estado': 'aprobada'  # Excede capacidad
                },
                {
                    'id': 3, 'laboratorio_id': 2, 'numero_participantes': 35,
                    'estado': 'aprobada'  # Excede capacidad
                }
            ]
        }
        
        inconsistencias = self.detector._detectar_capacidad_excedida(datos_test)
        
        self.assertEqual(len(inconsistencias), 2)
        self.assertTrue(all(inc.tipo == TipoInconsistencia.CAPACIDAD_EXCEDIDA for inc in inconsistencias))
        self.assertTrue(all(inc.severidad == SeveridadInconsistencia.ALTA for inc in inconsistencias))
    
    def test_detectar_datos_faltantes(self):
        """Test detección de datos obligatorios faltantes"""
        datos_test = {
            'usuarios': [
                {
                    'id': 1, 'correo_institucional': 'complete@universidad.edu',
                    'nombre': 'Juan', 'apellido': 'Pérez', 'rol': 'estudiante'
                },
                {
                    'id': 2, 'correo_institucional': '',  # Faltante
                    'nombre': 'María', 'apellido': 'García', 'rol': 'estudiante'
                },
                {
                    'id': 3, 'correo_institucional': 'incomplete@universidad.edu',
                    'nombre': '', 'apellido': 'López', 'rol': ''  # Múltiples faltantes
                }
            ]
        }
        
        inconsistencias = self.detector._detectar_datos_faltantes(datos_test)
        
        self.assertGreaterEqual(len(inconsistencias), 3)  # Al menos 3 campos faltantes
        self.assertTrue(all(inc.tipo == TipoInconsistencia.DATOS_FALTANTES for inc in inconsistencias))
        self.assertTrue(all(inc.severidad == SeveridadInconsistencia.MEDIA for inc in inconsistencias))
    
    def test_ejecutar_deteccion_completa(self):
        """Test ejecución completa de detección de inconsistencias"""
        datos_test = {
            'usuarios': [
                {'id': 1, 'correo_institucional': 'test@universidad.edu', 'nombre': 'Juan', 'apellido': 'Pérez', 'rol': 'estudiante'},
                {'id': 2, 'correo_institucional': 'test@universidad.edu', 'nombre': 'María', 'apellido': '', 'rol': 'estudiante'}  # Duplicado + dato faltante
            ],
            'cursos': [],
            'matriculas': [],
            'reservas': [],
            'laboratorios': []
        }
        
        inconsistencias = self.detector.ejecutar_deteccion_completa(datos_test)
        
        self.assertGreater(len(inconsistencias), 0)
        self.assertTrue(any(inc.tipo == TipoInconsistencia.USUARIO_DUPLICADO for inc in inconsistencias))
        self.assertTrue(any(inc.tipo == TipoInconsistencia.DATOS_FALTANTES for inc in inconsistencias))
    
    def test_obtener_resumen_inconsistencias(self):
        """Test obtención de resumen de inconsistencias"""
        # Crear inconsistencias de prueba
        inc1 = InconsistenciaSistema()
        inc1.tipo = TipoInconsistencia.USUARIO_DUPLICADO
        inc1.severidad = SeveridadInconsistencia.ALTA
        
        inc2 = InconsistenciaSistema()
        inc2.tipo = TipoInconsistencia.DATOS_FALTANTES
        inc2.severidad = SeveridadInconsistencia.MEDIA
        
        self.detector.inconsistencias_detectadas = [inc1, inc2]
        
        resumen = self.detector.obtener_resumen_inconsistencias()
        
        self.assertEqual(resumen['total'], 2)
        self.assertEqual(resumen['por_severidad']['alta'], 1)
        self.assertEqual(resumen['por_severidad']['media'], 1)
        self.assertEqual(resumen['por_tipo']['usuario_duplicado'], 1)
        self.assertEqual(resumen['por_tipo']['datos_faltantes'], 1)


class TestGestorAlertas(unittest.TestCase):
    """Tests para el gestor de alertas del sistema"""
    
    def setUp(self):
        self.gestor = GestorAlertas()
    
    def test_crear_alerta_desde_inconsistencia(self):
        """Test creación de alerta desde inconsistencia"""
        inconsistencia = InconsistenciaSistema()
        inconsistencia.id = "inc_001"
        inconsistencia.tipo = TipoInconsistencia.USUARIO_DUPLICADO
        inconsistencia.severidad = SeveridadInconsistencia.ALTA
        inconsistencia.titulo = "Usuario duplicado"
        inconsistencia.descripcion = "Correo duplicado detectado"
        inconsistencia.entidad_afectada = "Usuario"
        inconsistencia.registro_id = "123"
        
        alerta = self.gestor.crear_alerta_desde_inconsistencia(inconsistencia)
        
        self.assertEqual(alerta.tipo, TipoAlerta.INCONSISTENCIA_DETECTADA)
        self.assertEqual(alerta.severidad, SeveridadInconsistencia.ALTA)
        self.assertIn("Usuario duplicado", alerta.titulo)
        self.assertEqual(alerta.entidad_origen, "DetectorInconsistencias")
        self.assertTrue(alerta.notificar_email)
    
    def test_crear_alerta_error_carga(self):
        """Test creación de alerta por error de carga"""
        alerta = self.gestor.crear_alerta_error_carga(
            modulo="TestModule",
            error="Error de conexión a base de datos",
            detalles={'codigo_error': 'DB_001', 'timestamp': datetime.now()}
        )
        
        self.assertEqual(alerta.tipo, TipoAlerta.ERROR_CARGA_DATOS)
        self.assertEqual(alerta.severidad, SeveridadInconsistencia.ALTA)
        self.assertIn("TestModule", alerta.titulo)
        self.assertEqual(alerta.entidad_origen, "TestModule")
        self.assertTrue(alerta.notificar_email)
        self.assertEqual(alerta.impacto_estimado, "alto")
    
    def test_crear_alerta_rendimiento(self):
        """Test creación de alerta por degradación de rendimiento"""
        alerta = self.gestor.crear_alerta_rendimiento(
            metrica="tiempo_respuesta_db",
            valor_actual=250.0,
            umbral=200.0
        )
        
        self.assertEqual(alerta.tipo, TipoAlerta.RENDIMIENTO_DEGRADADO)
        self.assertEqual(alerta.severidad, SeveridadInconsistencia.MEDIA)
        self.assertIn("tiempo_respuesta_db", alerta.titulo)
        self.assertEqual(alerta.entidad_origen, "MonitorRendimiento")
        self.assertIn("250", alerta.descripcion)
        self.assertIn("200", alerta.descripcion)
    
    def test_agregar_alerta_duplicada(self):
        """Test manejo de alertas duplicadas"""
        # Configurar para auto-resolver duplicadas
        self.gestor.configuracion['auto_resolver_duplicadas'] = True
        
        alerta1 = AlertaSistema()
        alerta1.tipo = TipoAlerta.ERROR_CARGA_DATOS
        alerta1.titulo = "Error de prueba"
        alerta1.entidad_origen = "TestModule"
        alerta1.estado = EstadoAlerta.ACTIVA
        alerta1.veces_ocurrida = 1
        
        alerta2 = AlertaSistema()
        alerta2.tipo = TipoAlerta.ERROR_CARGA_DATOS
        alerta2.titulo = "Error de prueba"
        alerta2.entidad_origen = "TestModule"
        alerta2.estado = EstadoAlerta.ACTIVA
        alerta2.veces_ocurrida = 1
        
        # Agregar primera alerta
        resultado1 = self.gestor.agregar_alerta(alerta1)
        self.assertTrue(resultado1)
        self.assertEqual(len(self.gestor.alertas), 1)
        
        # Agregar alerta duplicada
        resultado2 = self.gestor.agregar_alerta(alerta2)
        self.assertFalse(resultado2)  # No se agrega, se incrementa la existente
        self.assertEqual(len(self.gestor.alertas), 1)
        self.assertEqual(self.gestor.alertas[0].veces_ocurrida, 2)
    
    def test_obtener_alertas_por_severidad(self):
        """Test filtrado de alertas por severidad"""
        # Crear alertas de diferentes severidades
        alerta_critica = AlertaSistema()
        alerta_critica.severidad = SeveridadInconsistencia.CRITICA
        alerta_critica.estado = EstadoAlerta.ACTIVA
        
        alerta_media = AlertaSistema()
        alerta_media.severidad = SeveridadInconsistencia.MEDIA
        alerta_media.estado = EstadoAlerta.ACTIVA
        
        alerta_resuelta = AlertaSistema()
        alerta_resuelta.severidad = SeveridadInconsistencia.CRITICA
        alerta_resuelta.estado = EstadoAlerta.RESUELTA
        
        self.gestor.alertas = [alerta_critica, alerta_media, alerta_resuelta]
        
        alertas_criticas = self.gestor.obtener_alertas_por_severidad(SeveridadInconsistencia.CRITICA)
        
        self.assertEqual(len(alertas_criticas), 1)  # Solo la activa
        self.assertEqual(alertas_criticas[0].severidad, SeveridadInconsistencia.CRITICA)
        self.assertEqual(alertas_criticas[0].estado, EstadoAlerta.ACTIVA)
    
    def test_obtener_resumen_alertas(self):
        """Test obtención de resumen de alertas"""
        # Crear alertas de prueba
        alerta1 = AlertaSistema()
        alerta1.severidad = SeveridadInconsistencia.CRITICA
        alerta1.tipo = TipoAlerta.ERROR_CARGA_DATOS
        alerta1.estado = EstadoAlerta.ACTIVA
        alerta1.fecha_creacion = datetime.now()
        
        alerta2 = AlertaSistema()
        alerta2.severidad = SeveridadInconsistencia.MEDIA
        alerta2.tipo = TipoAlerta.RENDIMIENTO_DEGRADADO
        alerta2.estado = EstadoAlerta.ACTIVA
        alerta2.fecha_creacion = datetime.now() - timedelta(hours=2)
        
        self.gestor.alertas = [alerta1, alerta2]
        
        resumen = self.gestor.obtener_resumen_alertas()
        
        self.assertEqual(resumen['total_activas'], 2)
        self.assertEqual(resumen['por_severidad']['critica'], 1)
        self.assertEqual(resumen['por_severidad']['media'], 1)
        self.assertEqual(resumen['por_tipo']['error_carga_datos'], 1)
        self.assertEqual(resumen['por_tipo']['rendimiento_degradado'], 1)
        self.assertGreaterEqual(len(resumen['alertas_recientes']), 1)
    
    def test_resolver_alerta(self):
        """Test resolución de alerta"""
        alerta = AlertaSistema()
        alerta.id = "alerta_001"
        alerta.estado = EstadoAlerta.ACTIVA
        
        self.gestor.alertas = [alerta]
        
        resultado = self.gestor.resolver_alerta(
            alerta_id="alerta_001",
            usuario="admin_test",
            accion="Problema corregido",
            notas="Se reinició el servicio"
        )
        
        self.assertTrue(resultado)
        self.assertEqual(alerta.estado, EstadoAlerta.RESUELTA)
        self.assertEqual(alerta.usuario_resolucion, "admin_test")
        self.assertEqual(alerta.accion_correctiva, "Problema corregido")
        self.assertEqual(alerta.notas_resolucion, "Se reinició el servicio")
        self.assertIsNotNone(alerta.fecha_resolucion)


class TestSistemaAuditoria(unittest.TestCase):
    """Tests para el sistema de auditoría"""
    
    def setUp(self):
        self.sistema = SistemaAuditoria()
    
    def test_registrar_accion_basica(self):
        """Test registro básico de acción"""
        registro = self.sistema.registrar_accion(
            usuario_id="user_001",
            usuario_nombre="Juan Pérez",
            usuario_rol="admin",
            accion=TipoAccionAuditoria.USUARIO_ACTIVADO,
            descripcion="Usuario activado correctamente",
            entidad_afectada="Usuario",
            entidad_id="123"
        )
        
        self.assertIsNotNone(registro.timestamp)
        self.assertEqual(registro.usuario_id, "user_001")
        self.assertEqual(registro.usuario_nombre, "Juan Pérez")
        self.assertEqual(registro.accion, TipoAccionAuditoria.USUARIO_ACTIVADO)
        self.assertEqual(registro.entidad_afectada, "Usuario")
        self.assertEqual(registro.entidad_id, "123")
        self.assertTrue(registro.exitoso)
        self.assertEqual(len(self.sistema.registros), 1)
    
    def test_registrar_login_admin_exitoso(self):
        """Test registro de login administrativo exitoso"""
        registro = self.sistema.registrar_login_admin(
            usuario_id="admin_001",
            usuario_nombre="Admin Test",
            ip="192.168.1.100",
            exitoso=True
        )
        
        self.assertEqual(registro.accion, TipoAccionAuditoria.LOGIN_ADMIN)
        self.assertTrue(registro.exitoso)
        self.assertEqual(registro.ip_address, "192.168.1.100")
        self.assertNotIn("seguridad", registro.tags)
    
    def test_registrar_login_admin_fallido(self):
        """Test registro de login administrativo fallido"""
        registro = self.sistema.registrar_login_admin(
            usuario_id="admin_001",
            usuario_nombre="Admin Test",
            ip="192.168.1.100",
            exitoso=False,
            error="Credenciales inválidas"
        )
        
        self.assertEqual(registro.accion, TipoAccionAuditoria.ACCESO_DENEGADO)
        self.assertFalse(registro.exitoso)
        self.assertEqual(registro.mensaje_error, "Credenciales inválidas")
        self.assertEqual(registro.nivel, NivelAuditoria.ALTO)
        self.assertIn("seguridad", registro.tags)
    
    def test_registrar_cambio_usuario(self):
        """Test registro de cambio en usuario"""
        datos_anteriores = {'activo': False, 'rol': 'estudiante'}
        datos_nuevos = {'activo': True, 'rol': 'estudiante'}
        
        registro = self.sistema.registrar_cambio_usuario(
            admin_id="admin_001",
            admin_nombre="Admin Test",
            usuario_afectado_id="user_123",
            accion=TipoAccionAuditoria.USUARIO_ACTIVADO,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos
        )
        
        self.assertEqual(registro.accion, TipoAccionAuditoria.USUARIO_ACTIVADO)
        self.assertEqual(registro.entidad_afectada, "Usuario")
        self.assertEqual(registro.entidad_id, "user_123")
        self.assertEqual(registro.datos_anteriores, datos_anteriores)
        self.assertEqual(registro.datos_nuevos, datos_nuevos)
        
        cambios = registro.obtener_cambios_realizados()
        self.assertIn('activo', cambios)
        self.assertEqual(cambios['activo']['anterior'], False)
        self.assertEqual(cambios['activo']['nuevo'], True)
    
    def test_obtener_registros_usuario(self):
        """Test obtención de registros por usuario"""
        # Crear registros de diferentes usuarios
        self.sistema.registrar_accion("user_001", "Usuario 1", "admin", TipoAccionAuditoria.LOGIN_ADMIN, "Login 1")
        self.sistema.registrar_accion("user_002", "Usuario 2", "admin", TipoAccionAuditoria.LOGIN_ADMIN, "Login 2")
        self.sistema.registrar_accion("user_001", "Usuario 1", "admin", TipoAccionAuditoria.LOGOUT_ADMIN, "Logout 1")
        
        registros_user1 = self.sistema.obtener_registros_usuario("user_001")
        
        self.assertEqual(len(registros_user1), 2)
        self.assertTrue(all(r.usuario_id == "user_001" for r in registros_user1))
        # Verificar orden descendente por timestamp
        self.assertGreaterEqual(registros_user1[0].timestamp, registros_user1[1].timestamp)
    
    def test_obtener_estadisticas_auditoria(self):
        """Test obtención de estadísticas de auditoría"""
        # Crear registros de prueba
        fecha_base = datetime.now() - timedelta(days=5)
        
        # Registro exitoso
        registro1 = self.sistema.registrar_accion(
            "user_001", "Usuario 1", "admin", TipoAccionAuditoria.USUARIO_ACTIVADO, "Activación"
        )
        registro1.timestamp = fecha_base
        
        # Registro con error
        registro2 = self.sistema.registrar_accion(
            "user_002", "Usuario 2", "admin", TipoAccionAuditoria.REPORTE_GENERADO, "Error en reporte"
        )
        registro2.timestamp = fecha_base + timedelta(days=1)
        registro2.exitoso = False
        
        # Registro crítico
        registro3 = self.sistema.registrar_accion(
            "user_001", "Usuario 1", "admin", TipoAccionAuditoria.CONFIGURACION_MODIFICADA, "Config crítica"
        )
        registro3.timestamp = fecha_base + timedelta(days=2)
        registro3.nivel = NivelAuditoria.CRITICO
        
        estadisticas = self.sistema.obtener_estadisticas_auditoria(dias=7)
        
        self.assertEqual(estadisticas['total_acciones'], 3)
        self.assertEqual(estadisticas['errores_detectados'], 1)
        self.assertEqual(estadisticas['acciones_criticas'], 1)
        self.assertIn('usuarios_mas_activos', estadisticas)
        self.assertIn('acciones_por_tipo', estadisticas)
        self.assertIn('acciones_por_nivel', estadisticas)
    
    def test_buscar_registros_con_filtros(self):
        """Test búsqueda de registros con filtros"""
        # Crear registros de prueba
        fecha_inicio = datetime.now() - timedelta(days=2)
        fecha_fin = datetime.now() - timedelta(days=1)
        
        registro1 = self.sistema.registrar_accion(
            "user_001", "Usuario Test", "admin", TipoAccionAuditoria.USUARIO_ACTIVADO, "Activación usuario"
        )
        registro1.timestamp = fecha_inicio + timedelta(hours=12)
        
        registro2 = self.sistema.registrar_accion(
            "user_002", "Otro Usuario", "admin", TipoAccionAuditoria.REPORTE_GENERADO, "Generación reporte"
        )
        registro2.timestamp = fecha_fin + timedelta(hours=12)  # Fuera del rango
        
        filtros = {
            'usuario_id': 'user_001',
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'texto': 'usuario'
        }
        
        resultados = self.sistema.buscar_registros(filtros)
        
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].usuario_id, "user_001")
        self.assertIn("usuario", resultados[0].descripcion.lower())


class TestMonitorRendimiento(unittest.TestCase):
    """Tests para el monitor de rendimiento"""
    
    def setUp(self):
        self.monitor = MonitorRendimiento()
    
    def test_inicializacion_metricas(self):
        """Test inicialización correcta de métricas"""
        self.assertGreater(len(self.monitor.metricas), 0)
        
        # Verificar que existen métricas clave
        self.assertIn('tiempo_respuesta_db', self.monitor.metricas)
        self.assertIn('memoria_utilizada', self.monitor.metricas)
        self.assertIn('cpu_utilizada', self.monitor.metricas)
        
        # Verificar configuración de umbrales
        metrica_db = self.monitor.metricas['tiempo_respuesta_db']
        self.assertGreater(metrica_db.umbral_critico, metrica_db.umbral_degradado)
        self.assertGreater(metrica_db.umbral_degradado, metrica_db.umbral_bueno)
        self.assertGreater(metrica_db.umbral_bueno, metrica_db.umbral_optimo)
    
    def test_actualizar_metrica(self):
        """Test actualización de métrica individual"""
        valor_inicial = 75.5
        self.monitor.actualizar_metrica('memoria_utilizada', valor_inicial)
        
        metrica = self.monitor.metricas['memoria_utilizada']
        self.assertEqual(metrica.valor_actual, valor_inicial)
        self.assertIsNotNone(metrica.timestamp)
        self.assertEqual(len(metrica.valores_historicos), 1)
        
        # Verificar cálculo de estado
        if valor_inicial <= metrica.umbral_optimo:
            self.assertEqual(metrica.estado, EstadoRendimiento.OPTIMO)
        elif valor_inicial <= metrica.umbral_bueno:
            self.assertEqual(metrica.estado, EstadoRendimiento.BUENO)
        elif valor_inicial <= metrica.umbral_degradado:
            self.assertEqual(metrica.estado, EstadoRendimiento.DEGRADADO)
        else:
            self.assertEqual(metrica.estado, EstadoRendimiento.CRITICO)
    
    def test_metricas_en_alerta(self):
        """Test detección de métricas en estado de alerta"""
        # Configurar métricas en diferentes estados
        self.monitor.actualizar_metrica('memoria_utilizada', 95)  # Crítico
        self.monitor.actualizar_metrica('cpu_utilizada', 80)      # Degradado
        self.monitor.actualizar_metrica('tiempo_respuesta_db', 30) # Óptimo
        
        alertas = self.monitor.obtener_metricas_en_alerta()
        
        self.assertGreaterEqual(len(alertas), 2)  # Al menos memoria y CPU
        
        # Verificar que las métricas en alerta están correctamente identificadas
        tipos_en_alerta = [alerta['tipo'] for alerta in alertas]
        self.assertIn('memoria_utilizada', tipos_en_alerta)
        self.assertIn('cpu_utilizada', tipos_en_alerta)
        self.assertNotIn('tiempo_respuesta_db', tipos_en_alerta)
    
    def test_obtener_metricas_dashboard(self):
        """Test obtención de métricas para dashboard"""
        # Actualizar algunas métricas
        self.monitor.actualizar_metrica('tiempo_respuesta_db', 120)
        self.monitor.actualizar_metrica('memoria_utilizada', 65)
        
        metricas_dashboard = self.monitor.obtener_metricas_dashboard()
        
        self.assertIsInstance(metricas_dashboard, list)
        self.assertLessEqual(len(metricas_dashboard), self.monitor.configuracion['max_metricas_dashboard'])
        
        # Verificar estructura de cada métrica
        for metrica in metricas_dashboard:
            self.assertIn('tipo', metrica)
            self.assertIn('nombre', metrica)
            self.assertIn('valor', metrica)
            self.assertIn('unidad', metrica)
            self.assertIn('estado', metrica)
            self.assertIn('color', metrica)
            self.assertIn('tendencia', metrica)
    
    def test_calcular_tendencia(self):
        """Test cálculo de tendencia de métricas"""
        metrica = self.monitor.metricas['tiempo_respuesta_db']
        
        # Simular valores que mejoran
        metrica.actualizar_valor(100)
        metrica.actualizar_valor(80)
        metrica.actualizar_valor(60)
        
        self.assertEqual(metrica.tendencia, "mejorando")
        
        # Simular valores que empeoran
        metrica.valores_historicos.clear()
        metrica.actualizar_valor(50)
        metrica.actualizar_valor(70)
        metrica.actualizar_valor(90)
        
        self.assertEqual(metrica.tendencia, "empeorando")
    
    def test_resumen_rendimiento(self):
        """Test obtención de resumen general de rendimiento"""
        # Configurar métricas en diferentes estados
        self.monitor.actualizar_metrica('memoria_utilizada', 45)   # Óptimo
        self.monitor.actualizar_metrica('cpu_utilizada', 60)       # Bueno
        self.monitor.actualizar_metrica('tiempo_respuesta_db', 180) # Degradado
        
        resumen = self.monitor.obtener_resumen_rendimiento()
        
        self.assertIn('estado_general', resumen)
        self.assertIn('porcentaje_saludable', resumen)
        self.assertIn('metricas_por_estado', resumen)
        self.assertIn('total_metricas', resumen)
        self.assertIn('metricas_en_alerta', resumen)
        
        # Verificar cálculos
        self.assertGreaterEqual(resumen['porcentaje_saludable'], 0)
        self.assertLessEqual(resumen['porcentaje_saludable'], 100)
        self.assertEqual(resumen['total_metricas'], len(self.monitor.metricas))
    
    def test_medidor_tiempo_context_manager(self):
        """Test del context manager para medir tiempo"""
        import time
        
        with self.monitor.medir_tiempo_operacion('dashboard_load') as medidor:
            time.sleep(0.1)  # Simular operación
        
        duracion = medidor.obtener_duracion_ms()
        self.assertGreaterEqual(duracion, 100)  # Al menos 100ms
        
        # Verificar que se actualizó la métrica correspondiente
        metrica_dashboard = self.monitor.metricas.get('tiempo_carga_dashboard')
        if metrica_dashboard:
            self.assertGreater(metrica_dashboard.valor_actual, 0)


class TestServicioMonitoreo(unittest.TestCase):
    """Tests para el servicio de monitoreo integrado"""
    
    def setUp(self):
        self.servicio = ServicioMonitoreo()
    
    def test_inicializacion_servicio(self):
        """Test inicialización correcta del servicio"""
        self.assertIsNotNone(self.servicio.detector_inconsistencias)
        self.assertIsNotNone(self.servicio.gestor_alertas)
        self.assertIsNotNone(self.servicio.sistema_auditoria)
        self.assertIsNotNone(self.servicio.monitor_rendimiento)
        
        self.assertFalse(self.servicio.deteccion_en_progreso)
        self.assertIsNone(self.servicio.ultima_deteccion)
    
    @patch('servicios.servicioMonitoreo.ServicioMonitoreo._recopilar_datos_sistema')
    def test_ejecutar_deteccion_completa(self, mock_recopilar):
        """Test ejecución completa de detección"""
        # Mock de datos del sistema
        mock_recopilar.return_value = {
            'usuarios': [
                {'id': 1, 'correo_institucional': 'test@universidad.edu', 'nombre': 'Test', 'apellido': 'User', 'rol': 'estudiante'},
                {'id': 2, 'correo_institucional': 'test@universidad.edu', 'nombre': 'Test2', 'apellido': 'User2', 'rol': 'estudiante'}  # Duplicado
            ],
            'cursos': [],
            'matriculas': [],
            'reservas': [],
            'laboratorios': []
        }
        
        resultado = self.servicio.ejecutar_deteccion_completa()
        
        self.assertNotIn('error', resultado)
        self.assertIn('total_inconsistencias', resultado)
        self.assertIn('estado_deteccion', resultado)
        self.assertEqual(resultado['estado_deteccion'], 'completado')
        self.assertIsNotNone(self.servicio.ultima_deteccion)
        
        # Verificar que se generaron alertas
        alertas_activas = self.servicio.gestor_alertas.obtener_alertas_activas()
        self.assertGreater(len(alertas_activas), 0)
    
    def test_obtener_estado_sistema(self):
        """Test obtención del estado completo del sistema"""
        estado = self.servicio.obtener_estado_sistema()
        
        self.assertIn('timestamp', estado)
        self.assertIn('estado_general', estado)
        self.assertIn('alertas', estado)
        self.assertIn('inconsistencias', estado)
        self.assertIn('rendimiento', estado)
        self.assertIn('auditoria', estado)
        
        # Verificar estructura de alertas
        self.assertIn('total_activas', estado['alertas'])
        self.assertIn('criticas', estado['alertas'])
        
        # Verificar estructura de inconsistencias
        self.assertIn('total_activas', estado['inconsistencias'])
        self.assertIn('por_severidad', estado['inconsistencias'])
        
        # Verificar estructura de rendimiento
        self.assertIn('estado_general', estado['rendimiento'])
        self.assertIn('porcentaje_saludable', estado['rendimiento'])
    
    def test_registrar_accion_administrativa(self):
        """Test registro de acción administrativa"""
        registro = self.servicio.registrar_accion_administrativa(
            usuario_id="admin_001",
            usuario_nombre="Admin Test",
            accion="usuario_activado",
            descripcion="Usuario activado correctamente",
            entidad_afectada="Usuario",
            entidad_id="123",
            contexto_request={'ip': '192.168.1.100'}
        )
        
        self.assertIsNotNone(registro)
        self.assertEqual(registro.usuario_id, "admin_001")
        self.assertEqual(registro.descripcion, "Usuario activado correctamente")
        self.assertEqual(registro.ip_address, "192.168.1.100")
        
        # Verificar que se agregó al sistema de auditoría
        registros = self.servicio.sistema_auditoria.obtener_registros_usuario("admin_001")
        self.assertEqual(len(registros), 1)
    
    def test_resolver_alerta(self):
        """Test resolución de alerta"""
        # Crear una alerta de prueba
        alerta = AlertaSistema()
        alerta.id = "test_alerta_001"
        alerta.estado = EstadoAlerta.ACTIVA
        alerta.titulo = "Alerta de prueba"
        
        self.servicio.gestor_alertas.alertas.append(alerta)
        
        resultado = self.servicio.resolver_alerta(
            alerta_id="test_alerta_001",
            usuario="admin_test",
            accion="Problema resuelto",
            notas="Se corrigió el error"
        )
        
        self.assertTrue(resultado)
        self.assertEqual(alerta.estado, EstadoAlerta.RESUELTA)
        
        # Verificar que se registró en auditoría
        registros = self.servicio.sistema_auditoria.obtener_registros_usuario("admin_test")
        self.assertGreater(len(registros), 0)
    
    def test_obtener_alertas_dashboard(self):
        """Test obtención de alertas para dashboard"""
        # Crear alertas de prueba
        alerta1 = AlertaSistema()
        alerta1.id = "alerta_001"
        alerta1.tipo = TipoAlerta.ERROR_CARGA_DATOS
        alerta1.titulo = "Error crítico"
        alerta1.severidad = SeveridadInconsistencia.CRITICA
        alerta1.estado = EstadoAlerta.ACTIVA
        alerta1.fecha_creacion = datetime.now()
        
        alerta2 = AlertaSistema()
        alerta2.id = "alerta_002"
        alerta2.tipo = TipoAlerta.RENDIMIENTO_DEGRADADO
        alerta2.titulo = "Rendimiento degradado"
        alerta2.severidad = SeveridadInconsistencia.MEDIA
        alerta2.estado = EstadoAlerta.ACTIVA
        alerta2.fecha_creacion = datetime.now() - timedelta(minutes=30)
        
        self.servicio.gestor_alertas.alertas = [alerta1, alerta2]
        
        alertas_dashboard = self.servicio.obtener_alertas_dashboard(limite=5)
        
        self.assertLessEqual(len(alertas_dashboard), 5)
        self.assertGreater(len(alertas_dashboard), 0)
        
        # Verificar estructura de respuesta
        for alerta in alertas_dashboard:
            self.assertIn('id', alerta)
            self.assertIn('tipo', alerta)
            self.assertIn('titulo', alerta)
            self.assertIn('severidad', alerta)
            self.assertIn('tiempo_transcurrido', alerta)
    
    def test_obtener_historial_auditoria(self):
        """Test obtención de historial de auditoría"""
        # Crear registros de prueba
        self.servicio.sistema_auditoria.registrar_accion(
            "user_001", "Usuario 1", "admin", TipoAccionAuditoria.LOGIN_ADMIN, "Login exitoso"
        )
        self.servicio.sistema_auditoria.registrar_accion(
            "user_002", "Usuario 2", "admin", TipoAccionAuditoria.USUARIO_ACTIVADO, "Usuario activado"
        )
        
        historial = self.servicio.obtener_historial_auditoria(limite=10)
        
        self.assertLessEqual(len(historial), 10)
        self.assertGreater(len(historial), 0)
        
        # Verificar estructura de respuesta
        for registro in historial:
            self.assertIn('id', registro)
            self.assertIn('timestamp', registro)
            self.assertIn('usuario', registro)
            self.assertIn('accion', registro)
            self.assertIn('descripcion', registro)
    
    def test_simular_metricas_rendimiento(self):
        """Test simulación de métricas de rendimiento"""
        # Obtener estado inicial
        estado_inicial = self.servicio.monitor_rendimiento.obtener_resumen_rendimiento()
        
        # Simular métricas
        self.servicio.simular_metricas_rendimiento()
        
        # Verificar que se actualizaron las métricas
        estado_final = self.servicio.monitor_rendimiento.obtener_resumen_rendimiento()
        
        self.assertIsNotNone(self.servicio.monitor_rendimiento.ultima_medicion)
        
        # Verificar que al menos algunas métricas tienen valores
        metricas_dashboard = self.servicio.monitor_rendimiento.obtener_metricas_dashboard()
        valores_actualizados = [m for m in metricas_dashboard if m['valor'] > 0]
        self.assertGreater(len(valores_actualizados), 0)


if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)