#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.inscripciones.ILaboratorioRepository import ILaboratorioRepository
from Dominio.Modelo.inscripciones.ILaboratorioRepository import ILaboratorioRepository


class LaboratorioRepositoryMySQL(ILaboratorioRepository, ILaboratorioRepository):
    def __init__(self):
        pass

    def agregar(lab: Laboratorio): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(lab: Laboratorio): void(self, ):
        pass

    def +obtener_por_id(id: str): Laboratorio(self, ):
        pass

    def +listar_por_curso(curso_id: str): List<Laboratorio>(self, ):
        pass

    def verificar_conflicto_horario(lab_id: str, horario: Horario): bool(self, ):
        pass

    def obtener_con_cupos(): List<Laboratorio>(self, ):
        pass

    def listar_todos(): List<Laboratorio>(self, ):
        pass

    def listar_disponibles(fecha: date, horario: Horario): List<Laboratorio>(self, ):
        pass

    def listar_por_docente(docente_id: str): List<Laboratorio>(self, ):
        pass
