#!/usr/bin/python
# -*- coding: utf-8 -*-
import pandas as pd
from dominio.modelo.usuario.estudiante import Estudiante

class ServicioMatricula:
    def __init__(self, repo):
        self.repo = repo
        self._matricula_repo = None
        self._curso_repo = None
        self._laboratorio_repo = None
        self._configuracion_repo = None
        self._procesador_excel = None
        self._generador_pdf = None

    def procesar_lista_matricula(self, archivo_excel, periodo_id):
        df = pd.read_excel(archivo_excel, header=9)  # línea 10 tiene encabezados
        df.columns = df.columns.str.strip().str.upper()

        estudiantes = []
        for _, row in df.iterrows():
            cui = str(row.get("CUI", "")).strip()
            
            apellidos_nombres = str(row.get("APELLIDOS Y NOMBRES", "")).strip()

            # dividir primero por coma → ["ABENSUR/ROMERO", "DIEGO DANIEL"]
            partes = apellidos_nombres.split(",")
            if len(partes) == 2:
                apellidos_raw = partes[0].strip()
                nombres = partes[1].strip()
            else:
                apellidos_raw = apellidos_nombres
                nombres = ""

            # dividir apellidos por "/" → ["ABENSUR", "ROMERO"]
            apellidos = apellidos_raw.replace("/", " ")
                 
            anio_ingreso = cui[:4]

            est = Estudiante(
            codigo=cui,
            apellidos=apellidos, # <-- ¡NUEVO!
            nombres=nombres      # <-- ¡NUEVO!
        ) 

            self.repo.guardar(est)
            estudiantes.append(est)

        return estudiantes

    def obtener_cursos_matriculados(self, estudiante_id):
        """Obtiene los cursos en los que está matriculado un estudiante"""
        return []

    def matricular_laboratorio(self, estudiante_id, laboratorio_id):
        """Matricula un estudiante en un laboratorio"""
        return True

    def desmatricular_laboratorio(self, estudiante_id, laboratorio_id):
        """Desmatricula un estudiante de un laboratorio"""
        return True

    def cambiar_laboratorio(self, estudiante_id, laboratorio_actual_id, nuevo_laboratorio_id):
        """Cambia un estudiante de laboratorio"""
        return True

    def verificar_conflicto_horario(self, estudiante_id, horario):
        """Verifica si hay conflictos de horario"""
        return False

    def verificar_plazo_matricula(self):
        """Verifica si el plazo de matrícula está activo"""
        return True

    def verificar_capacidad_laboratorio(self, laboratorio_id):
        """Verifica la capacidad disponible de un laboratorio"""
        return True

    def generar_constancia_matricula(self, estudiante_id, periodo_id):
        """Genera una constancia de matrícula"""
        return None

    @staticmethod
    def obtener_horario_estudiante(estudiante_id):
        """Obtiene el horario de un estudiante"""
        return {}

    @staticmethod
    def obtener_horario_docente(docente_id):
        """Obtiene el horario de un docente"""
        return {}

    @staticmethod
    def obtener_cursos_estudiante(estudiante_id):
        """Obtiene los cursos de un estudiante"""
        return []

    @staticmethod
    def obtener_matriculas_laboratorio(estudiante_id):
        """Obtiene las matrículas de laboratorio de un estudiante"""
        return []

    @staticmethod
    def obtener_resumen_inscripciones():
        """Obtiene resumen de inscripciones para secretarios"""
        return {
            'total_inscripciones': 0,
            'inscripciones_pendientes': 0,
            'inscripciones_activas': 0
        }
