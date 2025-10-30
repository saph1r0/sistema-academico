#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import time

class Laboratorio:
    def __init__(self, codigo: str, nombre: str, capacidad_maxima: int = 20, horario: dict = None):
        """
        horario: {'start': datetime.time, 'end': datetime.time}
        codigo: e.g. "CS205-A"
        nombre: e.g. "Programación II - Lab A"
        """
        self.codigo: str = codigo
        self.nombre = nombre
        self.capacidad_maxima = capacidad_maxima
        self.horario = horario or {'start': time(0, 0), 'end': time(0, 0)}
        self.disponible: bool = True

    def verificar_disponibilidad(self, inscritos_count: int) -> bool:
        """True si hay cupo"""
        return inscritos_count < self.capacidad_maxima

    def verificar_conflicto_horario(self, horario_curso: dict) -> bool:
        """
        horario_curso: {'start': time, 'end': time}
        Devuelve True si HAY conflicto.
        """
        s1 = self.horario['start']
        e1 = self.horario['end']
        s2 = horario_curso['start']
        e2 = horario_curso['end']

        # conflicto si los intervalos se solapan
        overlap = (s1 < e2) and (s2 < e1)
        return overlap
