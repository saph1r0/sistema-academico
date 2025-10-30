#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reporte.Reporte import Reporte


class ReporteAsistencia(Reporte):
    def __init__(self):
        self.porcentaje_asistencia = None
        self.numero_faltas = None
        self.cumple_minimo = None
