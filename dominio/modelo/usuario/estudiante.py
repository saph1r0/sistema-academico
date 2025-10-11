#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Usuario.Usuario import Usuario


class Estudiante(Usuario):
    def __init__(self):
        self.student_id = None
        self.año_ingreso = None
        self.enrolled_courses: list[Enrollment] = None

    def view_own_performance() : dict(self, ):
        pass

    def ver_horario(self, ):
        pass
