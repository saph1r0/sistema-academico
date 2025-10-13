#!/usr/bin/python
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List
from dominio.modelo.usuario.estudiante import Estudiante  # o Alumno si esa es tu clase

class IEstudianteRepository(ABC):

    @abstractmethod
    def listar_por_anio_ingreso(self, anio: int) -> List[Estudiante]:
        pass

    @abstractmethod
    def buscar_por_apellido(self, apellido: str) -> List[Estudiante]:
        pass

    @abstractmethod
    def obtener_alumnos_curso(self, curso_id: str) -> List[Estudiante]:
        pass
    