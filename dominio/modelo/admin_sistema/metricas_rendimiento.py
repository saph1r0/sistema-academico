#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import time


class TipoMetricaRendimiento(Enum):
    """Tipos de métricas de rendimiento del sistema"""
    TIEMPO_RESPUESTA_DB = "tiempo_respuesta_db"
    TIEMPO_CARGA_DASHBOARD = "tiempo_carga_dashboard"
    MEMORIA_UTILIZADA = "memoria_utilizada"
    CPU_UTILIZADA = "cpu_utilizada"
    CONEXIONES_ACTIVAS = "conexiones_activas"
    QUERIES_POR_SEGUNDO = "queries_por_segundo"
    ERRORES_POR_MINUTO = "errores_por_minuto"
    USUARIOS_CONCURRENTES = "usuarios_concurrentes"
    TIEMPO_GENERACION_REPORTES = "tiempo_generacion_reportes"
    ESPACIO_DISCO_UTILIZADO = "espacio_disco_utilizado"


class EstadoRendimiento(Enum):
    """Estados del rendimiento del sistema"""
    OPTIMO = "optimo"
    BUENO = "bueno"
    DEGRADADO = "degradado"
    CRITICO = "critico"


class MetricaRendimiento:
    """Representa una métrica de rendimiento individual"""
    
    def __init__(self):
        self.id = None
        self.tipo: TipoMetricaRendimiento = None
        self.nombre = ""
        self.descripcion = ""
        self.valor_actual = 0.0
        self.unidad = ""  # ms, %, MB, etc.
        self.timestamp = None
        
        # Umbrales de rendimiento
        self.umbral_optimo = 0.0
        self.umbral_bueno = 0.0
        self.umbral_degradado = 0.0
        self.umbral_critico = 0.0
        
        # Estado actual
        self.estado: EstadoRendimiento = EstadoRendimiento.OPTIMO
        self.tendencia = "estable"  # mejorando, empeorando, estable
        
        # Histórico
        self.valores_historicos: List[Dict[str, Any]] = []
        self.promedio_24h = 0.0
        self.maximo_24h = 0.0
        self.minimo_24h = 0.0
        
        # Configuración
        self.activa = True
        self.frecuencia_medicion = 60  # segundos
        self.retencion_datos = 7  # días
    
    def actualizar_valor(self, nuevo_valor: float):
        """Actualiza el valor de la métrica"""
        self.valor_actual = nuevo_valor
        self.timestamp = datetime.now()
        
        # Agregar al histórico
        self.valores_historicos.append({
            'valor': nuevo_valor,
            'timestamp': self.timestamp
        })
        
        # Limpiar datos antiguos
        self._limpiar_historico()
        
        # Actualizar estado
        self.estado = self._calcular_estado()
        
        # Calcular estadísticas
        self._calcular_estadisticas_24h()
        
        # Calcular tendencia
        self.tendencia = self._calcular_tendencia()
    
    def obtener_porcentaje_umbral(self) -> float:
        """Obtiene el porcentaje respecto al umbral crítico"""
        if self.umbral_critico == 0:
            return 0.0
        return (self.valor_actual / self.umbral_critico) * 100
    
    def esta_en_alerta(self) -> bool:
        """Verifica si la métrica está en estado de alerta"""
        return self.estado in [EstadoRendimiento.DEGRADADO, EstadoRendimiento.CRITICO]
    
    def obtener_color_estado(self) -> str:
        """Obtiene el color asociado al estado actual"""
        colores = {
            EstadoRendimiento.OPTIMO: "green",
            EstadoRendimiento.BUENO: "blue",
            EstadoRendimiento.DEGRADADO: "yellow",
            EstadoRendimiento.CRITICO: "red"
        }
        return colores.get(self.estado, "gray")
    
    def obtener_datos_grafico(self, horas: int = 24) -> List[Dict[str, Any]]:
        """Obtiene datos para gráfico de tendencia"""
        fecha_limite = datetime.now() - timedelta(hours=horas)
        
        datos_filtrados = [
            {
                'timestamp': dato['timestamp'].isoformat(),
                'valor': dato['valor']
            }
            for dato in self.valores_historicos
            if dato['timestamp'] >= fecha_limite
        ]
        
        return datos_filtrados
    
    def _calcular_estado(self) -> EstadoRendimiento:
        """Calcula el estado basado en los umbrales"""
        if self.valor_actual <= self.umbral_optimo:
            return EstadoRendimiento.OPTIMO
        elif self.valor_actual <= self.umbral_bueno:
            return EstadoRendimiento.BUENO
        elif self.valor_actual <= self.umbral_degradado:
            return EstadoRendimiento.DEGRADADO
        else:
            return EstadoRendimiento.CRITICO
    
    def _calcular_estadisticas_24h(self):
        """Calcula estadísticas de las últimas 24 horas"""
        fecha_limite = datetime.now() - timedelta(hours=24)
        valores_24h = [
            dato['valor'] for dato in self.valores_historicos
            if dato['timestamp'] >= fecha_limite
        ]
        
        if valores_24h:
            self.promedio_24h = sum(valores_24h) / len(valores_24h)
            self.maximo_24h = max(valores_24h)
            self.minimo_24h = min(valores_24h)
        else:
            self.promedio_24h = self.valor_actual
            self.maximo_24h = self.valor_actual
            self.minimo_24h = self.valor_actual
    
    def _calcular_tendencia(self) -> str:
        """Calcula la tendencia basada en los últimos valores"""
        if len(self.valores_historicos) < 3:
            return "estable"
        
        # Tomar los últimos 3 valores
        ultimos_valores = [dato['valor'] for dato in self.valores_historicos[-3:]]
        
        # Calcular tendencia simple
        if ultimos_valores[-1] > ultimos_valores[0] * 1.1:
            return "empeorando"
        elif ultimos_valores[-1] < ultimos_valores[0] * 0.9:
            return "mejorando"
        else:
            return "estable"
    
    def _limpiar_historico(self):
        """Limpia datos históricos antiguos"""
        fecha_limite = datetime.now() - timedelta(days=self.retencion_datos)
        self.valores_historicos = [
            dato for dato in self.valores_historicos
            if dato['timestamp'] >= fecha_limite
        ]


