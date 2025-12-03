# servicios/servicioReservas.py

import logging
from datetime import time, datetime
from typing import List, Dict

from django.db.models import Q

# Ajusta este import según tu proyecto
from repositorio.postgres_repository.models import (
    Reservation, Teacher, Classroom, Course,
    Horario, Aula
)

# Configurar logger
logger = logging.getLogger(__name__)

# Mapeo de slots a horas reales
SLOTS = {
    "07:00/07:50": (time(7, 0),  time(7, 50)),
    "07:50/08:40": (time(7, 50), time(8, 40)),
    "08:50/09:40": (time(8, 50), time(9, 40)),
    "09:40/10:30": (time(9, 40), time(10, 30)),
    "10:40/11:30": (time(10, 40), time(11, 30)),
    "11:30/12:20": (time(11, 30), time(12, 20)),
    "12:20/13:10": (time(12, 20), time(13, 10)),
    "13:10/14:00": (time(13, 10), time(14, 0)),
    "14:00/14:50": (time(14, 0), time(14, 50)),
    "14:50/15:40": (time(14, 50), time(15, 40)),
    "15:50/16:40": (time(15, 50), time(16, 40)),
    "16:40/17:30": (time(16, 40), time(17, 30)),
    "17:40/18:30": (time(17, 40), time(18, 30)),
    "18:30/19:20": (time(18, 30), time(19, 20)),
    "19:20/20:10": (time(19, 20), time(20, 10)),
}

# weekday(): lunes=0 ... domingo=6
DIAS_NUM_A_STR = {
    0: "lunes",
    1: "martes",
    2: "miercoles",   # ajusta si en tu BD usas "miércoles"
    3: "jueves",
    4: "viernes",
    5: "sabado",
    6: "domingo",
}


