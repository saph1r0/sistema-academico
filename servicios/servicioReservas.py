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

MAX_RESERVAS_SEMANALES = 10

class ServicioReservaAmbientes:
    """
    Servicio mejorado con validaciones automáticas:
    - Máximo 10 reservas por semana por profesor
    - Aprobación automática si cumple las reglas
    - Soporte para admin (sin restricciones)
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

    def _es_admin(self, user):
        """Verifica si el usuario es administrador o staff"""
        return user.is_staff or user.is_superuser
    def _es_secretaria(self, user):
        return user.groups.filter(name__iexact="secretary").exists()

    # ==========================
    # VALIDACIONES DE RESTRICCIONES
    # ==========================
    
    def validar_restricciones(self, user, fecha_reserva) -> Tuple[bool, List[str]]:
        """
        Valida si el usuario puede hacer una reserva
        Admin no tiene restricciones
        """
        # Admin puede hacer reservas sin restricciones
        if self._es_admin(user) or self._es_secretaria(user):
            return True, []
        
        try:
            teacher = Teacher.objects.get(user=user)
        except Teacher.DoesNotExist:
            return False, ["No se encontró un docente asociado al usuario."]
        
        errores = []
        
        # VALIDACIÓN 1: Máximo 10 reservas por semana
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
        
        # VALIDACIÓN 2: Fechas pasadas
        hoy = timezone.now().date()
        dias_anticipacion = (fecha_reserva - hoy).days

        if dias_anticipacion < 0:
            errores.append("No puedes reservar en fechas pasadas.")
        
        puede_reservar = len(errores) == 0
        
        return puede_reservar, errores

    def obtener_info_restricciones(self, user) -> Dict:
        """
        Devuelve información sobre las restricciones del usuario
        """
        # Admin no tiene restricciones
        if self._es_admin(user):
            return {
                'success': True,
                'total_semana': 0,
                'limite_semana': 'Sin límite',
                'reservas_restantes': 'Ilimitadas',
                'puede_reservar': True,
                'es_admin': True,
                'reservas_detalle': []
            }
        
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
            'puede_reservar': reservas_restantes > 0,
            'es_admin': False,
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
            # 2) OCUPADO POR RESERVAS (solo activas)
            # ----------------------
            reservas = Reservation.objects.filter(
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='approved'  # Solo mostrar reservas activas
            ).select_related('classroom', 'teacher__user')

            for r in reservas:
                code = getattr(r.classroom, 'code', None) or getattr(r.classroom, 'name', None)
                if not code:
                    continue

                mine = False
                # Para profesor, verificar si es suya
                if r.teacher and r.teacher.user_id == user.id:
                    mine = True
                # Para admin, considerar como propia para poder editar
                elif self._es_admin(user):
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
        Admin puede reservar sin restricciones
        """
        try:
            start_time, end_time = self._slot_to_times(slot)
            dia_nombre = self._dia_nombre(date)

            self.logger.info(
                f"Creando reserva - Usuario: {user.id}, "
                f"Ambiente: {resource_code}, Fecha: {date}, Slot: {slot}"
            )

            # 1) Localizar al docente (si no es admin)
            teacher = None
            if not self._es_admin(user) and not self._es_secretaria(user):
                try:
                    teacher = Teacher.objects.get(user=user)
                    self.logger.debug(f"Docente encontrado: {teacher.id}")
                except Teacher.DoesNotExist:
                    error_msg = "No se encontró un docente asociado al usuario."
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)

                # 2) VALIDAR RESTRICCIONES (solo para profesores)
                puede_reservar, errores = self.validar_restricciones(user, date)
                
                if not puede_reservar:
                    error_msg = " ".join(errores)
                    self.logger.warning(f"Restricciones no cumplidas: {error_msg}")
                    raise ValueError(error_msg)

            # 3) Localizar el aula
            resource_code = str(resource_code).strip()

            classroom = (
                Classroom.objects.filter(
                    Q(code__iexact=resource_code) | Q(name__iexact=resource_code)
                ).first()
            )

            if not classroom:
                classroom = (
                    Classroom.objects.filter(
                        Q(code__icontains=resource_code) | Q(name__icontains=resource_code)
                    ).first()
                )

            if not classroom:
                error_msg = f"No se encontró el ambiente que contenga '{resource_code}'."
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

            # 6) Verificar conflictos con otras RESERVAS ACTIVAS
            if Reservation.objects.filter(
                classroom=classroom,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='approved'  # Solo verificar reservas activas
            ).exists():
                error_msg = "El ambiente ya está reservado en ese horario."
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

            # 7) CREAR LA RESERVA CON APROBACIÓN AUTOMÁTICA (ACTIVO)
            reserva = Reservation.objects.create(
                teacher=teacher,  # Puede ser None para admin
                classroom=classroom,
                course=course,
                date=date,
                start_time=start_time,
                end_time=end_time,
                status='approved',  # ✅ Activo por defecto
                purpose=purpose or 'Reserva de ambiente',
                approved_by=user if self._es_admin(user) else None,
            )

            self.logger.info(
                f"✅ Reserva creada y aprobada automáticamente: {reserva.id}"
            )
            
            return reserva

        except Exception as e:
            self.logger.error(f"Error creando reserva: {str(e)}")
            raise

    # ==========================
    # ELIMINAR/CANCELAR RESERVA
    # ==========================
    
    def eliminar_reserva(self, user, reserva_id):
        """
        Cambia el estado de la reserva a 'cancelled' (Inactivo)
        - Profesor: solo puede cancelar sus propias reservas
        - Admin: puede cancelar cualquier reserva
        """
        try:
            self.logger.info(f"Cancelando reserva - Usuario: {user.id}, Reserva: {reserva_id}")

            try:
                reserva = Reservation.objects.select_related('teacher__user').get(id=reserva_id)
                self.logger.debug(f"Reserva encontrada: {reserva.id}")
            except Reservation.DoesNotExist:
                error_msg = "Reserva no encontrada."
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Verificar permisos
            es_admin = self._es_admin(user)
            es_dueno = reserva.teacher and reserva.teacher.user_id == user.id
            
            if not es_admin and not es_dueno:
                error_msg = "No tienes permiso para cancelar esta reserva."
                self.logger.warning(
                    f"Intento de cancelar reserva sin permiso - "
                    f"Usuario: {user.id}, Dueño: {reserva.teacher.user_id if reserva.teacher else 'None'}"
                )
                raise PermissionError(error_msg)

            # Cambiar estado a 'cancelled' (Inactivo) en lugar de eliminar
            reserva.status = 'cancelled'
            reserva.save()
            
            self.logger.info(f"Reserva cancelada exitosamente: {reserva_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error cancelando reserva: {str(e)}")
            raise

    def obtener_reservas_profesor(self, user):
        """
        Devuelve TODAS las reservas del usuario
        - Profesor: solo sus reservas
        - Admin: todas las reservas
        """
        es_admin = self._es_admin(user)
        es_secretaria = self._es_secretaria(user)
        
        if es_admin or es_secretaria:
            # Admin ve todas las reservas
            return (
                Reservation.objects
                .select_related("classroom", "course", "teacher__user")
                .order_by("-date", "start_time")
            )
        
        # Profesor ve solo sus reservas
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
        canceladas = reservas.filter(status='cancelled').count()
        
        # Profesores con más reservas
        top_profesores = reservas.filter(
            status='approved'
        ).values(
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
            'activas': aprobadas,
            'canceladas': canceladas,
            'tasa_activas': round((aprobadas / total * 100), 1) if total > 0 else 0,
            'top_profesores': list(top_profesores),
            'top_aulas': list(top_aulas),
        }


# Instancia global
servicio_reservas = ServicioReservaAmbientes()