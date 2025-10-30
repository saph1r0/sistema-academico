#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.notas.INotaRepository import INotaRepository


class NotaRepositoryMySQL(INotaRepository):
    def __init__(self):
        pass

    def agregar(nota: Nota): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(nota: Nota): void(self, ):
        pass

    def obtener_por_id(id: str):(self, ):
        pass

    def obtener_por_alumno(alumno_id: str): List<Nota>(self, ):
        pass

    def obtener_por_alumno_curso(alumno_id: str, curso_id: str): List<Nota>(self, ):
        pass

    def calcular_promedio_alumno(alumno_id: str, curso_id: str): float(self, ):
        pass

    def obtener_estadisticas_curso(curso_id: str): EstadisticasCurso(self, ):
        pass

    def listar_por_curso(curso_id: str): List<Nota>(self, ):
        pass
