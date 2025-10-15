#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioNotas:
    def __init__(self):
        self._nota_repo = None
        self._examen_repo = None
        self._procesador_excel = None
        self._generador_pdf = None

    def ingresar_notas(self, curso_id, notas):
        pass

    def procesar_notas_desde_excel(self, archivo, curso_id):
        pass

    def calcular_estadisticas(self, curso_id):
        pass

    def obtener_notas_estudiante(self, estudiante_id, curso_id):
        pass
