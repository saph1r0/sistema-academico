#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reporte.Reporte import Reporte


class ReporteGlobal(Reporte):
    def __init__(self):
        self.resumen_cursos: list[ResumenCurso] = None
        self.resumen_estudiantes: list[ResumenEstudiante] = None

    def generar_estadisticas_generales(self, ):
        pass
