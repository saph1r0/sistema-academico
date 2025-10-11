#!/usr/bin/python
# -*- coding: utf-8 -*-

class Laboratorio:
    def __init__(self):
        self.codigo: str = None
        self.nombre = None
        self.capacidad_maxima = None
        self.horario = None
        self.disponible: bool = None

    def verificar_disponibilidad(self, ):
        pass

    def verificar_conflicto_horario(self, horario):
        pass