class MonitorRendimiento:
    """Sistema de monitoreo de rendimiento del sistema"""
    
    def __init__(self):
        self.metricas: Dict[str, MetricaRendimiento] = {}
        self.configuracion = {
            'intervalo_medicion': 60,  # segundos
            'alertar_degradacion': True,
            'umbral_alerta_critica': 5,  # minutos en estado crítico
            'log_metricas': True,
            'max_metricas_dashboard': 8
        }
        self.ultima_medicion = None
        self.estado_general = EstadoRendimiento.OPTIMO
        self._inicializar_metricas()
    
    def _inicializar_metricas(self):
        """Inicializa las métricas de rendimiento con sus umbrales"""
        metricas_config = {
            'tiempo_respuesta_db': {
                'nombre': 'Tiempo de Respuesta BD',
                'descripcion': 'Tiempo promedio de respuesta de la base de datos',
                'unidad': 'ms',
                'umbral_optimo': 50,
                'umbral_bueno': 100,
                'umbral_degradado': 200,
                'umbral_critico': 500
            },
            'tiempo_carga_dashboard': {
                'nombre': 'Carga del Dashboard',
                'descripcion': 'Tiempo de carga del dashboard administrativo',
                'unidad': 'ms',
                'umbral_optimo': 500,
                'umbral_bueno': 1000,
                'umbral_degradado': 2000,
                'umbral_critico': 5000
            },
            'memoria_utilizada': {
                'nombre': 'Memoria Utilizada',
                'descripcion': 'Porcentaje de memoria RAM utilizada',
                'unidad': '%',
                'umbral_optimo': 50,
                'umbral_bueno': 70,
                'umbral_degradado': 85,
                'umbral_critico': 95
            },
            'cpu_utilizada': {
                'nombre': 'CPU Utilizada',
                'descripcion': 'Porcentaje de CPU utilizada',
                'unidad': '%',
                'umbral_optimo': 30,
                'umbral_bueno': 50,
                'umbral_degradado': 75,
                'umbral_critico': 90
            },
            'conexiones_activas': {
                'nombre': 'Conexiones Activas',
                'descripcion': 'Número de conexiones activas a la base de datos',
                'unidad': 'conn',
                'umbral_optimo': 10,
                'umbral_bueno': 25,
                'umbral_degradado': 50,
                'umbral_critico': 100
            },
            'errores_por_minuto': {
                'nombre': 'Errores por Minuto',
                'descripcion': 'Número de errores detectados por minuto',
                'unidad': 'err/min',
                'umbral_optimo': 0,
                'umbral_bueno': 1,
                'umbral_degradado': 5,
                'umbral_critico': 10
            },
            'usuarios_concurrentes': {
                'nombre': 'Usuarios Concurrentes',
                'descripcion': 'Número de usuarios conectados simultáneamente',
                'unidad': 'usuarios',
                'umbral_optimo': 50,
                'umbral_bueno': 100,
                'umbral_degradado': 200,
                'umbral_critico': 500
            },
            'tiempo_generacion_reportes': {
                'nombre': 'Generación de Reportes',
                'descripcion': 'Tiempo promedio de generación de reportes',
                'unidad': 'seg',
                'umbral_optimo': 5,
                'umbral_bueno': 15,
                'umbral_degradado': 30,
                'umbral_critico': 60
            }
        }
        
        for tipo_str, config in metricas_config.items():
            metrica = MetricaRendimiento()
            metrica.tipo = TipoMetricaRendimiento(tipo_str)
            metrica.nombre = config['nombre']
            metrica.descripcion = config['descripcion']
            metrica.unidad = config['unidad']
            metrica.umbral_optimo = config['umbral_optimo']
            metrica.umbral_bueno = config['umbral_bueno']
            metrica.umbral_degradado = config['umbral_degradado']
            metrica.umbral_critico = config['umbral_critico']
            
            self.metricas[tipo_str] = metrica
    
    def medir_tiempo_operacion(self, operacion: str) -> 'MedidorTiempo':
        """Crea un medidor de tiempo para una operación específica"""
        return MedidorTiempo(self, operacion)
    
    def actualizar_metrica(self, tipo: str, valor: float):
        """Actualiza una métrica específica"""
        if tipo in self.metricas:
            self.metricas[tipo].actualizar_valor(valor)
            self._actualizar_estado_general()
    
    def obtener_metricas_dashboard(self) -> List[Dict[str, Any]]:
        """Obtiene las métricas principales para el dashboard"""
        metricas_principales = [
            'tiempo_carga_dashboard',
            'tiempo_respuesta_db',
            'memoria_utilizada',
            'cpu_utilizada',
            'conexiones_activas',
            'errores_por_minuto',
            'usuarios_concurrentes',
            'tiempo_generacion_reportes'
        ]
        
        resultado = []
        for tipo in metricas_principales[:self.configuracion['max_metricas_dashboard']]:
            if tipo in self.metricas:
                metrica = self.metricas[tipo]
                resultado.append({
                    'tipo': tipo,
                    'nombre': metrica.nombre,
                    'valor': metrica.valor_actual,
                    'unidad': metrica.unidad,
                    'estado': metrica.estado.value,
                    'color': metrica.obtener_color_estado(),
                    'tendencia': metrica.tendencia,
                    'porcentaje_umbral': metrica.obtener_porcentaje_umbral(),
                    'promedio_24h': metrica.promedio_24h
                })
        
        return resultado
    
    def obtener_metricas_en_alerta(self) -> List[Dict[str, Any]]:
        """Obtiene las métricas que están en estado de alerta"""
        alertas = []
        
        for tipo, metrica in self.metricas.items():
            if metrica.esta_en_alerta():
                alertas.append({
                    'tipo': tipo,
                    'nombre': metrica.nombre,
                    'valor': metrica.valor_actual,
                    'unidad': metrica.unidad,
                    'estado': metrica.estado.value,
                    'umbral_excedido': metrica.umbral_degradado if metrica.estado == EstadoRendimiento.DEGRADADO else metrica.umbral_critico,
                    'porcentaje_exceso': metrica.obtener_porcentaje_umbral() - 100
                })
        
        return alertas
    
    def obtener_resumen_rendimiento(self) -> Dict[str, Any]:
        """Obtiene un resumen general del rendimiento del sistema"""
        metricas_por_estado = {
            'optimo': 0,
            'bueno': 0,
            'degradado': 0,
            'critico': 0
        }
        
        for metrica in self.metricas.values():
            metricas_por_estado[metrica.estado.value] += 1
        
        total_metricas = len(self.metricas)
        porcentaje_saludable = ((metricas_por_estado['optimo'] + metricas_por_estado['bueno']) / total_metricas) * 100
        
        return {
            'estado_general': self.estado_general.value,
            'porcentaje_saludable': round(porcentaje_saludable, 1),
            'metricas_por_estado': metricas_por_estado,
            'total_metricas': total_metricas,
            'metricas_en_alerta': len(self.obtener_metricas_en_alerta()),
            'ultima_actualizacion': self.ultima_medicion.isoformat() if self.ultima_medicion else None
        }
    
    def obtener_datos_grafico_tendencia(self, tipo_metrica: str, horas: int = 24) -> List[Dict[str, Any]]:
        """Obtiene datos para gráfico de tendencia de una métrica específica"""
        if tipo_metrica in self.metricas:
            return self.metricas[tipo_metrica].obtener_datos_grafico(horas)
        return []
    
    def simular_medicion_sistema(self):
        """Simula una medición del sistema (para testing/demo)"""
        import random
        
        # Simular valores realistas
        simulaciones = {
            'tiempo_respuesta_db': random.uniform(30, 150),
            'tiempo_carga_dashboard': random.uniform(400, 1200),
            'memoria_utilizada': random.uniform(40, 80),
            'cpu_utilizada': random.uniform(20, 60),
            'conexiones_activas': random.randint(5, 30),
            'errores_por_minuto': random.randint(0, 3),
            'usuarios_concurrentes': random.randint(10, 80),
            'tiempo_generacion_reportes': random.uniform(3, 20)
        }
        
        for tipo, valor in simulaciones.items():
            self.actualizar_metrica(tipo, valor)
        
        self.ultima_medicion = datetime.now()
    
    def _actualizar_estado_general(self):
        """Actualiza el estado general del sistema basado en todas las métricas"""
        estados = [metrica.estado for metrica in self.metricas.values()]
        
        if EstadoRendimiento.CRITICO in estados:
            self.estado_general = EstadoRendimiento.CRITICO
        elif EstadoRendimiento.DEGRADADO in estados:
            self.estado_general = EstadoRendimiento.DEGRADADO
        elif EstadoRendimiento.BUENO in estados:
            self.estado_general = EstadoRendimiento.BUENO
        else:
            self.estado_general = EstadoRendimiento.OPTIMO


class MedidorTiempo:
    """Context manager para medir tiempo de operaciones"""
    
    def __init__(self, monitor: MonitorRendimiento, operacion: str):
        self.monitor = monitor
        self.operacion = operacion
        self.tiempo_inicio = None
        self.tiempo_fin = None
    
    def __enter__(self):
        self.tiempo_inicio = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tiempo_fin = time.time()
        duracion_ms = (self.tiempo_fin - self.tiempo_inicio) * 1000
        
        # Mapear operación a métrica
        mapeo_operaciones = {
            'dashboard_load': 'tiempo_carga_dashboard',
            'db_query': 'tiempo_respuesta_db',
            'report_generation': 'tiempo_generacion_reportes'
        }
        
        tipo_metrica = mapeo_operaciones.get(self.operacion)
        if tipo_metrica:
            self.monitor.actualizar_metrica(tipo_metrica, duracion_ms)
    
    def obtener_duracion_ms(self) -> float:
        """Obtiene la duración en milisegundos"""
        if self.tiempo_inicio and self.tiempo_fin:
            return (self.tiempo_fin - self.tiempo_inicio) * 1000
        return 0.0