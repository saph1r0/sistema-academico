#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio de validación para reservas
Maneja validación de datos y detección de conflictos para el sistema de reservas
"""

import logging
import uuid
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.dateparse import parse_date, parse_time
from django.db import transaction
from django.db.models import Q

logger = logging.getLogger(__name__)


class ReservationValidator:
    """
    Servicio de validación para reservas usando modelos dinámicos
    """
    
    def __init__(self):
        self.logger = logger
    
    def validate_reservation_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Valida los datos de reserva antes de la creación
        
        Args:
            data: Diccionario con los datos de la reserva
            
        Returns:
            Lista de errores de validación (vacía si no hay errores)
        """
        errors = []
        
        try:
            # Validar campos requeridos
            required_fields = ['resource_id', 'requested_by', 'reservation_date', 'start_time', 'end_time']
            for field in required_fields:
                if not data.get(field):
                    errors.append(f"Campo requerido: {field}")
            
            # Validar formato de UUID para resource_id y requested_by
            if data.get('resource_id'):
                uuid_error = self._validate_uuid_format(data['resource_id'], 'resource_id')
                if uuid_error:
                    errors.append(uuid_error)
            
            if data.get('requested_by'):
                uuid_error = self._validate_uuid_format(data['requested_by'], 'requested_by')
                if uuid_error:
                    errors.append(uuid_error)
            
            # Validar UUIDs opcionales
            optional_uuid_fields = ['course_group_id', 'laboratory_id']
            for field in optional_uuid_fields:
                if data.get(field):
                    uuid_error = self._validate_uuid_format(data[field], field)
                    if uuid_error:
                        errors.append(uuid_error)
            
            # Validar formato de fecha
            if data.get('reservation_date'):
                date_error = self._validate_date_format(data['reservation_date'])
                if date_error:
                    errors.append(date_error)
            
            # Validar formato de hora
            if data.get('start_time'):
                time_error = self._validate_time_format(data['start_time'], 'start_time')
                if time_error:
                    errors.append(time_error)
            
            if data.get('end_time'):
                time_error = self._validate_time_format(data['end_time'], 'end_time')
                if time_error:
                    errors.append(time_error)
            
            # Validar lógica de horarios
            if data.get('start_time') and data.get('end_time'):
                time_logic_error = self._validate_time_logic(data['start_time'], data['end_time'])
                if time_logic_error:
                    errors.append(time_logic_error)
            
            # Validar status si se proporciona
            if data.get('status'):
                status_error = self._validate_status(data['status'])
                if status_error:
                    errors.append(status_error)
            
            # Validar longitud de campos de texto
            if data.get('purpose') and len(str(data['purpose'])) > 1000:
                errors.append("El propósito no puede exceder 1000 caracteres")
            
        except Exception as e:
            self.logger.error(f"Error durante validación de datos: {str(e)}")
            errors.append("Error interno durante la validación")
        
        return errors
    
    def _validate_uuid_format(self, value: Any, field_name: str) -> Optional[str]:
        """
        Valida que un valor tenga formato UUID válido
        
        Args:
            value: Valor a validar
            field_name: Nombre del campo para el mensaje de error
            
        Returns:
            Mensaje de error o None si es válido
        """
        try:
            if isinstance(value, str):
                uuid.UUID(value, version=4)
            elif hasattr(value, 'hex'):  # UUID object
                pass  # Ya es un UUID válido
            else:
                return f"Formato de UUID inválido para {field_name}"
        except (ValueError, TypeError):
            return f"Formato de UUID inválido para {field_name}"
        
        return None
    
    def _validate_date_format(self, value: Any) -> Optional[str]:
        """
        Valida que un valor tenga formato de fecha válido
        
        Args:
            value: Valor a validar
            
        Returns:
            Mensaje de error o None si es válido
        """
        try:
            if isinstance(value, date):
                return None
            elif isinstance(value, str):
                parsed_date = parse_date(value)
                if not parsed_date:
                    return "Formato de fecha inválido. Use YYYY-MM-DD"
            else:
                return "Formato de fecha inválido. Use YYYY-MM-DD"
        except (ValueError, TypeError):
            return "Formato de fecha inválido. Use YYYY-MM-DD"
        
        return None
    
    def _validate_time_format(self, value: Any, field_name: str) -> Optional[str]:
        """
        Valida que un valor tenga formato de hora válido
        
        Args:
            value: Valor a validar
            field_name: Nombre del campo para el mensaje de error
            
        Returns:
            Mensaje de error o None si es válido
        """
        try:
            if isinstance(value, time):
                return None
            elif isinstance(value, str):
                parsed_time = parse_time(value)
                if not parsed_time:
                    return f"Formato de hora inválido para {field_name}. Use HH:MM"
            else:
                return f"Formato de hora inválido para {field_name}. Use HH:MM"
        except (ValueError, TypeError):
            return f"Formato de hora inválido para {field_name}. Use HH:MM"
        
        return None
    
    def _validate_time_logic(self, start_time: Any, end_time: Any) -> Optional[str]:
        """
        Valida la lógica de horarios (hora fin debe ser posterior a hora inicio)
        
        Args:
            start_time: Hora de inicio
            end_time: Hora de fin
            
        Returns:
            Mensaje de error o None si es válido
        """
        try:
            # Convertir a objetos time si son strings
            if isinstance(start_time, str):
                start_time = parse_time(start_time)
            if isinstance(end_time, str):
                end_time = parse_time(end_time)
            
            if start_time and end_time:
                if start_time >= end_time:
                    return "La hora de fin debe ser posterior a la hora de inicio"
        except Exception:
            return "Error validando lógica de horarios"
        
        return None
    
    def _validate_status(self, status: str) -> Optional[str]:
        """
        Valida que el status sea uno de los valores permitidos
        
        Args:
            status: Status a validar
            
        Returns:
            Mensaje de error o None si es válido
        """
        valid_statuses = ['pending', 'approved', 'rejected', 'cancelled']
        if status not in valid_statuses:
            return f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}"
        
        return None
    
    def check_time_conflicts(self, resource_id: str, reservation_date: Any, 
                           start_time: Any, end_time: Any, 
                           exclude_reservation_id: Optional[str] = None) -> bool:
        """
        Verifica conflictos de horario para un recurso específico
        
        Args:
            resource_id: ID del recurso a verificar
            reservation_date: Fecha de la reserva
            start_time: Hora de inicio
            end_time: Hora de fin
            exclude_reservation_id: ID de reserva a excluir (para actualizaciones)
            
        Returns:
            True si hay conflictos, False si no hay conflictos
        """
        try:
            # Importar modelos dinámicos aquí para evitar problemas de importación circular
            from presentacion.profesor.api_reservas import ReservationDyn
            
            # Convertir fecha si es string
            if isinstance(reservation_date, str):
                reservation_date = parse_date(reservation_date)
            
            # Convertir horas si son strings
            if isinstance(start_time, str):
                start_time = parse_time(start_time)
            if isinstance(end_time, str):
                end_time = parse_time(end_time)
            
            # Construir query para buscar conflictos
            query = Q(
                resource_id=resource_id,
                reservation_date=reservation_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            
            # Excluir reserva específica si se proporciona (para actualizaciones)
            if exclude_reservation_id:
                query &= ~Q(id=exclude_reservation_id)
            
            # Verificar si existen reservas conflictivas
            existing_reservations = ReservationDyn.objects.filter(query)
            
            return existing_reservations.exists()
            
        except Exception as e:
            self.logger.error(f"Error verificando conflictos de horario: {str(e)}")
            # En caso de error, asumir que hay conflicto por seguridad
            return True
    
    def check_resource_availability(self, resource_id: str, reservation_date: Any, 
                                  start_time: Any, end_time: Any) -> Dict[str, Any]:
        """
        Verifica la disponibilidad de un recurso y proporciona información detallada
        
        Args:
            resource_id: ID del recurso a verificar
            reservation_date: Fecha de la reserva
            start_time: Hora de inicio
            end_time: Hora de fin
            
        Returns:
            Dict con información de disponibilidad
        """
        try:
            # Importar modelos dinámicos aquí para evitar problemas de importación circular
            from presentacion.profesor.api_reservas import ReservationDyn, ResourceDyn
            
            # Verificar que el recurso existe
            try:
                resource = ResourceDyn.objects.get(id=resource_id)
            except ResourceDyn.DoesNotExist:
                return {
                    'available': False,
                    'reason': 'RESOURCE_NOT_FOUND',
                    'message': 'El recurso especificado no existe',
                    'conflicting_reservations': []
                }
            
            # Verificar que el recurso está activo
            if not resource.is_active:
                return {
                    'available': False,
                    'reason': 'RESOURCE_INACTIVE',
                    'message': 'El recurso no está disponible para reservas',
                    'conflicting_reservations': []
                }
            
            # Convertir fecha si es string
            if isinstance(reservation_date, str):
                reservation_date = parse_date(reservation_date)
            
            # Convertir horas si son strings
            if isinstance(start_time, str):
                start_time = parse_time(start_time)
            if isinstance(end_time, str):
                end_time = parse_time(end_time)
            
            # Buscar reservas conflictivas
            conflicting_reservations = ReservationDyn.objects.filter(
                resource_id=resource_id,
                reservation_date=reservation_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).order_by('start_time')
            
            if conflicting_reservations.exists():
                conflicts = []
                for reservation in conflicting_reservations:
                    conflicts.append({
                        'id': str(reservation.id),
                        'start_time': reservation.start_time.strftime('%H:%M'),
                        'end_time': reservation.end_time.strftime('%H:%M'),
                        'status': reservation.status,
                        'purpose': reservation.purpose or 'Sin propósito especificado'
                    })
                
                return {
                    'available': False,
                    'reason': 'TIME_CONFLICT',
                    'message': f'El recurso ya está reservado en el horario solicitado',
                    'conflicting_reservations': conflicts
                }
            
            return {
                'available': True,
                'reason': 'AVAILABLE',
                'message': 'El recurso está disponible para el horario solicitado',
                'conflicting_reservations': []
            }
            
        except Exception as e:
            self.logger.error(f"Error verificando disponibilidad del recurso: {str(e)}")
            return {
                'available': False,
                'reason': 'INTERNAL_ERROR',
                'message': 'Error interno verificando disponibilidad',
                'conflicting_reservations': []
            }
    
    def detect_concurrent_booking_attempts(self, resource_id: str, reservation_date: Any,
                                         start_time: Any, end_time: Any,
                                         request_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Detecta intentos concurrentes de reserva para el mismo recurso y horario
        
        Args:
            resource_id: ID del recurso
            reservation_date: Fecha de la reserva
            start_time: Hora de inicio
            end_time: Hora de fin
            request_timestamp: Timestamp de la solicitud (opcional)
            
        Returns:
            Dict con información sobre concurrencia
        """
        try:
            # Importar modelos dinámicos aquí para evitar problemas de importación circular
            from presentacion.profesor.api_reservas import ReservationDyn
            from django.utils import timezone
            
            if not request_timestamp:
                request_timestamp = timezone.now()
            
            # Convertir fecha si es string
            if isinstance(reservation_date, str):
                reservation_date = parse_date(reservation_date)
            
            # Convertir horas si son strings
            if isinstance(start_time, str):
                start_time = parse_time(start_time)
            if isinstance(end_time, str):
                end_time = parse_time(end_time)
            
            # Buscar reservas creadas muy recientemente (últimos 5 segundos)
            # que podrían indicar intentos concurrentes
            from datetime import timedelta
            recent_threshold = request_timestamp - timedelta(seconds=5)
            
            recent_reservations = ReservationDyn.objects.filter(
                resource_id=resource_id,
                reservation_date=reservation_date,
                start_time__lt=end_time,
                end_time__gt=start_time,
                created_at__gte=recent_threshold
            )
            
            concurrent_count = recent_reservations.count()
            
            return {
                'has_concurrent_attempts': concurrent_count > 0,
                'concurrent_count': concurrent_count,
                'recommendation': 'RETRY_WITH_DELAY' if concurrent_count > 0 else 'PROCEED',
                'message': f'Se detectaron {concurrent_count} intentos concurrentes' if concurrent_count > 0 
                          else 'No se detectaron intentos concurrentes'
            }
            
        except Exception as e:
            self.logger.error(f"Error detectando intentos concurrentes: {str(e)}")
            return {
                'has_concurrent_attempts': False,
                'concurrent_count': 0,
                'recommendation': 'PROCEED',
                'message': 'Error verificando concurrencia, procediendo con precaución'
            }
    
    def validate_complete_reservation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validación completa de una reserva incluyendo datos y conflictos
        
        Args:
            data: Datos de la reserva a validar
            
        Returns:
            Dict con resultado completo de validación
        """
        try:
            # Validar datos básicos
            validation_errors = self.validate_reservation_data(data)
            
            if validation_errors:
                return {
                    'valid': False,
                    'errors': validation_errors,
                    'error_type': 'VALIDATION_ERROR',
                    'can_proceed': False
                }
            
            # Verificar disponibilidad del recurso
            availability = self.check_resource_availability(
                data['resource_id'],
                data['reservation_date'],
                data['start_time'],
                data['end_time']
            )
            
            if not availability['available']:
                return {
                    'valid': False,
                    'errors': [availability['message']],
                    'error_type': availability['reason'],
                    'can_proceed': False,
                    'availability_info': availability
                }
            
            # Detectar intentos concurrentes
            concurrency = self.detect_concurrent_booking_attempts(
                data['resource_id'],
                data['reservation_date'],
                data['start_time'],
                data['end_time']
            )
            
            return {
                'valid': True,
                'errors': [],
                'error_type': None,
                'can_proceed': True,
                'availability_info': availability,
                'concurrency_info': concurrency
            }
            
        except Exception as e:
            self.logger.error(f"Error en validación completa: {str(e)}")
            return {
                'valid': False,
                'errors': ['Error interno durante la validación'],
                'error_type': 'INTERNAL_ERROR',
                'can_proceed': False
            }


# Instancia global del validador
reservation_validator = ReservationValidator()