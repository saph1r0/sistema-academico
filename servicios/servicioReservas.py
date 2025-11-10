#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de reservas de ambientes
Maneja reserva automática de 9 ambientes (3 pisos)
"""

import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date, time

from repositorio.postgres_repository.models import (
    Teacher, Course, Classroom, Reservation, User
)

logger = logging.getLogger(__name__)


class ServicioReservas:
    """
    Servicio para manejo de reservas de ambientes
    """
    
    # Definición de los 9 ambientes
    AMBIENTES = {
        'piso_1': [
            {'code': '101', 'name': 'Aula 101', 'type': 'classroom', 'capacity': 40},
            {'code': '102', 'name': 'Aula 102', 'type': 'classroom', 'capacity': 40},
            {'code': '103', 'name': 'Laboratorio 103', 'type': 'laboratory', 'capacity': 30}
        ],
        'piso_2': [
            {'code': '201', 'name': 'Aula 201', 'type': 'classroom', 'capacity': 40},
            {'code': '202', 'name': 'Aula 202', 'type': 'classroom', 'capacity': 40},
            {'code': '203', 'name': 'Aula 203', 'type': 'classroom', 'capacity': 40}
        ],
        'piso_3': [
            {'code': '301', 'name': 'Laboratorio 301', 'type': 'laboratory', 'capacity': 30},
            {'code': '302', 'name': 'Laboratorio 302', 'type': 'laboratory', 'capacity': 30},
            {'code': '303', 'name': 'Laboratorio 303', 'type': 'laboratory', 'capacity': 30}
        ]
    }
    
    def __init__(self):
        self.logger = logger
        self._inicializar_ambientes()
    
    def _inicializar_ambientes(self):
        """Crear los ambientes en la base de datos si no existen"""
        try:
            for piso, ambientes in self.AMBIENTES.items():
                for ambiente_data in ambientes:
                    classroom, created = Classroom.objects.get_or_create(
                        code=ambiente_data['code'],
                        defaults={
                            'name': ambiente_data['name'],
                            'room_type': ambiente_data['type'],
                            'capacity': ambiente_data['capacity'],
                            'location': f'Piso {piso.split("_")[1]}',
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.logger.info(f"Ambiente creado: {classroom.name}")
        
        except Exception as e:
            self.logger.error(f"Error inicializando ambientes: {str(e)}")
    
    def obtener_ambientes_disponibles(self, fecha: date, hora_inicio: time, 
                                    hora_fin: time, tipo_ambiente: str = None) -> Dict:
        """
        Obtener ambientes disponibles para una fecha y horario específico
        
        Args:
            fecha: Fecha de la reserva
            hora_inicio: Hora de inicio
            hora_fin: Hora de fin
            tipo_ambiente: Tipo de ambiente ('classroom' o 'laboratory')
            
        Returns:
            Dict con ambientes disponibles
        """
        try:
            # Filtrar ambientes por tipo si se especifica
            ambientes_query = Classroom.objects.filter(is_active=True)
            if tipo_ambiente:
                ambientes_query = ambientes_query.filter(room_type=tipo_ambiente)
            
            # Obtener reservas existentes para la fecha y horario
            reservas_conflicto = Reservation.objects.filter(
                date=fecha,
                status__in=['pending', 'approved']
            ).filter(
                Q(start_time__lt=hora_fin) & Q(end_time__gt=hora_inicio)
            )
            
            # IDs de ambientes ocupados
            ambientes_ocupados = set(reservas_conflicto.values_list('classroom_id', flat=True))
            
            # Filtrar ambientes disponibles
            ambientes_disponibles = ambientes_query.exclude(id__in=ambientes_ocupados)
            
            # Organizar por piso
            ambientes_por_piso = {
                'piso_1': [],
                'piso_2': [],
                'piso_3': []
            }
            
            for ambiente in ambientes_disponibles:
                # Determinar piso basado en el código
                if ambiente.code.startswith('1'):
                    piso = 'piso_1'
                elif ambiente.code.startswith('2'):
                    piso = 'piso_2'
                elif ambiente.code.startswith('3'):
                    piso = 'piso_3'
                else:
                    continue
                
                ambientes_por_piso[piso].append({
                    'classroom_id': str(ambiente.id),
                    'code': ambiente.code,
                    'name': ambiente.name,
                    'type': ambiente.room_type,
                    'capacity': ambiente.capacity,
                    'location': ambiente.location,
                    'equipment': ambiente.equipment
                })
            
            # Contar totales
            total_disponibles = sum(len(ambientes) for ambientes in ambientes_por_piso.values())
            total_ocupados = len(ambientes_ocupados)
            
            return {
                'success': True,
                'fecha': fecha.isoformat(),
                'horario': {
                    'hora_inicio': hora_inicio.isoformat(),
                    'hora_fin': hora_fin.isoformat()
                },
                'tipo_ambiente': tipo_ambiente or 'Todos',
                'ambientes_por_piso': ambientes_por_piso,
                'estadisticas': {
                    'total_disponibles': total_disponibles,
                    'total_ocupados': total_ocupados,
                    'total_ambientes': 9
                },
                'fecha_consulta': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ambientes disponibles: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def reservar_ambiente_automatico(self, teacher_id: str, course_id: str, 
                                   fecha: date, hora_inicio: time, hora_fin: time,
                                   proposito: str, tipo_preferido: str = None) -> Dict:
        """
        Reservar automáticamente el mejor ambiente disponible
        
        Args:
            teacher_id: ID del profesor
            course_id: ID del curso
            fecha: Fecha de la reserva
            hora_inicio: Hora de inicio
            hora_fin: Hora de fin
            proposito: Propósito de la reserva
            tipo_preferido: Tipo de ambiente preferido
            
        Returns:
            Dict con resultado de la reserva
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            course = Course.objects.get(id=course_id)
            
            with transaction.atomic():
                # Obtener ambientes disponibles
                disponibles = self.obtener_ambientes_disponibles(
                    fecha, hora_inicio, hora_fin, tipo_preferido
                )
                
                if not disponibles['success']:
                    return disponibles
                
                # Buscar el mejor ambiente disponible
                mejor_ambiente = None
                
                # Prioridad: laboratorios para cursos prácticos, aulas para teóricos
                if tipo_preferido == 'laboratory':
                    # Buscar en pisos 1 y 3 (que tienen labs)
                    for piso in ['piso_3', 'piso_1']:  # Piso 3 primero (más labs)
                        if disponibles['ambientes_por_piso'][piso]:
                            mejor_ambiente = disponibles['ambientes_por_piso'][piso][0]
                            break
                else:
                    # Buscar aulas (piso 1 y 2)
                    for piso in ['piso_2', 'piso_1']:
                        ambientes_piso = [
                            a for a in disponibles['ambientes_por_piso'][piso]
                            if a['type'] == 'classroom'
                        ]
                        if ambientes_piso:
                            mejor_ambiente = ambientes_piso[0]
                            break
                
                # Si no encontró del tipo preferido, tomar cualquiera
                if not mejor_ambiente:
                    for piso in ['piso_1', 'piso_2', 'piso_3']:
                        if disponibles['ambientes_por_piso'][piso]:
                            mejor_ambiente = disponibles['ambientes_por_piso'][piso][0]
                            break
                
                if not mejor_ambiente:
                    return {
                        'success': False,
                        'error': 'No hay ambientes disponibles para el horario solicitado',
                        'error_code': 'NO_ROOMS_AVAILABLE'
                    }
                
                # Crear la reserva
                classroom = Classroom.objects.get(id=mejor_ambiente['classroom_id'])
                
                reservation = Reservation.objects.create(
                    teacher=teacher,
                    classroom=classroom,
                    course=course,
                    date=fecha,
                    start_time=hora_inicio,
                    end_time=hora_fin,
                    purpose=proposito,
                    status='approved'  # Aprobación automática
                )
                
                return {
                    'success': True,
                    'reservation_id': str(reservation.id),
                    'ambiente_asignado': {
                        'code': classroom.code,
                        'name': classroom.name,
                        'type': classroom.room_type,
                        'capacity': classroom.capacity,
                        'location': classroom.location
                    },
                    'detalles_reserva': {
                        'fecha': fecha.isoformat(),
                        'hora_inicio': hora_inicio.isoformat(),
                        'hora_fin': hora_fin.isoformat(),
                        'proposito': proposito,
                        'status': 'approved'
                    },
                    'teacher_name': teacher.user.get_full_name(),
                    'course_name': course.name,
                    'message': f'Ambiente {classroom.code} reservado automáticamente'
                }
            
        except (Teacher.DoesNotExist, Course.DoesNotExist) as e:
            return {
                'success': False,
                'error': 'Profesor o curso no encontrado',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error en reserva automática: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def obtener_reservas_profesor(self, teacher_id: str, fecha_inicio: date = None, 
                                fecha_fin: date = None) -> Dict:
        """
        Obtener todas las reservas de un profesor
        
        Args:
            teacher_id: ID del profesor
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            
        Returns:
            Dict con reservas del profesor
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Definir período por defecto (próximos 30 días)
            if not fecha_inicio:
                fecha_inicio = timezone.now().date()
            if not fecha_fin:
                from datetime import timedelta
                fecha_fin = fecha_inicio + timedelta(days=30)
            
            # Obtener reservas del período
            reservations = Reservation.objects.filter(
                teacher=teacher,
                date__range=[fecha_inicio, fecha_fin]
            ).select_related('classroom', 'course').order_by('date', 'start_time')
            
            reservas_por_fecha = {}
            
            for reservation in reservations:
                fecha_str = reservation.date.isoformat()
                
                if fecha_str not in reservas_por_fecha:
                    reservas_por_fecha[fecha_str] = []
                
                reservas_por_fecha[fecha_str].append({
                    'reservation_id': str(reservation.id),
                    'classroom_code': reservation.classroom.code,
                    'classroom_name': reservation.classroom.name,
                    'classroom_type': reservation.classroom.room_type,
                    'course_name': reservation.course.name,
                    'start_time': reservation.start_time.isoformat(),
                    'end_time': reservation.end_time.isoformat(),
                    'purpose': reservation.purpose,
                    'status': reservation.status,
                    'created_at': reservation.created_at.isoformat()
                })
            
            return {
                'success': True,
                'teacher_name': teacher.user.get_full_name(),
                'periodo': {
                    'fecha_inicio': fecha_inicio.isoformat(),
                    'fecha_fin': fecha_fin.isoformat()
                },
                'reservas_por_fecha': reservas_por_fecha,
                'total_reservas': reservations.count(),
                'fecha_consulta': timezone.now().isoformat()
            }
            
        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado',
                'error_code': 'TEACHER_NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo reservas del profesor: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def cancelar_reserva(self, reservation_id: str, teacher_id: str) -> Dict:
        """
        Cancelar una reserva
        
        Args:
            reservation_id: ID de la reserva
            teacher_id: ID del profesor (para verificar permisos)
            
        Returns:
            Dict con resultado de la cancelación
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            reservation = Reservation.objects.get(id=reservation_id)
            
            # Verificar que el profesor puede cancelar esta reserva
            if reservation.teacher != teacher:
                return {
                    'success': False,
                    'error': 'No tiene permisos para cancelar esta reserva',
                    'error_code': 'PERMISSION_DENIED'
                }
            
            # Verificar que la reserva se puede cancelar
            if reservation.status == 'cancelled':
                return {
                    'success': False,
                    'error': 'La reserva ya está cancelada',
                    'error_code': 'ALREADY_CANCELLED'
                }
            
            # Cancelar la reserva
            reservation.status = 'cancelled'
            reservation.save()
            
            return {
                'success': True,
                'reservation_id': str(reservation.id),
                'classroom_code': reservation.classroom.code,
                'date': reservation.date.isoformat(),
                'message': f'Reserva del ambiente {reservation.classroom.code} cancelada exitosamente'
            }
            
        except (Teacher.DoesNotExist, Reservation.DoesNotExist) as e:
            return {
                'success': False,
                'error': 'Profesor o reserva no encontrada',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            self.logger.error(f"Error cancelando reserva: {str(e)}")
            return {
                'success': False,
                'error': f'Error interno: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }


# Instancia global del servicio
servicio_reservas = ServicioReservas()