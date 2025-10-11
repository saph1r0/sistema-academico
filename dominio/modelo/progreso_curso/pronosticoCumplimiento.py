#!/usr/bin/python
# -*- coding: utf-8 -*-

class PronosticoCumplimiento:
    def __init__(self):
        self.probabilidad_cumplimiento = None
        self.temas_en_riesgo: list[str] = None
        self.fecha_estimada_finalizacion = None
