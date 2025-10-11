#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.inscripciones.IMatriculaRepository import IMatriculaRepository


class MatriculaRepositoryMySQL(IMatriculaRepository):
    def __init__(self):
        pass

    def agregar(matricula: Matricula): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(matricula: Matricula): void(self, ):
        pass

    def obtener_por_id(id: str): Matricula(self, ):
        pass

    def obtener_por_alumno(alumno_id: str): List<Matricula>(self, ):
        pass

    def obtener_por_curso(curso_id: str): List<Matricula>(self, ):
        pass

    def obtener_por_estado(estado: EstadoMatricula): List<Matricula>(self, ):
        pass

    def listar_todas(): List<Matricula>(self, ):
        pass

    def buscar_por_fecha(inicio: datetime, fin: datetime): List<Matricula>(self, ):
        pass
