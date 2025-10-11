#!/usr/bin/python
# -*- coding: utf-8 -*-

class IAmbienteRepository:
    def __init__(self):
        pass

    def listar_disponibles(self, fecha, horario):
        pass

    def buscar_por_tipo(self, tipo):
        pass

    def verificar_disponibilidad(self, recurso_id, horario):
        pass

    def _verificar_solapamientos(self, recurso_id, fecha):
        pass
