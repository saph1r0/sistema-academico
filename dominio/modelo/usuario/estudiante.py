#!/usr/bin/python
# -*- coding: utf-8 -*-

from dominio.modelo.usuario.usuario import Usuario


class Estudiante(Usuario):
    def __init__(self, student_id:str, enrolled_courses = None ):
        super().__init__()   # inicializa Usuario
        self.student_id = student_id # se cambio para generar anio de ingreso
        self.año_ingreso = int(student_id[:4]) if student_id and len(student_id) >= 4 else None
        self.enrolled_courses: list = enrolled_courses if enrolled_courses else[]   
        """ se quito Enrollment"""

    def view_own_performance(self) -> dict:
        pass

    def ver_horario(self):
        pass
