#!/usr/bin/python
# -*- coding: utf-8 -*-

from dominio.modelo.usuario.iEstudianteRepository import IEstudianteRepository
from dominio.modelo.usuario.estudiante import Estudiante
from typing import List


class EstudianteRepositorioMemoria(IEstudianteRepository):
    def __init__(self):
        self.estudiantes: List[Estudiante] = []

    def guardar(self, estudiante: Estudiante):
        """Guarda un estudiante en la lista en memoria"""
        self.estudiantes.append(estudiante)

    def listar(self) -> List[Estudiante]:
        """Devuelve todos los estudiantes guardados"""
        return self.estudiantes

    def listar_por_anio_ingreso(self, anio: int) -> List[Estudiante]:
        """Filtra estudiantes por año de ingreso"""
        return [e for e in self.estudiantes if getattr(e, "año_ingreso", None) == anio]

    def buscar_por_apellido(self, apellido: str) -> List[Estudiante]:
        """Busca estudiantes cuyo apellido coincida (case-insensitive)"""
        return [e for e in self.estudiantes if apellido.lower() in getattr(e, "apellido", "").lower()]

    def obtener_alumnos_curso(self, curso_id: str) -> List[Estudiante]:
        """(Ejemplo) Devuelve estudiantes matriculados en un curso específico"""
        return [e for e in self.estudiantes if curso_id in getattr(e, "enrolled_courses", [])]
