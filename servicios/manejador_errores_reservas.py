#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Manejador de errores para el sistema de reservas
Proporciona manejo centralizado de errores con traducción a respuestas HTTP apropiadas
"""

import logging
import re
from typing import Dict, Any, Optional, Union
from datetime import datetime
from django.db import IntegrityError, DatabaseError as DjangoDatabaseError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from django.utils import timezone

from .excepciones_reservas import (
    ReservationError,
    ValidationError,
    ConflictError,
    DatabaseError,
    AuthorizationError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)


class ReservationErrorHandler:
    """
    Manejador centralizado de errores para el sistema de reservas
    
    Proporciona métodos para:
    - Traducir excepciones de base de datos a errores de dominio
    - Formatear respuestas HTTP apropiadas
    - Registrar errores para debugging
    - Mapear códigos de estado HTTP
    """
    
    def __init__(self):
        self.logger = logger
    
    def handle_database_error(self, error: Exception, operation: str = "unknown") -> Dict[str, Any]:
        """
        Maneja errores de base de datos y los traduce a errores de dominio
        
        Args:
            error: Excepción de base de datos original
            operation: Operación que causó el error
            
        Returns:
            Dict con información del error formateada
        """
        error_str = str(error).lower()
        
        try:
            # Detectar violación de restricción NOT NULL
            if "viola la restricción de no nulo" in error_str or "null value" in error_str:
                # Extraer nombre del campo si es posible
                field_match = re.search(r'columna «(\w+)»', str(error))
                field_name = field_match.group(1) if field_match else "unknown"
                
                db_error = DatabaseError.null_constraint_violation(field_name)
                self.logger.error(f"NULL constraint violation in {operation}: {field_name}")
                
                return db_error.to_dict()
            
            # Detectar violación de clave duplicada
            elif "duplicate key" in error_str or "ya existe" in error_str:
                conflict_error = ConflictError.duplicate_reservation("unknown")
                self.logger.warning(f"Duplicate key violation in {operation}: {str(error)}")
                
                return conflict_error.to_dict()
            
            # Detectar violación de clave foránea
            elif "foreign key" in error_str or "clave foránea" in error_str:
                # Extraer tabla referenciada si es posible
                table_match = re.search(r'tabla «(\w+)»', str(error))
                table_name = table_match.group(1) if table_match else "unknown"
                
                db_error = DatabaseError.foreign_key_violation(table_name)
                self.logger.error(f"Foreign key violation in {operation}: {table_name}")
                
                return db_error.to_dict()
            
            # Detectar errores de conexión
            elif "connection" in error_str or "conexión" in error_str:
                db_error = DatabaseError.connection_error(error)
                self.logger.critical(f"Database connection error in {operation}: {str(error)}")
                
                return db_error.to_dict()
            
            # Detectar errores de transacción
            elif "transaction" in error_str or "transacción" in error_str:
                db_error = DatabaseError.transaction_error(operation, error)
                self.logger.error(f"Transaction error in {operation}: {str(error)}")
                
                return db_error.to_dict()
            
            # Error de base de datos genérico
            else:
                db_error = DatabaseError(
                    message="Error interno de base de datos. Contacte al administrador si el problema persiste.",
                    db_error_type="GENERIC_ERROR",
                    original_error=error,
                    operation=operation
                )
                self.logger.error(f"Generic database error in {operation}: {str(error)}")
                
                return db_error.to_dict()
                
        except Exception as handler_error:
            # Si hay error en el manejador mismo, crear respuesta de emergencia
            self.logger.critical(f"Error in error handler: {str(handler_error)}")
            
            return {
                'error': 'Error interno del sistema',
                'code': 'HANDLER_ERROR',
                'details': {},
                'status': 500
            }
    
    def handle_validation_error(self, errors: Union[list, Dict[str, str], str]) -> Dict[str, Any]:
        """
        Maneja errores de validación de entrada
        
        Args:
            errors: Errores de validación (lista, dict o string)
            
        Returns:
            Dict con información del error formateada
        """
        try:
            if isinstance(errors, str):
                # Error simple como string
                validation_error = ValidationError(errors)
                
            elif isinstance(errors, list):
                # Lista de errores
                if not errors:
                    validation_error = ValidationError("Error de validación desconocido")
                elif len(errors) == 1:
                    validation_error = ValidationError(errors[0])
                else:
                    validation_error = ValidationError(
                        message="Múltiples errores de validación encontrados",
                        invalid_fields=errors
                    )
                    
            elif isinstance(errors, dict):
                # Diccionario de errores por campo
                validation_error = ValidationError.from_field_errors(errors)
                
            else:
                # Tipo no reconocido
                validation_error = ValidationError("Error de validación con formato no reconocido")
            
            self.logger.warning(f"Validation error: {validation_error.message}")
            return validation_error.to_dict()
            
        except Exception as handler_error:
            self.logger.error(f"Error handling validation error: {str(handler_error)}")
            
            return {
                'error': 'Error de validación',
                'code': 'VALIDATION_ERROR',
                'details': {'original_errors': str(errors)},
                'status': 400
            }
    
    def handle_conflict_error(self, conflict_type: str, message: str, 
                            additional_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Maneja errores de conflicto de reservas
        
        Args:
            conflict_type: Tipo de conflicto
            message: Mensaje descriptivo
            additional_info: Información adicional sobre el conflicto
            
        Returns:
            Dict con información del error formateada
        """
        try:
            additional_info = additional_info or {}
            
            if conflict_type == "TIME_CONFLICT":
                conflicting_reservations = additional_info.get('conflicting_reservations', [])
                resource_name = additional_info.get('resource_name', 'recurso')
                conflict_error = ConflictError.time_conflict(conflicting_reservations, resource_name)
                
            elif conflict_type == "RESOURCE_UNAVAILABLE":
                resource_id = additional_info.get('resource_id', 'unknown')
                reason = additional_info.get('reason', 'inactivo')
                conflict_error = ConflictError.resource_unavailable(resource_id, reason)
                
            elif conflict_type == "DUPLICATE_RESERVATION":
                existing_id = additional_info.get('existing_reservation_id', 'unknown')
                conflict_error = ConflictError.duplicate_reservation(existing_id)
                
            else:
                # Conflicto genérico
                conflict_error = ConflictError(
                    message=message,
                    conflict_type=conflict_type,
                    **additional_info
                )
            
            self.logger.warning(f"Conflict error ({conflict_type}): {message}")
            return conflict_error.to_dict()
            
        except Exception as handler_error:
            self.logger.error(f"Error handling conflict error: {str(handler_error)}")
            
            return {
                'error': message or 'Error de conflicto en reserva',
                'code': 'CONFLICT_ERROR',
                'details': {'conflict_type': conflict_type},
                'status': 409
            }
    
    def handle_authorization_error(self, user_id: str, operation: str, 
                                 resource_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Maneja errores de autorización
        
        Args:
            user_id: ID del usuario sin permisos
            operation: Operación denegada
            resource_id: ID del recurso (opcional)
            
        Returns:
            Dict con información del error formateada
        """
        try:
            if resource_id:
                auth_error = AuthorizationError.resource_access_denied(user_id, resource_id)
            else:
                auth_error = AuthorizationError.insufficient_permissions(user_id, operation)
            
            self.logger.warning(f"Authorization error for user {user_id}: {operation}")
            return auth_error.to_dict()
            
        except Exception as handler_error:
            self.logger.error(f"Error handling authorization error: {str(handler_error)}")
            
            return {
                'error': 'No tiene permisos para realizar esta operación',
                'code': 'AUTHORIZATION_ERROR',
                'details': {'user_id': user_id, 'operation': operation},
                'status': 403
            }
    
    def handle_not_found_error(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Maneja errores de recurso no encontrado
        
        Args:
            resource_type: Tipo de recurso no encontrado
            resource_id: ID del recurso no encontrado
            
        Returns:
            Dict con información del error formateada
        """
        try:
            if resource_type.lower() == "reserva":
                not_found_error = ResourceNotFoundError.reservation_not_found(resource_id)
            elif resource_type.lower() == "recurso":
                not_found_error = ResourceNotFoundError.resource_not_found(resource_id)
            elif resource_type.lower() == "usuario":
                not_found_error = ResourceNotFoundError.user_not_found(resource_id)
            else:
                not_found_error = ResourceNotFoundError(resource_type, resource_id)
            
            self.logger.info(f"Resource not found: {resource_type} {resource_id}")
            return not_found_error.to_dict()
            
        except Exception as handler_error:
            self.logger.error(f"Error handling not found error: {str(handler_error)}")
            
            return {
                'error': f'{resource_type} no encontrado',
                'code': 'RESOURCE_NOT_FOUND',
                'details': {'resource_type': resource_type, 'resource_id': resource_id},
                'status': 404
            }
    
    def create_error_response(self, error_dict: Dict[str, Any], 
                            request_id: Optional[str] = None) -> JsonResponse:
        """
        Crea una respuesta HTTP JSON a partir de un diccionario de error
        
        Args:
            error_dict: Diccionario con información del error
            request_id: ID de la solicitud para tracking (opcional)
            
        Returns:
            JsonResponse con el error formateado
        """
        try:
            # Agregar timestamp y request_id si están disponibles
            response_data = error_dict.copy()
            response_data['timestamp'] = timezone.now().isoformat()
            
            if request_id:
                response_data['request_id'] = request_id
            
            # Obtener código de estado HTTP
            status_code = error_dict.get('status', 500)
            
            return JsonResponse(response_data, status=status_code)
            
        except Exception as handler_error:
            self.logger.critical(f"Error creating error response: {str(handler_error)}")
            
            # Respuesta de emergencia
            return JsonResponse({
                'error': 'Error interno del sistema',
                'code': 'RESPONSE_CREATION_ERROR',
                'timestamp': timezone.now().isoformat(),
                'status': 500
            }, status=500)
    
    def handle_exception(self, exception: Exception, operation: str = "unknown", 
                        request_id: Optional[str] = None) -> JsonResponse:
        """
        Maneja cualquier excepción y devuelve una respuesta HTTP apropiada
        
        Args:
            exception: Excepción a manejar
            operation: Operación que causó la excepción
            request_id: ID de la solicitud para tracking
            
        Returns:
            JsonResponse con el error apropiado
        """
        try:
            # Si ya es una excepción de dominio, usar directamente
            if isinstance(exception, ReservationError):
                error_dict = exception.to_dict()
                
            # Errores de base de datos de Django
            elif isinstance(exception, (IntegrityError, DjangoDatabaseError)):
                error_dict = self.handle_database_error(exception, operation)
                
            # Errores de validación de Django
            elif isinstance(exception, DjangoValidationError):
                error_dict = self.handle_validation_error(str(exception))
                
            # Excepción genérica
            else:
                self.logger.error(f"Unhandled exception in {operation}: {str(exception)}")
                error_dict = {
                    'error': 'Error interno del sistema',
                    'code': 'INTERNAL_ERROR',
                    'details': {'operation': operation},
                    'status': 500
                }
            
            return self.create_error_response(error_dict, request_id)
            
        except Exception as handler_error:
            self.logger.critical(f"Critical error in exception handler: {str(handler_error)}")
            
            # Respuesta de último recurso
            return JsonResponse({
                'error': 'Error crítico del sistema',
                'code': 'CRITICAL_ERROR',
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    def log_error_context(self, error: Exception, context: Dict[str, Any]):
        """
        Registra contexto adicional para debugging de errores
        
        Args:
            error: Excepción ocurrida
            context: Contexto adicional (user_id, request_data, etc.)
        """
        try:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            self.logger.error(f"Error context - {str(error)} | Context: {context_str}")
            
        except Exception as log_error:
            self.logger.error(f"Error logging context: {str(log_error)}")
    
    def get_user_friendly_message(self, error_code: str, default_message: str = None) -> str:
        """
        Obtiene mensaje amigable para el usuario basado en código de error
        
        Args:
            error_code: Código de error
            default_message: Mensaje por defecto si no hay traducción
            
        Returns:
            Mensaje amigable para el usuario
        """
        messages = {
            'VALIDATION_ERROR': 'Por favor, verifique los datos ingresados e intente nuevamente.',
            'CONFLICT_ERROR': 'El horario solicitado no está disponible. Seleccione otro horario.',
            'DATABASE_ERROR': 'Error interno del sistema. Intente nuevamente en unos momentos.',
            'AUTHORIZATION_ERROR': 'No tiene permisos para realizar esta operación.',
            'RESOURCE_NOT_FOUND': 'El recurso solicitado no fue encontrado.',
            'TIME_CONFLICT': 'El recurso ya está reservado en el horario solicitado.',
            'RESOURCE_UNAVAILABLE': 'El recurso no está disponible para reservas.',
            'NULL_CONSTRAINT_VIOLATION': 'Error interno del sistema. Por favor, intente nuevamente.',
            'FOREIGN_KEY_VIOLATION': 'Referencia inválida en los datos. Verifique la información.',
            'CONNECTION_ERROR': 'Error de conexión. Intente nuevamente en unos momentos.',
            'DUPLICATE_RESERVATION': 'Ya existe una reserva para este horario y recurso.'
        }
        
        return messages.get(error_code, default_message or 'Ha ocurrido un error. Intente nuevamente.')


# Instancia global del manejador de errores
error_handler = ReservationErrorHandler()