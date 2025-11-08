#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

class ConfiguracionSistema:
    """Modelo de dominio para la configuración del sistema"""
    
    def __init__(self):
        self.id = None
        self.capacidad_maxima_laboratorio = 30
        self.tiempo_sesion_minutos = 120
        self.backup_automatico = True
        self.frecuencia_backup_horas = 24
        self.alertas_activas = True
        self.fecha_modificacion = None
        self.usuario_modificacion = None
        self.configuracion_adicional = {}

    def actualizar_configuracion(self, parametros, usuario_id):
        """Actualiza la configuración del sistema"""
        for key, value in parametros.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.fecha_modificacion = datetime.now()
        self.usuario_modificacion = usuario_id
        return True

    def validar_parametros(self, parametros):
        """Valida los parámetros de configuración"""
        errores = []
        
        if 'capacidad_maxima_laboratorio' in parametros:
            if not isinstance(parametros['capacidad_maxima_laboratorio'], int) or parametros['capacidad_maxima_laboratorio'] <= 0:
                errores.append("La capacidad máxima debe ser un número entero positivo")
        
        if 'tiempo_sesion_minutos' in parametros:
            if not isinstance(parametros['tiempo_sesion_minutos'], int) or parametros['tiempo_sesion_minutos'] <= 0:
                errores.append("El tiempo de sesión debe ser un número entero positivo")
        
        if 'frecuencia_backup_horas' in parametros:
            if not isinstance(parametros['frecuencia_backup_horas'], int) or parametros['frecuencia_backup_horas'] <= 0:
                errores.append("La frecuencia de backup debe ser un número entero positivo")
        
        return errores

    def obtener_configuracion_actual(self):
        """Obtiene la configuración actual del sistema"""
        return {
            'capacidad_maxima_laboratorio': self.capacidad_maxima_laboratorio,
            'tiempo_sesion_minutos': self.tiempo_sesion_minutos,
            'backup_automatico': self.backup_automatico,
            'frecuencia_backup_horas': self.frecuencia_backup_horas,
            'alertas_activas': self.alertas_activas,
            'fecha_modificacion': self.fecha_modificacion,
            'usuario_modificacion': self.usuario_modificacion
        }

    def es_parametro_critico(self, parametro):
        """Determina si un parámetro es crítico para el funcionamiento"""
        parametros_criticos = [
            'capacidad_maxima_laboratorio',
            'tiempo_sesion_minutos',
            'backup_automatico'
        ]
        return parametro in parametros_criticos

    def __str__(self):
        return f"ConfiguracionSistema(id={self.id}, modificado={self.fecha_modificacion})"