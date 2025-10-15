#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioAsistencia:
    def __init__(self):
        self._asistencia_repo = None
        self._validador_ip = None

    def registrar_asistencia_estudiante(self, curso_id, estudiante_id, estado):
        pass

    def registrar_asistencia_docente(self, docente_id, ip):
        pass

    def calcular_porcentaje_asistencia(self, estudiante_id, curso_id):
        pass
