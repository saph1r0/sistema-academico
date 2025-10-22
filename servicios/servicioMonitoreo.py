#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
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
    from dominio.modelo.admin_sistema.metricas_sistema import MetricasSistema
except ImportError as e:
    # Fallback para cuando no se pueden importar las dependencias
    print(f"Warning: Could not import monitoring dependencies: {e}")
    DetectorInconsistencias = None
    GestorAlertas = None
    SistemaAuditoria = None
    MonitorRendimiento = None

import logging


class ServicioMonitoreo:
    """
    Servicio de monitoreo global del sistema administrativo.
    Coordina la detección de inconsistencias, gestión de alertas, 
    auditoría y métricas de rendimiento.
    """
    
    def __init__(self, usuario_repository=None, curso_repository=None, 
                 matricula_repository=None, reserva_repository=None, laboratorio_repository=None):
        
        # Inicializar componentes si están disponibles
        if DetectorInconsistencias:
            self.detector_inconsistencias = DetectorInconsistencias()
        else:
            self.detector_inconsistencias = None
            
        if GestorAlertas:
            self.gestor_alertas = GestorAlertas()
        else:
            self.gestor_alertas = None
            
        if SistemaAuditoria:
            self.sistema_auditoria = SistemaAuditoria()
        else:
            self.sistema_auditoria = None
            
        if MonitorRendimiento:
            self.monitor_rendimiento = MonitorRendimiento()
        else:
            self.monitor_rendimiento = None
        
        # Repositorios para acceso a datos
        self.usuario_repository = usuario_repository
        self.curso_repository = curso_repository
        self.matricula_repository = matricula_repository
        self.reserva_repository = reserva_repository
        self.laboratorio_repository = laboratorio_repository
        
        # Logger específico para monitoreo
        self.logger = logging.getLogger('admin_panel.monitoreo')
        
        # Configuración del servicio
        self.configuracion = {
            'deteccion_automatica_activa': True,
            'intervalo_deteccion_minutos': 30,
            'generar_alertas_automaticas': True,
            'log_todas_las_acciones': True,
            'monitoreo_rendimiento_activo': True
        }
        
        # Estado del servicio
        self.ultima_deteccion = None
        self.deteccion_en_progreso = False
    
    def ejecutar_deteccion_completa(self) -> Dict[str, Any]:
        """
        Ejecuta una detección completa de inconsistencias en el sistema.
        Retorna un resumen de las inconsistencias encontradas.
        """
        if not self.detector_inconsistencias:
            return {'error': 'Detector de inconsistencias no disponible'}
            
        if self.deteccion_en_progreso:
            return {'error': 'Detección ya en progreso'}
        
        try:
            self.deteccion_en_progreso = True
            self.logger.info("Iniciando detección completa de inconsistencias")
            
            # Recopilar datos del sistema
            datos_sistema = self._recopilar_datos_sistema()
            
            # Ejecutar detección
            inconsistencias = self.detector_inconsistencias.ejecutar_deteccion_completa(datos_sistema)
            
            # Generar alertas automáticas
            if self.configuracion['generar_alertas_automaticas'] and self.gestor_alertas:
                self._generar_alertas_desde_inconsistencias(inconsistencias)
            
            # Registrar en auditoría
            if self.sistema_auditoria:
                self.sistema_auditoria.registrar_accion(
                    usuario_id="sistema",
                    usuario_nombre="Sistema Automático",
                    usuario_rol="sistema",
                    accion=TipoAccionAuditoria.DETECCION_INCONSISTENCIAS,
                    descripcion=f"Detección automática completada: {len(inconsistencias)} inconsistencias encontradas",
                    modulo_origen="ServicioMonitoreo"
                )
            
            self.ultima_deteccion = datetime.now()
            
            # Preparar resumen
            resumen = self._generar_resumen_deteccion(inconsistencias)
            
            self.logger.info(f"Detección completada: {len(inconsistencias)} inconsistencias encontradas")
            return resumen
            
        except Exception as e:
            self.logger.error(f"Error en detección de inconsistencias: {str(e)}")
            
            # Crear alerta por error del sistema
            if self.gestor_alertas:
                alerta_error = self.gestor_alertas.crear_alerta_error_carga(
                    "ServicioMonitoreo", 
                    f"Error en detección de inconsistencias: {str(e)}"
                )
                self.gestor_alertas.agregar_alerta(alerta_error)
            
            return {'error': str(e)}
        
        finally:
            self.deteccion_en_progreso = False
    
    def obtener_estado_sistema(self) -> Dict[str, Any]:
        """
        Obtiene el estado general del sistema incluyendo alertas,
        inconsistencias y métricas de rendimiento.
        """
        try:
            # Obtener alertas activas
            alertas_activas = []
            alertas_criticas = []
            if self.gestor_alertas:
                alertas_activas = self.gestor_alertas.obtener_alertas_activas()
                alertas_criticas = self.gestor_alertas.obtener_alertas_criticas()
            
            # Obtener inconsistencias no resueltas
            inconsistencias_activas = []
            if self.detector_inconsistencias:
                inconsistencias_activas = [
                    inc for inc in self.detector_inconsistencias.inconsistencias_detectadas
                    if not inc.resuelto
                ]
            
            # Obtener métricas de rendimiento
            metricas_dashboard = []
            resumen_rendimiento = {'estado_general': 'desconocido', 'porcentaje_saludable': 0, 'metricas_en_alerta': 0}
            if self.monitor_rendimiento:
                metricas_dashboard = self.monitor_rendimiento.obtener_metricas_dashboard()
                resumen_rendimiento = self.monitor_rendimiento.obtener_resumen_rendimiento()
            
            # Obtener estadísticas de auditoría
            estadisticas_auditoria = {'total_acciones': 0, 'errores_detectados': 0, 'acciones_criticas': 0}
            if self.sistema_auditoria:
                estadisticas_auditoria = self.sistema_auditoria.obtener_estadisticas_auditoria(7)
            
            estado = {
                'timestamp': datetime.now().isoformat(),
                'estado_general': self._calcular_estado_general(),
                'alertas': {
                    'total_activas': len(alertas_activas),
                    'criticas': len(alertas_criticas),
                    'resumen': self.gestor_alertas.obtener_resumen_alertas() if self.gestor_alertas else {}
                },
                'inconsistencias': {
                    'total_activas': len(inconsistencias_activas),
                    'por_severidad': self._contar_inconsistencias_por_severidad(inconsistencias_activas),
                    'ultima_deteccion': self.ultima_deteccion.isoformat() if self.ultima_deteccion else None
                },
                'rendimiento': {
                    'estado_general': resumen_rendimiento['estado_general'],
                    'porcentaje_saludable': resumen_rendimiento['porcentaje_saludable'],
                    'metricas_en_alerta': resumen_rendimiento['metricas_en_alerta'],
                    'metricas_principales': metricas_dashboard[:4]  # Top 4 para dashboard
                },
                'auditoria': {
                    'acciones_ultima_semana': estadisticas_auditoria['total_acciones'],
                    'errores_detectados': estadisticas_auditoria['errores_detectados'],
                    'acciones_criticas': estadisticas_auditoria['acciones_criticas']
                }
            }
            
            return estado
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estado del sistema: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'estado_general': 'error'
            }
    
    def obtener_alertas_dashboard(self, limite: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene las alertas más importantes para mostrar en el dashboard.
        """
        if not self.gestor_alertas:
            return []
            
        alertas_dashboard = self.gestor_alertas.obtener_alertas_dashboard(limite)
        
        return [
            {
                'id': alerta.id,
                'tipo': alerta.tipo.value if alerta.tipo else 'desconocido',
                'titulo': alerta.titulo,
                'descripcion': alerta.descripcion,
                'severidad': alerta.severidad.value if alerta.severidad else 'media',
                'tiempo_transcurrido': alerta.obtener_tiempo_transcurrido() if hasattr(alerta, 'obtener_tiempo_transcurrido') else 'Desconocido',
                'entidad_origen': alerta.entidad_origen
            }
            for alerta in alertas_dashboard
        ]
    
    def obtener_metricas_rendimiento_dashboard(self) -> Dict[str, Any]:
        """
        Obtiene las métricas de rendimiento para el dashboard.
        """
        if not self.monitor_rendimiento:
            return {
                'estado_general': 'desconocido',
                'porcentaje_saludable': 0,
                'metricas': [],
                'alertas_rendimiento': []
            }
            
        metricas = self.monitor_rendimiento.obtener_metricas_dashboard()
        resumen = self.monitor_rendimiento.obtener_resumen_rendimiento()
        
        return {
            'estado_general': resumen['estado_general'],
            'porcentaje_saludable': resumen['porcentaje_saludable'],
            'metricas': metricas,
            'alertas_rendimiento': self.monitor_rendimiento.obtener_metricas_en_alerta()
        }
    
    def registrar_accion_administrativa(self, usuario_id: str, usuario_nombre: str, 
                                      accion: str, descripcion: str, 
                                      entidad_afectada: str = "", entidad_id: str = None,
                                      datos_anteriores: Dict = None, datos_nuevos: Dict = None,
                                      contexto_request: Dict = None) -> Optional[Any]:
        """
        Registra una acción administrativa en el sistema de auditoría.
        """
        if not self.sistema_auditoria:
            return None
            
        try:
            # Mapear string de acción a enum
            accion_enum = self._mapear_accion_string_a_enum(accion)
            
            registro = self.sistema_auditoria.registrar_accion(
                usuario_id=usuario_id,
                usuario_nombre=usuario_nombre,
                usuario_rol="admin",
                accion=accion_enum,
                descripcion=descripcion,
                entidad_afectada=entidad_afectada,
                entidad_id=entidad_id,
                modulo_origen="AdminPanel",
                datos_anteriores=datos_anteriores,
                datos_nuevos=datos_nuevos,
                contexto_request=contexto_request
            )
            
            self.logger.info(f"Acción registrada: {usuario_nombre} - {accion} - {descripcion}")
            return registro
            
        except Exception as e:
            self.logger.error(f"Error registrando acción administrativa: {str(e)}")
            raise
    
    def resolver_alerta(self, alerta_id: str, usuario: str, accion: str = "", notas: str = "") -> bool:
        """
        Resuelve una alerta específica y registra la acción.
        """
        if not self.gestor_alertas:
            return False
            
        try:
            # Resolver la alerta
            resultado = self.gestor_alertas.resolver_alerta(alerta_id, usuario, accion, notas)
            
            if resultado and self.sistema_auditoria:
                # Registrar en auditoría
                self.sistema_auditoria.registrar_accion(
                    usuario_id=usuario,
                    usuario_nombre=usuario,
                    usuario_rol="admin",
                    accion=TipoAccionAuditoria.ALERTA_RESUELTA,
                    descripcion=f"Alerta {alerta_id} resuelta",
                    entidad_afectada="Alerta",
                    entidad_id=alerta_id,
                    modulo_origen="AdminPanel",
                    datos_nuevos={'accion_correctiva': accion, 'notas': notas}
                )
                
                self.logger.info(f"Alerta {alerta_id} resuelta por {usuario}")
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error resolviendo alerta {alerta_id}: {str(e)}")
            return False
    
    def obtener_historial_auditoria(self, filtros: Dict[str, Any] = None, limite: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de auditoría con filtros opcionales.
        """
        if not self.sistema_auditoria:
            return []
            
        try:
            registros = self.sistema_auditoria.buscar_registros(filtros or {}, limite)
            
            return [
                {
                    'id': registro.id,
                    'timestamp': registro.timestamp.isoformat() if registro.timestamp else None,
                    'usuario': registro.usuario_nombre,
                    'accion': registro.accion.value if registro.accion else None,
                    'descripcion': registro.descripcion,
                    'entidad_afectada': registro.entidad_afectada,
                    'entidad_id': registro.entidad_id,
                    'nivel': registro.nivel.value if registro.nivel else None,
                    'exitoso': registro.exitoso,
                    'ip_address': registro.ip_address
                }
                for registro in registros
            ]
            
        except Exception as e:
            self.logger.error(f"Error obteniendo historial de auditoría: {str(e)}")
            return []
    
    def simular_metricas_rendimiento(self):
        """
        Simula métricas de rendimiento para testing/demo.
        """
        if self.monitor_rendimiento:
            self.monitor_rendimiento.simular_medicion_sistema()
    
    def _recopilar_datos_sistema(self) -> Dict[str, Any]:
        """
        Recopila datos del sistema desde los repositorios.
        """
        datos = {
            'usuarios': [],
            'cursos': [],
            'matriculas': [],
            'reservas': [],
            'laboratorios': []
        }
        
        try:
            # Recopilar usuarios
            if self.usuario_repository:
                usuarios = self.usuario_repository.obtener_todos()
                datos['usuarios'] = [
                    {
                        'id': u.id,
                        'correo_institucional': getattr(u, 'correo_institucional', ''),
                        'nombre': getattr(u, 'nombre', ''),
                        'apellido': getattr(u, 'apellido', ''),
                        'rol': getattr(u, 'rol', ''),
                        'activo': getattr(u, 'activo', True)
                    }
                    for u in usuarios
                ]
            
            # Recopilar cursos
            if self.curso_repository:
                cursos = self.curso_repository.obtener_todos()
                datos['cursos'] = [
                    {
                        'id': c.id,
                        'nombre': getattr(c, 'nombre', ''),
                        'activo': getattr(c, 'activo', True)
                    }
                    for c in cursos
                ]
            
            # Recopilar matrículas
            if self.matricula_repository:
                matriculas = self.matricula_repository.obtener_todos()
                datos['matriculas'] = [
                    {
                        'id': m.id,
                        'usuario_id': getattr(m, 'estudiante_id', None),
                        'curso_id': getattr(m, 'curso_id', None),
                        'activo': getattr(m, 'activo', True)
                    }
                    for m in matriculas
                ]
            
            # Recopilar reservas
            if self.reserva_repository:
                reservas = self.reserva_repository.obtener_todos()
                datos['reservas'] = [
                    {
                        'id': r.id,
                        'laboratorio_id': getattr(r, 'ambiente_id', None),
                        'fecha': getattr(r, 'fecha', None),
                        'hora_inicio': getattr(r, 'hora_inicio', None),
                        'hora_fin': getattr(r, 'hora_fin', None),
                        'estado': getattr(r, 'estado', 'pendiente'),
                        'numero_participantes': getattr(r, 'numero_participantes', 1)
                    }
                    for r in reservas
                ]
            
            # Recopilar laboratorios
            if self.laboratorio_repository:
                laboratorios = self.laboratorio_repository.obtener_todos()
                datos['laboratorios'] = [
                    {
                        'id': l.id,
                        'nombre': getattr(l, 'nombre', ''),
                        'capacidad_maxima': getattr(l, 'capacidad', 30)
                    }
                    for l in laboratorios
                ]
            
        except Exception as e:
            self.logger.error(f"Error recopilando datos del sistema: {str(e)}")
        
        return datos
    
    def _generar_alertas_desde_inconsistencias(self, inconsistencias: List[Any]):
        """
        Genera alertas automáticas a partir de las inconsistencias detectadas.
        """
        if not self.gestor_alertas:
            return
            
        for inconsistencia in inconsistencias:
            alerta = self.gestor_alertas.crear_alerta_desde_inconsistencia(inconsistencia)
            self.gestor_alertas.agregar_alerta(alerta)
    
    def _generar_resumen_deteccion(self, inconsistencias: List[Any]) -> Dict[str, Any]:
        """
        Genera un resumen de la detección de inconsistencias.
        """
        if not self.detector_inconsistencias:
            return {
                'timestamp': datetime.now().isoformat(),
                'total_inconsistencias': 0,
                'estado_deteccion': 'no_disponible'
            }
            
        resumen_inconsistencias = self.detector_inconsistencias.obtener_resumen_inconsistencias()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_inconsistencias': len(inconsistencias),
            'inconsistencias_por_severidad': resumen_inconsistencias['por_severidad'],
            'inconsistencias_por_tipo': resumen_inconsistencias['por_tipo'],
            'inconsistencias_criticas': len([
                inc for inc in inconsistencias 
                if hasattr(inc, 'severidad') and inc.severidad.value == 'critica'
            ]),
            'alertas_generadas': len(self.gestor_alertas.obtener_alertas_activas()) if self.gestor_alertas else 0,
            'estado_deteccion': 'completado'
        }
    
    def _calcular_estado_general(self) -> str:
        """
        Calcula el estado general del sistema basado en alertas e inconsistencias.
        """
        alertas_criticas = 0
        if self.gestor_alertas:
            alertas_criticas = len(self.gestor_alertas.obtener_alertas_criticas())
            
        inconsistencias_criticas = 0
        if self.detector_inconsistencias:
            inconsistencias_criticas = len([
                inc for inc in self.detector_inconsistencias.inconsistencias_detectadas
                if hasattr(inc, 'severidad') and inc.severidad.value == 'critica' and not getattr(inc, 'resuelto', False)
            ])
        
        estado_rendimiento = 'optimo'
        if self.monitor_rendimiento:
            estado_rendimiento = self.monitor_rendimiento.estado_general.value if hasattr(self.monitor_rendimiento.estado_general, 'value') else str(self.monitor_rendimiento.estado_general)
        
        if alertas_criticas > 0 or inconsistencias_criticas > 0:
            return 'critico'
        elif estado_rendimiento == 'degradado':
            return 'degradado'
        elif estado_rendimiento == 'bueno':
            return 'bueno'
        else:
            return 'optimo'
    
    def _contar_inconsistencias_por_severidad(self, inconsistencias: List[Any]) -> Dict[str, int]:
        """
        Cuenta las inconsistencias agrupadas por severidad.
        """
        conteo = {
            'critica': 0,
            'alta': 0,
            'media': 0,
            'baja': 0
        }
        
        for inconsistencia in inconsistencias:
            if hasattr(inconsistencia, 'severidad'):
                severidad = inconsistencia.severidad.value if hasattr(inconsistencia.severidad, 'value') else str(inconsistencia.severidad)
                if severidad in conteo:
                    conteo[severidad] += 1
        
        return conteo
    
    def _mapear_accion_string_a_enum(self, accion: str):
        """
        Mapea un string de acción a su enum correspondiente.
        """
        if not TipoAccionAuditoria:
            return None
            
        mapeo = {
            'usuario_activado': TipoAccionAuditoria.USUARIO_ACTIVADO,
            'usuario_desactivado': TipoAccionAuditoria.USUARIO_DESACTIVADO,
            'usuario_modificado': TipoAccionAuditoria.USUARIO_MODIFICADO,
            'reporte_generado': TipoAccionAuditoria.REPORTE_GENERADO,
            'configuracion_modificada': TipoAccionAuditoria.CONFIGURACION_MODIFICADA,
            'login_admin': TipoAccionAuditoria.LOGIN_ADMIN,
            'logout_admin': TipoAccionAuditoria.LOGOUT_ADMIN,
            'consulta_realizada': TipoAccionAuditoria.CONSULTA_REALIZADA
        }
        
        return mapeo.get(accion, TipoAccionAuditoria.CONSULTA_REALIZADA)