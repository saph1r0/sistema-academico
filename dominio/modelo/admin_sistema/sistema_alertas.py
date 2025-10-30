#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
from .inconsistencia_sistema import InconsistenciaSistema, SeveridadInconsistencia


class TipoAlerta(Enum):
    """Tipos de alertas del sistema"""
    ERROR_CARGA_DATOS = "error_carga_datos"
    INCONSISTENCIA_DETECTADA = "inconsistencia_detectada"
    RENDIMIENTO_DEGRADADO = "rendimiento_degradado"
    CAPACIDAD_LIMITE = "capacidad_limite"
    SEGURIDAD = "seguridad"
    MANTENIMIENTO = "mantenimiento"
    SISTEMA = "sistema"


class EstadoAlerta(Enum):
    """Estados posibles de una alerta"""
    ACTIVA = "activa"
    RESUELTA = "resuelta"
    IGNORADA = "ignorada"
    EN_PROCESO = "en_proceso"


class AlertaSistema:
    """Representa una alerta del sistema"""
    
    def __init__(self):
        self.id = None
        self.tipo: TipoAlerta = None
        self.severidad: SeveridadInconsistencia = SeveridadInconsistencia.MEDIA
        self.titulo = ""
        self.descripcion = ""
        self.mensaje_detallado = ""
        self.entidad_origen = ""  # Módulo o componente que generó la alerta
        self.datos_contexto: Dict[str, Any] = {}
        
        # Timestamps
        self.fecha_creacion = None
        self.fecha_actualizacion = None
        self.fecha_resolucion = None
        
        # Estado y gestión
        self.estado: EstadoAlerta = EstadoAlerta.ACTIVA
        self.usuario_asignado = None
        self.usuario_resolucion = None
        self.accion_correctiva = ""
        self.notas_resolucion = ""
        
        # Configuración de notificación
        self.notificar_dashboard = True
        self.notificar_email = False
        self.frecuencia_recordatorio = None  # en minutos
        self.ultima_notificacion = None
        
        # Métricas
        self.veces_ocurrida = 1
        self.impacto_estimado = "bajo"  # bajo, medio, alto, critico
    
    def marcar_como_resuelta(self, usuario: str, accion: str = "", notas: str = ""):
        """Marca la alerta como resuelta"""
        self.estado = EstadoAlerta.RESUELTA
        self.fecha_resolucion = datetime.now()
        self.fecha_actualizacion = datetime.now()
        self.usuario_resolucion = usuario
        self.accion_correctiva = accion
        self.notas_resolucion = notas
    
    def marcar_como_ignorada(self, usuario: str, razon: str = ""):
        """Marca la alerta como ignorada"""
        self.estado = EstadoAlerta.IGNORADA
        self.fecha_actualizacion = datetime.now()
        self.usuario_resolucion = usuario
        self.notas_resolucion = razon
    
    def asignar_usuario(self, usuario: str):
        """Asigna la alerta a un usuario específico"""
        self.usuario_asignado = usuario
        self.estado = EstadoAlerta.EN_PROCESO
        self.fecha_actualizacion = datetime.now()
    
    def incrementar_ocurrencia(self):
        """Incrementa el contador de veces que ha ocurrido esta alerta"""
        self.veces_ocurrida += 1
        self.fecha_actualizacion = datetime.now()
    
    def necesita_recordatorio(self) -> bool:
        """Verifica si la alerta necesita un recordatorio"""
        if not self.frecuencia_recordatorio or self.estado != EstadoAlerta.ACTIVA:
            return False
        
        if not self.ultima_notificacion:
            return True
        
        tiempo_transcurrido = datetime.now() - self.ultima_notificacion
        return tiempo_transcurrido.total_seconds() >= (self.frecuencia_recordatorio * 60)
    
    def obtener_prioridad_numerica(self) -> int:
        """Obtiene la prioridad numérica para ordenamiento"""
        prioridades = {
            SeveridadInconsistencia.CRITICA: 4,
            SeveridadInconsistencia.ALTA: 3,
            SeveridadInconsistencia.MEDIA: 2,
            SeveridadInconsistencia.BAJA: 1
        }
        return prioridades.get(self.severidad, 1)
    
    def obtener_tiempo_transcurrido(self) -> str:
        """Obtiene el tiempo transcurrido desde la creación en formato legible"""
        if not self.fecha_creacion:
            return "Desconocido"
        
        delta = datetime.now() - self.fecha_creacion
        
        if delta.days > 0:
            return f"Hace {delta.days} día{'s' if delta.days > 1 else ''}"
        elif delta.seconds > 3600:
            horas = delta.seconds // 3600
            return f"Hace {horas} hora{'s' if horas > 1 else ''}"
        elif delta.seconds > 60:
            minutos = delta.seconds // 60
            return f"Hace {minutos} minuto{'s' if minutos > 1 else ''}"
        else:
            return "Hace menos de un minuto"


