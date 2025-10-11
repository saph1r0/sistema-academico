#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.asistencia.IRegistroAsistenciaRepository import IRegistroAsistenciaRepository


class RegistroAsistenciaRepositoryMySQL(IRegistroAsistenciaRepository):
    def __init__(self):
        pass

    def agregar(registro: RegistroAsistencia): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(registro: RegistroAsistencia): void(self, ):
        pass

    def obtener_por_id(id: str): RegistroAsistencia(self, ):
        pass

    def obtener_por_curso(curso_id: str, fecha: date): List<RegistroAsistencia>(self, ):
        pass

    def obtener_por_docente(docente_id: str, hora_ingreso: time): List<RegistroAsistencia>(self, ):
        pass

    def obtener_por_alumno(student_id: str, hora_registro: time): List<RegistroAsistencia>(self, ):
        pass

    def calcular_porcentaje_asistencia(alumno_id: str, curso_id: str): float(self, ):
        pass

    def listar_por_fecha(fecha: date): List<RegistroAsistencia>(self, ):
        pass

    def listar_todos(): List<RegistroAsistencia>(self, ):
        pass
