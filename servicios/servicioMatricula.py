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

            est = Estudiante(student_id= cui)
            
              # asignar atributos manualmente (heredados de Usuario)
            est.nombre = nombres
            est.apellido = apellidos
            est.año_ingreso = anio_ingreso  

            self.repo.guardar(est)
            estudiantes.append(est)

        return estudiantes

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
