#!/usr/bin/python
# -*- coding: utf-8 -*-

class IRegistroAsistenciaRepository:
    def __init__(self):
        self.Attribute1 = None

    def agregar(self, registro):
        pass

    def obtener_por_id(self, id):
        pass

    def actualizar(self, registro):
        pass

    def obtener_por_curso_fecha(self, curso_id, fecha):
        pass

    def calcular_porcentaje_asistencia(self, alumno_id, curso_id):
        pass

    def obtener_por_docente(id_docente: str, hora_ingreso: time): list[RegistroAsistencia](self, ):
        pass

    def obtener_por_alumno(student_id: str, hora_registro:time): list[RegistroAsistencia](self, ):
        pass