class ServicioReservaAmbientes:
    """
    Usa:
      - Horario + Aula -> ocupación por clases
      - Reservation    -> ocupación por reservas (tu modelo)
    """

    def __init__(self):
        self.logger = logger

    def _slot_to_times(self, slot: str):
        try:
            if slot not in SLOTS:
                raise ValueError("Slot no válido")
            return SLOTS[slot]
        except Exception as e:
            self.logger.error(f"Error convirtiendo slot a tiempos: {str(e)}")
            raise

    def _dia_nombre(self, date):
        return DIAS_NUM_A_STR[date.weekday()]

    # ==========================
    # ESTADO (ocupado/libre)
    # ==========================
    def obtener_estado(self, date, slot: str, user) -> List[Dict]:
        """
        Devuelve lista de ocupación:
        [
          { "code": "A-101", "reason": "class", "label": "Álgebra Lineal" },
          { "code": "A-201", "reason": "reservation", "id": "...", "mine": true },
          ...
        ]
        """
        try:
            start_time, end_time = self._slot_to_times(slot)
            dia_nombre = self._dia_nombre(date)
            ocupados = []

            self.logger.info(f"Consultando estado para fecha: {date}, slot: {slot}, usuario: {user.id}")

            # ----------------------
            # 1) OCUPADO POR HORARIO
            # ----------------------
            horarios = Horario.objects.filter(
                dia_semana__iexact=dia_nombre,
                hora_inicio=start_time,
                hora_fin=end_time,
            ).select_related('aula', 'course_group__course')

            for h in horarios:
                if not h.aula:
                    continue
                # IMPORTANTE: usa el campo que coincida con el ID del front
                code = getattr(h.aula, 'codigo', None) or getattr(h.aula, 'name', None)
                if not code:
                    continue

                label = "Clase"
                if hasattr(h, 'course_group') and h.course_group and h.course_group.course:
                    label = h.course_group.course.name

                ocupados.append({
                    "code": code,
                    "reason": "class",
                    "label": label,
                })

            # ----------------------
            # 2) OCUPADO POR RESERVAS
            # ----------------------
            reservas = Reservation.objects.filter(
                date=date,
                start_time=start_time,
                end_time=end_time,
            ).exclude(
                status__in=['cancelled', 'rejected']
            ).select_related('classroom', 'teacher__user')

            for r in reservas:
                code = getattr(r.classroom, 'code', None) or getattr(r.classroom, 'name', None)
                if not code:
                    continue

                mine = False
                if r.teacher and r.teacher.user_id == user.id:
                    mine = True

                ocupados.append({
                    "code": code,
                    "reason": "reservation",
                    "id": str(r.id),   # UUID a string para el front
                    "mine": mine,
                    "label": r.purpose[:40] if r.purpose else "",
                })

            self.logger.info(f"Estado obtenido: {len(ocupados)} ambientes ocupados")
            return ocupados

        except Exception as e:
            self.logger.error(f"Error obteniendo estado: {str(e)}")
            raise

    # ==========================
    # CREAR RESERVA
    # ==========================
    def crear_reserva(self, user, resource_code: str, date, slot: str):
        """
        Crea una reserva simple para el docente logueado.
        Por ahora:
          - Usa el primer Course existente (luego lo puedes afinar).
          - status = 'approved' directamente.
        """
        try:
            start_time, end_time = self._slot_to_times(slot)
            dia_nombre = self._dia_nombre(date)

            self.logger.info(f"Creando reserva - Usuario: {user.id}, Ambiente: {resource_code}, Fecha: {date}, Slot: {slot}")

            # 1) Localizar al docente
            try:
                teacher = Teacher.objects.get(user=user)
                self.logger.debug(f"Docente encontrado: {teacher.id}")
            except Teacher.DoesNotExist:
                error_msg = "No se encontró un docente asociado al usuario."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # 2) Localizar el aula
            # Usa el campo que tengas: code, codigo, name...
            classroom = Classroom.objects.filter(code__icontains=resource_code).first()
            if not classroom:
                classroom = Classroom.objects.filter(name__icontains=resource_code).first()

            if not classroom:
                error_msg = f"No se encontró el ambiente '{resource_code}'."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.debug(f"Ambiente encontrado: {classroom.id} - {classroom.code}")

            # 3) Elegir un curso (versión simple)
            course = Course.objects.first()
            if not course:
                error_msg = "No hay cursos registrados para asociar la reserva."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.debug(f"Curso asignado: {course.id} - {course.name}")

            # 4) Verificar conflictos con HORARIO
            if Horario.objects.filter(
                dia_semana__iexact=dia_nombre,
                hora_inicio=start_time,
                hora_fin=end_time,
                aula__codigo=resource_code   # ajusta si es aula__name, etc.
            ).exists():
                error_msg = "El ambiente está ocupado por una clase en ese horario."
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

            # 5) Verificar conflictos con otras RESERVAS
            if Reservation.objects.filter(
                classroom=classroom,
                date=date,
                start_time=start_time,
                end_time=end_time
            ).exclude(
                status__in=['cancelled', 'rejected']
            ).exists():
                error_msg = "El ambiente ya está reservado en ese horario."
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

            # 6) Crear la reserva (simple)
            reserva = Reservation.objects.create(
                teacher=teacher,
                classroom=classroom,
                course=course,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='approved',      # así ya cuenta como ocupada
                purpose='Reserva rápida de aula',  # luego lo puedes pedir en el formulario
                approved_by=None,
            )

            self.logger.info(f"Reserva creada exitosamente: {reserva.id}")
            return reserva

        except Exception as e:
            self.logger.error(f"Error creando reserva: {str(e)}")
            raise

    # ==========================
    # ELIMINAR RESERVA
    # ==========================
    def eliminar_reserva(self, user, reserva_id):
        """
        Elimina solo reservas creadas por el mismo docente.
        """
        try:
            self.logger.info(f"Eliminando reserva - Usuario: {user.id}, Reserva: {reserva_id}")

            try:
                reserva = Reservation.objects.select_related('teacher__user').get(id=reserva_id)
                self.logger.debug(f"Reserva encontrada: {reserva.id}")
            except Reservation.DoesNotExist:
                error_msg = "Reserva no encontrada."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            if not reserva.teacher or reserva.teacher.user_id != user.id:
                error_msg = "No puedes eliminar esta reserva."
                self.logger.warning(f"Intento de eliminar reserva no propia - Usuario: {user.id}, Dueño real: {reserva.teacher.user_id if reserva.teacher else 'None'}")
                raise PermissionError(error_msg)

            reserva.delete()
            self.logger.info(f"Reserva eliminada exitosamente: {reserva_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error eliminando reserva: {str(e)}")
            raise

    def obtener_reservas_profesor(self, user):
        """
        Devuelve TODAS las reservas del profesor (sin filtrar por fecha ni hora).
        """
        teacher = getattr(user, "teacher", None)
        if teacher is None:
            return Reservation.objects.none()

        return (
            Reservation.objects
            .filter(teacher=teacher)
            .select_related("classroom", "course")
            .order_by("-date", "start_time")
        )
        
# Instancia global para usar en vistas
servicio_reservas = ServicioReservaAmbientes()