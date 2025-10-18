#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Dict, Any


class AlertaSistema:
    """Representa una alerta del sistema"""
    
    def __init__(self):
        self.id = None
        self.tipo = None  # 'error', 'warning', 'info'
        self.titulo = None
        self.descripcion = None
        self.fecha_creacion = None
        self.resuelto = False
        self.prioridad = 'media'  # 'alta', 'media', 'baja'
    
    def marcar_como_resuelto(self):
        """Marca la alerta como resuelta"""
        self.resuelto = True


class MetricasSistema:
    """
    Modelo de dominio para las métricas del sistema administrativo
    Contiene información agregada sobre el estado del sistema
    """
    
    def __init__(self):
        self.total_usuarios_activos = 0
        self.total_usuarios_inactivos = 0
        self.total_estudiantes = 0
        self.total_docentes = 0
        self.total_secretarias = 0
        self.total_administradores = 0
        
        self.total_cursos_activos = 0
        self.total_matriculas_activas = 0
        self.total_laboratorios = 0
        self.total_reservas_pendientes = 0
        self.total_reservas_aprobadas = 0
        
        self.promedio_asistencia_global = 0.0
        self.promedio_notas_global = 0.0
        
        self.alertas_pendientes: List[AlertaSistema] = []
        self.fecha_calculo = None
        
        # Métricas adicionales para el dashboard
        self.usuarios_activos_ultima_semana = 0
        self.nuevas_matriculas_mes = 0
        self.reservas_automaticas_hoy = 0
    
    def calcular_total_usuarios(self) -> int:
        """Calcula el total de usuarios en el sistema"""
        return (self.total_estudiantes + self.total_docentes + 
                self.total_secretarias + self.total_administradores)
    
    def obtener_porcentaje_usuarios_activos(self) -> float:
        """Calcula el porcentaje de usuarios activos"""
        total = self.calcular_total_usuarios()
        if total == 0:
            return 0.0
        return (self.total_usuarios_activos / total) * 100
    
    def obtener_alertas_por_prioridad(self, prioridad: str) -> List[AlertaSistema]:
        """Obtiene alertas filtradas por prioridad"""
        return [alerta for alerta in self.alertas_pendientes 
                if alerta.prioridad == prioridad and not alerta.resuelto]
    
    def tiene_alertas_criticas(self) -> bool:
        """Verifica si hay alertas de alta prioridad"""
        return len(self.obtener_alertas_por_prioridad('alta')) > 0
    
    def obtener_resumen_por_rol(self) -> Dict[str, int]:
        """Obtiene un resumen de usuarios por rol"""
        return {
            'estudiantes': self.total_estudiantes,
            'docentes': self.total_docentes,
            'secretarias': self.total_secretarias,
            'administradores': self.total_administradores
        }
    
    def obtener_metricas_dashboard(self) -> Dict[str, Any]:
        """Obtiene las métricas formateadas para el dashboard"""
        return {
            'usuarios_activos': self.total_usuarios_activos,
            'cursos_activos': self.total_cursos_activos,
            'promedio_asistencia': round(self.promedio_asistencia_global, 1),
            'promedio_notas': round(self.promedio_notas_global, 1),
            'alertas_pendientes': len([a for a in self.alertas_pendientes if not a.resuelto]),
            'alertas_criticas': len(self.obtener_alertas_por_prioridad('alta')),
            'usuarios_por_rol': self.obtener_resumen_por_rol(),
            'actividad_reciente': {
                'usuarios_activos_semana': self.usuarios_activos_ultima_semana,
                'nuevas_matriculas': self.nuevas_matriculas_mes,
                'reservas_automaticas': self.reservas_automaticas_hoy
            }
        }
    
    def actualizar_fecha_calculo(self):
        """Actualiza la fecha de cálculo de las métricas"""
        self.fecha_calculo = datetime.now()