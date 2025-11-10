#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

class MetricasSistema:
    """Modelo de dominio para las métricas del sistema"""
    
    def __init__(self):
        # Métricas básicas
        self.total_usuarios_activos = 0
        self.total_usuarios_inactivos = 0
        self.total_cursos_activos = 0
        self.total_laboratorios = 0
        self.promedio_asistencia_global = 0.0
        self.promedio_notas_global = 0.0
        self.alertas_pendientes = []
        self.fecha_calculo = None
        self.metricas_adicionales = {}
        
        # Métricas por rol
        self.total_estudiantes = 0
        self.total_docentes = 0
        self.total_secretarias = 0
        self.total_administradores = 0
        
        # Métricas académicas
        self.total_matriculas_activas = 0
        self.nuevas_matriculas_mes = 0
        self.total_reservas_pendientes = 0
        self.total_reservas_aprobadas = 0
        self.reservas_automaticas_hoy = 0
        
        # Métricas de actividad
        self.usuarios_activos_ultima_semana = 0

    def calcular_metricas(self):
        """Calcula las métricas del sistema"""
        # Simulación de cálculo de métricas
        # En una implementación real, esto consultaría la base de datos
        self.total_usuarios_activos = 150
        self.total_cursos_activos = 25
        self.total_laboratorios = 8
        self.promedio_asistencia_global = 85.5
        self.promedio_notas_global = 14.2
        self.fecha_calculo = datetime.now()
        
        return self

    def obtener_resumen_dashboard(self):
        """Obtiene un resumen para el dashboard administrativo"""
        return {
            'usuarios_activos': self.total_usuarios_activos,
            'cursos_activos': self.total_cursos_activos,
            'laboratorios_disponibles': self.total_laboratorios,
            'asistencia_promedio': f"{self.promedio_asistencia_global:.1f}%",
            'notas_promedio': f"{self.promedio_notas_global:.1f}",
            'alertas_count': len(self.alertas_pendientes),
            'ultima_actualizacion': self.fecha_calculo
        }

    def agregar_alerta(self, tipo, mensaje, nivel='info'):
        """Agrega una alerta al sistema"""
        alerta = {
            'tipo': tipo,
            'mensaje': mensaje,
            'nivel': nivel,
            'fecha': datetime.now()
        }
        self.alertas_pendientes.append(alerta)

    def limpiar_alertas_resueltas(self):
        """Limpia las alertas que han sido resueltas"""
        # En una implementación real, esto marcaría las alertas como resueltas
        self.alertas_pendientes = []

    def obtener_metricas_rendimiento(self):
        """Obtiene métricas de rendimiento del sistema"""
        return {
            'tiempo_respuesta_promedio': 0.25,
            'uso_memoria': 65.2,
            'uso_cpu': 12.8,
            'conexiones_activas': 45,
            'uptime': "5 días, 12 horas"
        }

    def __str__(self):
        return f"MetricasSistema(usuarios={self.total_usuarios_activos}, cursos={self.total_cursos_activos})"