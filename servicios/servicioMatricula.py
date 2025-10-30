#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import time, timedelta, datetime
import random

from dominio.modelo.inscripciones.laboratorio import Laboratorio
from dominio.modelo.inscripciones.matriculaLaboratorio import MatriculaLaboratorio

class ServicioMatricula:
    def __init__(self, repo):
        self.repo = repo
        # Por ahora no usamos repositorios, solo session (modo demo)

    # ======================================================
    # --------------- GENERADOR DE HORARIOS ----------------
    # ======================================================
    @staticmethod
    def _random_hour_block():
        """
        Genera un bloque horario de 2 horas dentro de 08:00-18:00.
        Retorna dict {'start': time, 'end': time}
        """
        start_hour = random.randint(8, 16)  # inicio entre 8 y 16
        start_min = random.choice([0, 30])
        start = time(start_hour, start_min)
        end_hour = min(start_hour + 2, 23)
        end = time(end_hour, start_min)
        return {'start': start, 'end': end}

    # ======================================================
    # ----------- GENERACIÓN DE LABORATORIOS ---------------
    # ======================================================
    def generar_labs_para_enrollment(self, enrollment_id, curso_nombre, curso_codigo, session):
        """
        Genera 2 laboratorios (A y B) por curso si aún no existen.
        Guarda la información en session['labs_generados'].
        """
        if 'labs_generados' not in session:
            session['labs_generados'] = {}

        labs_store = session['labs_generados']

        # Si ya existe, no regenerar
        if str(enrollment_id) in labs_store:
            return labs_store[str(enrollment_id)]

        # Crear horario del curso
        horario_curso = self._random_hour_block()

        # Crear laboratorios A y B
        labA_h = self._random_hour_block()
        labB_h = self._random_hour_block()

        labA = Laboratorio(
            codigo=f"{curso_codigo}-A",
            nombre=f"{curso_nombre} - Lab A",
            capacidad_maxima=20,
            horario=labA_h
        )
        labB = Laboratorio(
            codigo=f"{curso_codigo}-B",
            nombre=f"{curso_nombre} - Lab B",
            capacidad_maxima=20,
            horario=labB_h
        )

        # Guardar versión serializable en sesión
        labs_store[str(enrollment_id)] = {
            'horario_curso': {
                'start': horario_curso['start'].isoformat(),
                'end': horario_curso['end'].isoformat()
            },
            'labs': {
                'A': {
                    'codigo': labA.codigo,
                    'nombre': labA.nombre,
                    'capacidad': labA.capacidad_maxima,
                    'horario': {
                        'start': labA.horario['start'].isoformat(),
                        'end': labA.horario['end'].isoformat()
                    }
                },
                'B': {
                    'codigo': labB.codigo,
                    'nombre': labB.nombre,
                    'capacidad': labB.capacidad_maxima,
                    'horario': {
                        'start': labB.horario['start'].isoformat(),
                        'end': labB.horario['end'].isoformat()
                    }
                },
            },
            'generado_en': datetime.now().isoformat()
        }

        session.modified = True
        return labs_store[str(enrollment_id)]

    # ======================================================
    # ------------- MATRÍCULA EN LABORATORIO ---------------
    # ======================================================
    def matricular_laboratorio(self, request, estudiante_id, enrollment_id, opcion_lab_key):
        """
        Matricula un estudiante en el laboratorio A o B de un curso.
        Valida:
        - Plazo de 7 días desde la generación
        - No conflicto con horario del curso
        - Capacidad máxima (20)
        """
        labs_store = request.session.get('labs_generados', {})
        item = labs_store.get(str(enrollment_id))
        if not item:
            return False, "No se encontraron laboratorios generados para este curso."

        # Verificar plazo de 7 días desde generación
        gen_dt = datetime.fromisoformat(item['generado_en'])
        if datetime.now() > (gen_dt + timedelta(days=7)):
            return False, "El plazo para matricular en este laboratorio ha expirado."

        # Datos del curso y laboratorio
        curso_h = {
            'start': datetime.fromisoformat(item['horario_curso']['start']).time(),
            'end': datetime.fromisoformat(item['horario_curso']['end']).time()
        }
        lab_key = opcion_lab_key.upper()
        if lab_key not in item['labs']:
            return False, "Opción de laboratorio inválida."

        lab_info = item['labs'][lab_key]
        lab_h = {
            'start': datetime.fromisoformat(lab_info['horario']['start']).time(),
            'end': datetime.fromisoformat(lab_info['horario']['end']).time()
        }

        # Verificar conflicto de horarios
        s1, e1 = lab_h['start'], lab_h['end']
        s2, e2 = curso_h['start'], curso_h['end']
        conflict = (s1 < e2) and (s2 < e1)
        if conflict:
            return False, "El horario del laboratorio se cruza con el curso."

        # Verificar capacidad
        matriculas = request.session.get('matriculas_labs', {})
        inscritos = sum(1 for m in matriculas.values() if m.get('lab_codigo') == lab_info['codigo'])
        if inscritos >= lab_info['capacidad']:
            return False, "El laboratorio ya alcanzó su capacidad máxima."

        # Registrar matrícula
        matriculas[str(enrollment_id)] = {
            'estudiante_id': estudiante_id,
            'lab_codigo': lab_info['codigo'],
            'lab_key': lab_key,
            'fecha_matricula': datetime.now().isoformat()
        }
        request.session['matriculas_labs'] = matriculas
        request.session.modified = True
        return True, f"Te has matriculado en el Laboratorio {lab_key}."

    # ======================================================
    # ------------- DESMATRICULAR LABORATORIO --------------
    # ======================================================
    def desmatricular_laboratorio(self, request, estudiante_id, enrollment_id):
        matriculas = request.session.get('matriculas_labs', {})
        if str(enrollment_id) in matriculas:
            del matriculas[str(enrollment_id)]
            request.session['matriculas_labs'] = matriculas
            request.session.modified = True
            return True, "Te has desmatriculado correctamente."
        return False, "No tienes matrícula activa en este laboratorio."

    # ======================================================
    # ----------- UTILIDAD PARA LA VISTA CURSOS ------------
    # ======================================================
    def preparar_contexto_enrollments(self, request, enrollments_qs):
        """
        Combina datos de cursos (enrollments) + labs + estado actual
        para usar directamente en el template.
        """
        resultado = []
        for e in enrollments_qs:
            enrollment_id = e.id

            # Generar labs si no existen
            gen = self.generar_labs_para_enrollment(
                enrollment_id,
                e.course_group.course.name,
                getattr(e.course_group.course, 'code', 'CUR'),
                request.session
            )

            # Verificar si el estudiante ya tiene lab asignado
            matriculas = request.session.get('matriculas_labs', {})
            asignado = matriculas.get(str(enrollment_id))

            item = {
                'enrollment': e,
                'enrollment_id': enrollment_id,
                'curso_nombre': e.course_group.course.name,
                'curso_codigo': getattr(e.course_group.course, 'code', 'CUR'),
                'horario_curso': gen['horario_curso'],
                'labs': gen['labs'],
                'asignado': asignado,  # None o dict con lab_key y lab_codigo
            }
            resultado.append(item)
        return resultado

    # ======================================================
    # ----------- OBTENER HORARIO SEMANAL ESTUDIANTE -------
    # ======================================================
    def obtener_horario_estudiante(self, request, estudiante_id):
        """
        Combina cursos y laboratorios matriculados en un horario semanal.
        """
        enrollments_qs = request.session.get('labs_generados', {})
        matriculas = request.session.get('matriculas_labs', {})

        if not enrollments_qs:
            return []

        horario = []

        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

        for enrollment_id, data in enrollments_qs.items():
            curso_nombre = f"Curso {enrollment_id}"
            curso_horario = data['horario_curso']
            try:
                start = datetime.fromisoformat(curso_horario['start']).time()
                end = datetime.fromisoformat(curso_horario['end']).time()
            except Exception as e:
                print(f"[ERROR horario curso] {e} -> {curso_horario}")
                continue

            # Asignar día aleatorio solo visual (puedes luego vincular real)
            dia = random.choice(dias_semana)
            horario.append({
                "curso_nombre": curso_nombre,
                "es_laboratorio": False,
                "aula": "Aula 101",
                "profesor": "Por asignar",
                "dia": dia,
                "inicio": start.strftime("%H:%M"),
                "fin": end.strftime("%H:%M")
            })

            # Si tiene laboratorio matriculado
            matricula = matriculas.get(str(enrollment_id))
            if matricula:
                lab_key = matricula['lab_key']
                lab_info = data['labs'][lab_key]
                lab_h = lab_info['horario']
                try:
                    lab_start = datetime.fromisoformat(lab_h['start']).time()
                    lab_end = datetime.fromisoformat(lab_h['end']).time()
                except Exception as e:
                    print(f"[ERROR horario lab] {e} -> {lab_h}")
                    continue

                dia_lab = random.choice(dias_semana)

                horario.append({
                    "curso_nombre": f"{curso_nombre} - Lab {lab_key}",
                    "es_laboratorio": True,
                    "aula": f"Lab {lab_key}",
                    "profesor": "Por asignar",
                    "dia": dia_lab,
                    "inicio": lab_start.strftime("%H:%M"),
                    "fin": lab_end.strftime("%H:%M")
                })

        return horario


    # ======================================================
    # ------------ FUNCIONES ORIGINALES (PLACEHOLDER) ------
    # ======================================================
    def procesar_lista_matricula(self, archivo_excel, periodo_id):
        # Lógica previa tuya (para crear estudiantes desde Excel)
        pass

    def obtener_cursos_matriculados(self, estudiante_id):
        return []

    def verificar_conflicto_horario(self, estudiante_id, horario):
        return False

    def verificar_plazo_matricula(self):
        return True

    def verificar_capacidad_laboratorio(self, laboratorio_id):
        return True
