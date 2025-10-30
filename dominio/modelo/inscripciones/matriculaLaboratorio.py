#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

class MatriculaLaboratorio:
    def __init__(self, estudiante_id=None, laboratorio_codigo=None):
        self.id = None
        self.estudiante_id = estudiante_id
        self.laboratorio_codigo = laboratorio_codigo
        self.fecha_matricula = datetime.now()
        # fecha límite para cambiar (7 días por defecto)
        self.fecha_limite_cambio = self.fecha_matricula + timedelta(days=7)

    def cancelar_matricula(self):
        # lógica para cancelar (demo)
        self.laboratorio_codigo = None

    def verificar_plazo_cambio(self) -> bool:
        return datetime.now() <= self.fecha_limite_cambio
