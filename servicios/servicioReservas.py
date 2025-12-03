# servicios/servicioReservas.py

import logging
from datetime import time, datetime, timedelta
from typing import List, Dict, Tuple
from django.utils import timezone
from django.db.models import Q, Count

from repositorio.postgres_repository.models import (
    Reservation, Teacher, Classroom, Course,
    Horario, Aula
)
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

DIAS_NUM_A_STR = {
    0: "lunes", 1: "martes", 2: "miercoles",
    3: "jueves", 4: "viernes", 5: "sabado", 6: "domingo",
}

# === CONSTANTES DE RESTRICCIONES ===
MAX_RESERVAS_SEMANALES = 4  # Máximo de reservas por semana por profesor
MAX_DIAS_ANTICIPACION = 3   # Máximo de días de anticipación para reservar


class ServicioReservaAmbientes:
    """
    Servicio mejorado con validaciones automáticas:
    - Máximo 4 reservas por semana por profesor
    - Máximo 3 días de anticipación
    - Aprobación automática si cumple las reglas
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
    # VALIDACIONES DE RESTRICCIONES
    # ==========================
    
    def validar_restricciones(self, user, fecha_reserva) -> Tuple[bool, List[str]]:
        """
        Valida si el profesor puede hacer una reserva según las restricciones
        
        Returns:
            Tuple[bool, List[str]]: (puede_reservar, lista_de_errores)
        """
        try:
            teacher = Teacher.objects.get(user=user)
        except Teacher.DoesNotExist:
            return False, ["No se encontró un docente asociado al usuario."]
        
        errores = []
        
        # VALIDACIÓN 1: Máximo 4 reservas por semana
        inicio_semana = fecha_reserva - timedelta(days=fecha_reserva.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        reservas_semana = Reservation.objects.filter(
            teacher=teacher,
            date__gte=inicio_semana,
            date__lte=fin_semana,
            status__in=['approved', 'pending']
        ).count()
        
        self.logger.info(f"Profesor {teacher.id} tiene {reservas_semana} reservas esta semana")
        
        if reservas_semana >= MAX_RESERVAS_SEMANALES:
            errores.append(
                f"Ya tienes {reservas_semana} reservas esta semana. "
                f"El límite es {MAX_RESERVAS_SEMANALES} reservas por semana."
            )
        
        # VALIDACIÓN 2: Máximo 3 días de anticipación
        hoy = timezone.now().date()
        dias_anticipacion = (fecha_reserva - hoy).days
        
        self.logger.info(f"Reserva con {dias_anticipacion} días de anticipación")
        
        if dias_anticipacion > MAX_DIAS_ANTICIPACION:
            errores.append(
                f"Esta reserva es con {dias_anticipacion} días de anticipación. "
                f"El límite es {MAX_DIAS_ANTICIPACION} días."
            )
        
        if dias_anticipacion < 0:
            errores.append("No puedes reservar en fechas pasadas.")
        
        puede_reservar = len(errores) == 0
        
        return puede_reservar, errores

    def obtener_info_restricciones(self, user) -> Dict:
        """
        Devuelve información sobre las restricciones del profesor
        Útil para mostrar en el frontend
        """
        try:
            teacher = Teacher.objects.get(user=user)
        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'No se encontró un docente asociado.'
            }
        
        hoy = timezone.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        reservas_semana = Reservation.objects.filter(
            teacher=teacher,
            date__gte=inicio_semana,
            date__lte=fin_semana,
            status__in=['approved', 'pending']
        )
        
        total_semana = reservas_semana.count()
        reservas_restantes = max(0, MAX_RESERVAS_SEMANALES - total_semana)
        
        return {
            'success': True,
            'total_semana': total_semana,
            'limite_semana': MAX_RESERVAS_SEMANALES,
            'reservas_restantes': reservas_restantes,
            'max_dias_anticipacion': MAX_DIAS_ANTICIPACION,
            'puede_reservar': reservas_restantes > 0,
            'reservas_detalle': [
                {
                    'fecha': r.date.strftime('%Y-%m-%d'),
                    'aula': r.classroom.code if r.classroom else 'N/A',
                    'hora': f"{r.start_time.strftime('%H:%M')}-{r.end_time.strftime('%H:%M')}"
                }
                for r in reservas_semana.order_by('date', 'start_time')
            ]
        }

    # ==========================
    # ESTADO (ocupado/libre)
    # ==========================
    
    def obtener_estado(self, date, slot: str, user) -> List[Dict]:
        """
        Devuelve lista de ocupación con información de restricciones
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
                    "id": str(r.id),
                    "mine": mine,
                    "label": r.purpose[:40] if r.purpose else "",
                })

            self.logger.info(f"Estado obtenido: {len(ocupados)} ambientes ocupados")
            return ocupados

        except Exception as e:
            self.logger.error(f"Error obteniendo estado: {str(e)}")
            raise

    # ==========================
    # CREAR RESERVA (con validaciones automáticas)
    # ==========================
    
    def crear_reserva(self, user, resource_code: str, date, slot: str, purpose: str = None):
        """
        Crea una reserva CON VALIDACIONES AUTOMÁTICAS
        - Valida restricciones de semana y anticipación
        - Aprobación automática si cumple las reglas
        - Rechaza automáticamente si no cumple
        """
        try:
            start_time, end_time = self._slot_to_times(slot)
            dia_nombre = self._dia_nombre(date)

            self.logger.info(
                f"Creando reserva - Usuario: {user.id}, "
                f"Ambiente: {resource_code}, Fecha: {date}, Slot: {slot}"
            )

            # 1) Localizar al docente
            try:
                teacher = Teacher.objects.get(user=user)
                self.logger.debug(f"Docente encontrado: {teacher.id}")
            except Teacher.DoesNotExist:
                error_msg = "No se encontró un docente asociado al usuario."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # 2) VALIDAR RESTRICCIONES
            puede_reservar, errores = self.validar_restricciones(user, date)
            
            if not puede_reservar:
                error_msg = " ".join(errores)
                self.logger.warning(f"Restricciones no cumplidas: {error_msg}")
                raise ValueError(error_msg)

            # 3) Localizar el aula
            classroom = Classroom.objects.filter(code=resource_code).first()
            if not classroom:
                classroom = Classroom.objects.filter(name=resource_code).first()
            if not classroom:
                error_msg = f"No se encontró el ambiente '{resource_code}'."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.debug(f"Ambiente encontrado: {classroom.id} - {classroom.code}")

            # 4) Elegir un curso
            course = Course.objects.first()
            if not course:
                error_msg = "No hay cursos registrados para asociar la reserva."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.debug(f"Curso asignado: {course.id} - {course.name}")

            # 5) Verificar conflictos con HORARIO
            if Horario.objects.filter(
                dia_semana__iexact=dia_nombre,
                hora_inicio=start_time,
                hora_fin=end_time,
                aula__codigo=resource_code
            ).exists():
                error_msg = "El ambiente está ocupado por una clase en ese horario."
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

            # 6) Verificar conflictos con otras RESERVAS
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

            # 7) CREAR LA RESERVA CON APROBACIÓN AUTOMÁTICA
            reserva = Reservation.objects.create(
                teacher=teacher,
                classroom=classroom,
                course=course,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='approved',  # ✅ Aprobación automática
                purpose=purpose or 'Reserva de ambiente',
                approved_by=None,
            )

            self.logger.info(
                f"✅ Reserva creada y aprobada automáticamente: {reserva.id}"
            )
            
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
                self.logger.warning(
                    f"Intento de eliminar reserva no propia - "
                    f"Usuario: {user.id}, Dueño: {reserva.teacher.user_id if reserva.teacher else 'None'}"
                )
                raise PermissionError(error_msg)

            reserva.delete()
            self.logger.info(f"Reserva eliminada exitosamente: {reserva_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error eliminando reserva: {str(e)}")
            raise

    def obtener_reservas_profesor(self, user):
        """
        Devuelve TODAS las reservas del profesor
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

    # ==========================
    # REPORTES Y ESTADÍSTICAS
    # ==========================
    
    def obtener_reporte_semanal(self, fecha_inicio=None) -> Dict:
        """
        Genera un reporte de reservas de la semana
        """
        if not fecha_inicio:
            fecha_inicio = timezone.now().date()
        
        inicio_semana = fecha_inicio - timedelta(days=fecha_inicio.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        reservas = Reservation.objects.filter(
            date__gte=inicio_semana,
            date__lte=fin_semana
        ).select_related('teacher__user', 'classroom')
        
        total = reservas.count()
        aprobadas = reservas.filter(status='approved').count()
        rechazadas = reservas.filter(status='rejected').count()
        
        # Profesores con más reservas
        top_profesores = reservas.values(
            'teacher__user__first_name',
            'teacher__user__last_name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5]
        
        # Aulas más usadas
        top_aulas = reservas.filter(
            status='approved'
        ).values(
            'classroom__code',
            'classroom__name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5]
        
        return {
            'periodo': f"{inicio_semana.strftime('%d/%m/%Y')} - {fin_semana.strftime('%d/%m/%Y')}",
            'total_reservas': total,
            'aprobadas': aprobadas,
            'rechazadas': rechazadas,
            'tasa_aprobacion': round((aprobadas / total * 100), 1) if total > 0 else 0,
            'top_profesores': list(top_profesores),
            'top_aulas': list(top_aulas),
        }


# Instancia global
servicio_reservas = ServicioReservaAmbientes()