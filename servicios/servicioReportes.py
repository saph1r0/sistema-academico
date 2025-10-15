#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioReportes:
    def __init__(self):
        self._repositorio_reporte = None
        self._servicio_asistencia = None
        self._servicio_notas = None
        self._servicio_avance = None

    def exportar_reporte_pdf(self, reporte):
        pass

    def exportar_reporte_excel(self, reporte):
        pass

    def generar_reporte_asistencia(self, curso_id):
        pass

    def generar_reporte_notas(self, curso_id):
        pass

    def generar_reporte_avance(self, curso_id):
        pass

    def generar_reporte_global(self, periodo_id):
        pass

    def generar_lista_profesores(self, periodo_id):
        pass

    def generar_lista_alumnos(self, criterio):
        pass
