#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.inscripciones.ICursoRepository import ICursoRepository


class CursoRepositoryMySQL(ICursoRepository):
    def __init__(self):
        pass

    def agregar(curso: Curso): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(curso: Curso): void(self, ):
        pass

    def obtener_por_id(id: str): Curso(self, ):
        pass

    def listar_por_periodo(anio: int, semestre: int): List<Curso>(self, ):
        pass

    def buscar_por_nombre(nombre: str): List<Curso>(self, ):
        pass

    def obtener_por_docente(docente_id: str): List<Curso>(self, ):
        pass

    def listar_todos(): List<Curso>(self, ):
        pass