class GestorAlertas:
    """Sistema de gestión de alertas del sistema"""
    
    def __init__(self):
        self.alertas: List[AlertaSistema] = []
        self.configuracion = {
            'max_alertas_activas': 100,
            'dias_retencion_resueltas': 30,
            'auto_resolver_duplicadas': True,
            'umbral_critico_errores': 5,  # errores por minuto
            'umbral_warning_errores': 3
        }
    
    def crear_alerta_desde_inconsistencia(self, inconsistencia: InconsistenciaSistema) -> AlertaSistema:
        """Crea una alerta a partir de una inconsistencia detectada"""
        alerta = AlertaSistema()
        alerta.tipo = TipoAlerta.INCONSISTENCIA_DETECTADA
        alerta.severidad = inconsistencia.severidad
        alerta.titulo = f"Inconsistencia: {inconsistencia.titulo}"
        alerta.descripcion = inconsistencia.descripcion
        alerta.mensaje_detallado = f"Entidad: {inconsistencia.entidad_afectada}, ID: {inconsistencia.registro_id}"
        alerta.entidad_origen = "DetectorInconsistencias"
        alerta.datos_contexto = {
            'inconsistencia_id': inconsistencia.id,
            'tipo_inconsistencia': inconsistencia.tipo.value,
            'entidad_afectada': inconsistencia.entidad_afectada,
            'registro_id': inconsistencia.registro_id,
            'datos_adicionales': inconsistencia.datos_adicionales
        }
        alerta.fecha_creacion = datetime.now()
        alerta.fecha_actualizacion = datetime.now()
        
        # Configurar notificaciones según severidad
        if inconsistencia.severidad in [SeveridadInconsistencia.CRITICA, SeveridadInconsistencia.ALTA]:
            alerta.notificar_email = True
            alerta.frecuencia_recordatorio = 30  # 30 minutos
            alerta.impacto_estimado = "alto" if inconsistencia.severidad == SeveridadInconsistencia.CRITICA else "medio"
        
        return alerta
    
    def crear_alerta_error_carga(self, modulo: str, error: str, detalles: Dict[str, Any] = None) -> AlertaSistema:
        """Crea una alerta por error de carga de datos"""
        alerta = AlertaSistema()
        alerta.tipo = TipoAlerta.ERROR_CARGA_DATOS
        alerta.severidad = SeveridadInconsistencia.ALTA
        alerta.titulo = f"Error de carga en {modulo}"
        alerta.descripcion = error
        alerta.entidad_origen = modulo
        alerta.datos_contexto = detalles or {}
        alerta.fecha_creacion = datetime.now()
        alerta.fecha_actualizacion = datetime.now()
        alerta.notificar_email = True
        alerta.impacto_estimado = "alto"
        
        return alerta
    
    def crear_alerta_rendimiento(self, metrica: str, valor_actual: float, umbral: float) -> AlertaSistema:
        """Crea una alerta por degradación de rendimiento"""
        alerta = AlertaSistema()
        alerta.tipo = TipoAlerta.RENDIMIENTO_DEGRADADO
        alerta.severidad = SeveridadInconsistencia.MEDIA
        alerta.titulo = f"Rendimiento degradado: {metrica}"
        alerta.descripcion = f"Métrica {metrica} excede umbral: {valor_actual} > {umbral}"
        alerta.entidad_origen = "MonitorRendimiento"
        alerta.datos_contexto = {
            'metrica': metrica,
            'valor_actual': valor_actual,
            'umbral': umbral,
            'porcentaje_exceso': ((valor_actual - umbral) / umbral) * 100
        }
        alerta.fecha_creacion = datetime.now()
        alerta.fecha_actualizacion = datetime.now()
        
        return alerta
    
    def agregar_alerta(self, alerta: AlertaSistema) -> bool:
        """Agrega una nueva alerta al sistema"""
        # Verificar si ya existe una alerta similar
        if self.configuracion['auto_resolver_duplicadas']:
            alerta_existente = self._buscar_alerta_similar(alerta)
            if alerta_existente:
                alerta_existente.incrementar_ocurrencia()
                return False
        
        # Verificar límite de alertas activas
        alertas_activas = len([a for a in self.alertas if a.estado == EstadoAlerta.ACTIVA])
        if alertas_activas >= self.configuracion['max_alertas_activas']:
            self._limpiar_alertas_antiguas()
        
        self.alertas.append(alerta)
        return True
    
    def obtener_alertas_activas(self) -> List[AlertaSistema]:
        """Obtiene todas las alertas activas"""
        return [a for a in self.alertas if a.estado == EstadoAlerta.ACTIVA]
    
    def obtener_alertas_por_severidad(self, severidad: SeveridadInconsistencia) -> List[AlertaSistema]:
        """Obtiene alertas filtradas por severidad"""
        return [a for a in self.alertas if a.severidad == severidad and a.estado == EstadoAlerta.ACTIVA]
    
    def obtener_alertas_criticas(self) -> List[AlertaSistema]:
        """Obtiene alertas críticas activas"""
        return self.obtener_alertas_por_severidad(SeveridadInconsistencia.CRITICA)
    
    def obtener_alertas_dashboard(self, limite: int = 10) -> List[AlertaSistema]:
        """Obtiene las alertas más importantes para mostrar en el dashboard"""
        alertas_dashboard = [a for a in self.alertas 
                           if a.estado == EstadoAlerta.ACTIVA and a.notificar_dashboard]
        
        # Ordenar por prioridad y fecha
        alertas_dashboard.sort(key=lambda x: (-x.obtener_prioridad_numerica(), x.fecha_creacion))
        
        return alertas_dashboard[:limite]
    
    def obtener_resumen_alertas(self) -> Dict[str, Any]:
        """Obtiene un resumen de las alertas del sistema"""
        alertas_activas = self.obtener_alertas_activas()
        
        resumen = {
            'total_activas': len(alertas_activas),
            'por_severidad': {
                'critica': len([a for a in alertas_activas if a.severidad == SeveridadInconsistencia.CRITICA]),
                'alta': len([a for a in alertas_activas if a.severidad == SeveridadInconsistencia.ALTA]),
                'media': len([a for a in alertas_activas if a.severidad == SeveridadInconsistencia.MEDIA]),
                'baja': len([a for a in alertas_activas if a.severidad == SeveridadInconsistencia.BAJA])
            },
            'por_tipo': {},
            'alertas_recientes': [],
            'tendencia_24h': self._calcular_tendencia_24h()
        }
        
        # Contar por tipo
        for alerta in alertas_activas:
            tipo = alerta.tipo.value
            resumen['por_tipo'][tipo] = resumen['por_tipo'].get(tipo, 0) + 1
        
        # Alertas recientes (últimas 24 horas)
        hace_24h = datetime.now() - timedelta(hours=24)
        resumen['alertas_recientes'] = [
            {
                'id': a.id,
                'titulo': a.titulo,
                'severidad': a.severidad.value,
                'tiempo_transcurrido': a.obtener_tiempo_transcurrido()
            }
            for a in alertas_activas 
            if a.fecha_creacion and a.fecha_creacion >= hace_24h
        ]
        
        return resumen
    
    def resolver_alerta(self, alerta_id: str, usuario: str, accion: str = "", notas: str = "") -> bool:
        """Resuelve una alerta específica"""
        for alerta in self.alertas:
            if alerta.id == alerta_id:
                alerta.marcar_como_resuelta(usuario, accion, notas)
                return True
        return False
    
    def _buscar_alerta_similar(self, nueva_alerta: AlertaSistema) -> Optional[AlertaSistema]:
        """Busca una alerta similar ya existente"""
        for alerta in self.alertas:
            if (alerta.estado == EstadoAlerta.ACTIVA and
                alerta.tipo == nueva_alerta.tipo and
                alerta.entidad_origen == nueva_alerta.entidad_origen and
                alerta.titulo == nueva_alerta.titulo):
                return alerta
        return None
    
    def _limpiar_alertas_antiguas(self):
        """Limpia alertas resueltas antiguas"""
        fecha_limite = datetime.now() - timedelta(days=self.configuracion['dias_retencion_resueltas'])
        
        self.alertas = [
            a for a in self.alertas
            if not (a.estado == EstadoAlerta.RESUELTA and 
                   a.fecha_resolucion and 
                   a.fecha_resolucion < fecha_limite)
        ]
    
    def _calcular_tendencia_24h(self) -> Dict[str, int]:
        """Calcula la tendencia de alertas en las últimas 24 horas"""
        hace_24h = datetime.now() - timedelta(hours=24)
        
        alertas_24h = [a for a in self.alertas if a.fecha_creacion and a.fecha_creacion >= hace_24h]
        resueltas_24h = [a for a in alertas_24h if a.estado == EstadoAlerta.RESUELTA]
        
        return {
            'nuevas': len(alertas_24h),
            'resueltas': len(resueltas_24h),
            'pendientes': len(alertas_24h) - len(resueltas_24h)
        }
    
    def procesar_alertas_recordatorio(self) -> List[AlertaSistema]:
        """Procesa alertas que necesitan recordatorio"""
        alertas_recordatorio = []
        
        for alerta in self.alertas:
            if alerta.necesita_recordatorio():
                alerta.ultima_notificacion = datetime.now()
                alertas_recordatorio.append(alerta)
        
        return alertas_recordatorio