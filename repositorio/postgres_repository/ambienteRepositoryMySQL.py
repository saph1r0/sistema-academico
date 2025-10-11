#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reservas.IAmbienteRepository import IAmbienteRepository


class AmbienteRepositoryMySQL(IAmbienteRepository):
    def __init__(self):
        pass

    def agregar(ambiente: Ambiente): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(ambiente: Ambiente): void(self, ):
        pass

    def obtener_por_id(id: str): Ambiente(self, ):
        pass

    def listar_disponibles(fecha: date, horario: Horario): List<Ambiente>(self, ):
        pass

    def buscar_por_tipo(tipo: str): List<Ambiente>(self, ):
        pass

    def verificar_disponibilidad(recurso_id: str, horario: Horario): bool(self, ):
        pass

    def verificar_solapamientos(recurso_id: str, fecha: date, horario: Horario): List<Ambiente>(self, ):
        pass

    def listar_todos(): List<Ambiente>(self, ):
        pass
