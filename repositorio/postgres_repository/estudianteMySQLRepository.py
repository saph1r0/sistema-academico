#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Usuario.IEstudianteRepository import IEstudianteRepository


class EstudianteMySQLRepository(IEstudianteRepository):
    def __init__(self):
        pass

    def listar_por_año_ingreso(año: int): List<Estudiante>(self, ):
        pass

    def buscar_por_apellido(apellido: str): List<Estudiante>(self, ):
        pass

    def obtener_alumnos_curso(self, curso_id):
        pass

    def obtener_por_student_id(self, student_id):
        pass

    def obtener_cursos_matriculados(self, student_id):
        pass

    def verificar_inscripcion(self, student_id, curso_id):
        pass
