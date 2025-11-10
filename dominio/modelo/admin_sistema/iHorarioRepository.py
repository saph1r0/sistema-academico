#!/usr/bin/python
# -*- coding: utf-8 -*-

class IHorarioRepository:
    def __init__(self):
        pass

    def listar_por_dia(self, dia):
        pass

    def obtener_horarios_disponibles(self, dia, duracion_minutos):
        pass

    def verificar_conflicto(self, horario, tipo_entidad, entidad_id):
        pass

    def obtener_horarios_conflictivos(self, horario):
        pass

    def verificar_solapamiento_multiple(self, horarios):
        pass

    def obtener_por_curso(self, curso_id):
        pass

    def obtener_por_laboratorio(self, laboratorio_id):
        pass

    def obtener_por_docente(self, docente_id):
        pass

    def obtener_por_ambiente(self, ambiente_id):
        pass

    def buscar_huecos_disponibles(self, dia, duracion_minutos):
        pass
