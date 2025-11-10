#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reporte.Reporte import Reporte


class ReporteAvance(Reporte):
    def __init__(self):
        self.porcentaje_completado = None
        self.temas_pendientes: list[str] = None
