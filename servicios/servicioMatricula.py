#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioMatricula:
    def __init__(self):
        self._matricula_repo = None
        self._curso_repo = None
        self._laboratorio_repo = None
        self._configuracion_repo = None
        self._procesador_excel = None
        self._generador_pdf = None

    def procesar_lista_matricula(self, archivo, periodo_id):
        pass

    def obtener_cursos_matriculados(self, estudiante_id):
        pass

    def matricular_laboratorio(self, estudiante_id, laboratorio_id):
        pass

    def desmatricular_laboratorio(self, matricula_lab_id):
        pass

    def cambiar_laboratorio(self, estudiante_id, laboratorio_actual_id, nuevo_laboratorio_id):
        pass

    def verificar_conflicto_horario(self, estudiante_id, horario):
        pass

    def verificar_plazo_cambio_laboratorio_activo(self, ):
        pass

    def verificar_capacidad_laboratorio(self, laboratorio_id):
        pass

    def generar_constancia_matricula(self, estudiante_id, periodo_id):
        pass

    def obtener_horario_estudiante(self, estudiante_id):
        pass

    def obtener_horario_docente(self, docente_id):
        pass
