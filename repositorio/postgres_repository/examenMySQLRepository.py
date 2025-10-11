#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.notas.IExamenRepository import IExamenRepository


class ExamenMySQLRepository(IExamenRepository):
    def __init__(self):
        pass

    def agregar(examen: Examen): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(examen: Examen): void(self, ):
        pass

    def obtener_por_id(id: str): Examen(self, ):
        pass

    def obtener_por_curso(curso_id: str): List<Examen>(self, ):
        pass

    def obtener_por_parcial(curso_id: str, numero_parcial: int): Examen(self, ):
        pass

    def calcular_estadisticas(examen_id: str): dict(self, ):
        pass

    def listar_todos(): List<Examen>(self, ):
        pass
