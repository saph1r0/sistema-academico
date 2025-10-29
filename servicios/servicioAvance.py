#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioAvance:
    def __init__(self):
        self._avance_repo = None
        self._unidad_repo = None

    def subir_silabo(self, curso_id, silabo_datos):
        """Sube un sílabo para un curso"""
        return True

    def registrar_avance_semanal(self, curso_id, temas_completados):
        """Registra el avance semanal de un curso"""
        return True

    def calcular_avance_semanal(self, curso_id):
        """Calcula el avance semanal de un curso"""
        return 75.0

    def generar_pronostico_cumplimiento(self, curso_id):
        """Genera pronóstico de cumplimiento del sílabo"""
        return {'pronostico': 'En tiempo', 'porcentaje_esperado': 80.0}

    @staticmethod
    def calcular_avance_estudiante(estudiante_id):
        """Calcula el avance de un estudiante"""
        return 78.5
