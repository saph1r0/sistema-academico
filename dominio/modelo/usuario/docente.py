#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Usuario.Usuario import Usuario


class Docente(Usuario):
    def __init__(self):
        self.id_docente = None
        self.ip_address = None
        self.taught_courses: list[Course] = None

    def ver_horario(self, ):
        pass

    def reservar_aula(self, date, classroom):
        pass
