#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reporte.Reporte import Reporte


class ReporteNotas(Reporte):
    def __init__(self):
        self.notas_por_evaluacion = None
        self.promedio_acumulado = None
