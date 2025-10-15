#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioReservas:
    def __init__(self):
        self._reserva_repo = None
        self._ambiente_repo = None

    def consultar_disponibilidad(self, fecha, inicio, fin, tipo):
        pass

    def reservar_ambiente(self, docente_id, ambiente_id, fecha, inicio, fin):
        pass

    def verificar_conflicto(self, ambiente_id, fecha, inicio, fin):
        pass
