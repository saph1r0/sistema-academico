#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Admin_Sistema.IHorarioRepository import IHorarioRepository


class HorarioMySQLRepository(IHorarioRepository):
    def __init__(self):
        pass

    def listar_por_dia(dia: DiaSemana): List<Horario>(self, ):
        pass

    def obtener_horarios_disponibles(dia: DiaSemana, duracion_minutos: int): List<Horario>(self, ):
        pass

    def verificar_conflicto(horario: Horario, dia: str, entidad_id: str): bool(self, ):
        pass

    def obtener_horarios_conflicto(horario: Horario): List<Horario>(self, ):
        pass

    def verificar_solapamiento(horario1: Horario, horario2: Horario): bool(self, ):
        pass

    def obtener_por_curso(curso_id: str): List<Horario>(self, ):
        pass

    def obtener_por_laboratorio(lab_id: str): List<Horario>(self, ):
        pass

    def obtener_por_docente(docente_id: str): List<Horario>(self, ):
        pass

    def obtener_por_aula(aula_id: str): List<Horario>(self, ):
        pass

    def obtener_por_ambiente(ambiente_id: str): List<Horario>(self, ):
        pass

    def buscar_huecos_disponibles(dia: DiaSemana, duracion_minutos: int): List<tuple>(self, ):
        pass

    def listar_todos(): List<Horario>(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def agregar(horario: Horario): void(self, ):
        pass

    def +actualizar(horario: Horario): void(self, ):
        pass
