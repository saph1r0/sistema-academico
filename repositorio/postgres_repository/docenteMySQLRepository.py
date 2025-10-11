#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Usuario.IDocenteRepository import IDocenteRepository


class DocenteMySQLRepository(IDocenteRepository):
    def __init__(self):
        pass

    def listar_por_especialidad(especialidad: str): List<Docente>(self, ):
        pass

    def obtener_por_id(docente_id: str): Docente(self, ):
        pass

    def obtener_cursos_dictados(docente_id: str): List<Curso>(self, ):
        pass

    def verificar_disponibilidad(docente_id: str, horario: Horario): bool(self, ):
        pass

    def reservar_aula(docente_id: str, date: datetime, classroom_id: str): bool(self, ):
        pass
