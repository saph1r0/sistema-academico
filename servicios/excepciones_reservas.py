#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Excepciones personalizadas para el sistema de reservas
Define jerarquía de excepciones para manejo de errores específicos del dominio
"""

from typing import Optional, Dict, Any


class ReservationError(Exception):
    """
    Excepción base para errores del sistema de reservas
    
    Attributes:
        message: Mensaje de error legible para el usuario
        code: Código de error para identificación programática
        details: Información adicional sobre el error
        http_status: Código de estado HTTP sugerido
    """
    
    def __init__(self, message: str, code: str = "RESERVATION_ERROR", 
                 details: Optional[Dict[str, Any]] = None, http_status: int = 500):
        self.message = message
        self.code = code
        self.details = details or {}
        self.http_status = http_status
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la excepción a un diccionario para respuestas API
        
        Returns:
            Dict con información estructurada del error
        """
        return {
            'error': self.message,
            'code': self.code,
            'details': self.details,
            'status': self.http_status
        }
    
    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class ValidationError(ReservationError):
    """
    Error de validación de datos de entrada
    
    Se lanza cuando los datos proporcionados no cumplen con los requisitos
    de formato, tipo o reglas de negocio básicas.
    """
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None, 
                 invalid_fields: Optional[list] = None):
        details = {}
        if field_errors:
            details['field_errors'] = field_errors
        if invalid_fields:
            details['invalid_fields'] = invalid_fields
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            http_status=400
        )
        
        self.field_errors = field_errors or {}
        self.invalid_fields = invalid_fields or []
    
    @classmethod
    def from_field_errors(cls, field_errors: Dict[str, str]) -> 'ValidationError':
        """
        Crea una ValidationError a partir de errores de campo específicos
        
        Args:
            field_errors: Diccionario con errores por campo
            
        Returns:
            Instancia de ValidationError
        """
        message = "Datos de reserva inválidos"
        if len(field_errors) == 1:
            field, error = next(iter(field_errors.items()))
            message = f"Error en campo {field}: {error}"
        
        return cls(
            message=message,
            field_errors=field_errors,
            invalid_fields=list(field_errors.keys())
        )
    
    @classmethod
    def missing_required_fields(cls, missing_fields: list) -> 'ValidationError':
        """
        Crea una ValidationError para campos requeridos faltantes
        
        Args:
            missing_fields: Lista de campos requeridos faltantes
            
        Returns:
            Instancia de ValidationError
        """
        field_errors = {field: "Campo requerido" for field in missing_fields}
        message = f"Campos requeridos faltantes: {', '.join(missing_fields)}"
        
        return cls(
            message=message,
            field_errors=field_errors,
            invalid_fields=missing_fields
        )


class ConflictError(ReservationError):
    """
    Error de conflicto de reserva
    
    Se lanza cuando existe un conflicto de horario, recurso no disponible,
    o intentos de reserva duplicados.
    """
    
    def __init__(self, message: str, conflict_type: str = "TIME_CONFLICT", 
                 conflicting_reservations: Optional[list] = None,
                 resource_info: Optional[Dict[str, Any]] = None):
        details = {
            'conflict_type': conflict_type
        }
        if conflicting_reservations:
            details['conflicting_reservations'] = conflicting_reservations
        if resource_info:
            details['resource_info'] = resource_info
        
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            details=details,
            http_status=409
        )
        
        self.conflict_type = conflict_type
        self.conflicting_reservations = conflicting_reservations or []
        self.resource_info = resource_info or {}
    
    @classmethod
    def time_conflict(cls, conflicting_reservations: list, 
                     resource_name: str = "recurso") -> 'ConflictError':
        """
        Crea un ConflictError para conflictos de horario
        
        Args:
            conflicting_reservations: Lista de reservas en conflicto
            resource_name: Nombre del recurso en conflicto
            
        Returns:
            Instancia de ConflictError
        """
        message = f"El {resource_name} ya está reservado en el horario solicitado"
        
        return cls(
            message=message,
            conflict_type="TIME_CONFLICT",
            conflicting_reservations=conflicting_reservations
        )
    
    @classmethod
    def resource_unavailable(cls, resource_id: str, reason: str = "inactivo") -> 'ConflictError':
        """
        Crea un ConflictError para recurso no disponible
        
        Args:
            resource_id: ID del recurso no disponible
            reason: Razón por la cual no está disponible
            
        Returns:
            Instancia de ConflictError
        """
        message = f"El recurso no está disponible para reservas ({reason})"
        
        return cls(
            message=message,
            conflict_type="RESOURCE_UNAVAILABLE",
            resource_info={'resource_id': resource_id, 'reason': reason}
        )
    
    @classmethod
    def duplicate_reservation(cls, existing_reservation_id: str) -> 'ConflictError':
        """
        Crea un ConflictError para reserva duplicada
        
        Args:
            existing_reservation_id: ID de la reserva existente
            
        Returns:
            Instancia de ConflictError
        """
        message = "Ya existe una reserva idéntica para este horario y recurso"
        
        return cls(
            message=message,
            conflict_type="DUPLICATE_RESERVATION",
            resource_info={'existing_reservation_id': existing_reservation_id}
        )


class DatabaseError(ReservationError):
    """
    Error de base de datos
    
    Se lanza cuando ocurren errores a nivel de base de datos como
    violaciones de restricciones, problemas de conexión, o errores de transacción.
    """
    
    def __init__(self, message: str, db_error_type: str = "UNKNOWN", 
                 original_error: Optional[Exception] = None,
                 operation: Optional[str] = None):
        details = {
            'db_error_type': db_error_type
        }
        if original_error:
            details['original_error'] = str(original_error)
        if operation:
            details['failed_operation'] = operation
        
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=details,
            http_status=500
        )
        
        self.db_error_type = db_error_type
        self.original_error = original_error
        self.operation = operation
    
    @classmethod
    def constraint_violation(cls, constraint_name: str = "unknown", 
                           operation: str = "create") -> 'DatabaseError':
        """
        Crea un DatabaseError para violaciones de restricciones
        
        Args:
            constraint_name: Nombre de la restricción violada
            operation: Operación que causó la violación
            
        Returns:
            Instancia de DatabaseError
        """
        message = "Error de integridad en la base de datos. Por favor, verifique los datos e intente nuevamente."
        
        return cls(
            message=message,
            db_error_type="CONSTRAINT_VIOLATION",
            operation=operation
        )
    
    @classmethod
    def null_constraint_violation(cls, field_name: str = "unknown") -> 'DatabaseError':
        """
        Crea un DatabaseError para violaciones de restricción NOT NULL
        
        Args:
            field_name: Nombre del campo que no puede ser nulo
            
        Returns:
            Instancia de DatabaseError
        """
        message = "Error interno del sistema. Por favor, intente nuevamente."
        
        return cls(
            message=message,
            db_error_type="NULL_CONSTRAINT_VIOLATION",
            operation="create_reservation"
        )
    
    @classmethod
    def foreign_key_violation(cls, referenced_table: str = "unknown") -> 'DatabaseError':
        """
        Crea un DatabaseError para violaciones de clave foránea
        
        Args:
            referenced_table: Tabla referenciada que no existe
            
        Returns:
            Instancia de DatabaseError
        """
        message = "Referencia inválida en los datos. Verifique que todos los recursos existan."
        
        return cls(
            message=message,
            db_error_type="FOREIGN_KEY_VIOLATION",
            operation="create_reservation"
        )
    
    @classmethod
    def connection_error(cls, original_error: Optional[Exception] = None) -> 'DatabaseError':
        """
        Crea un DatabaseError para errores de conexión
        
        Args:
            original_error: Excepción original de conexión
            
        Returns:
            Instancia de DatabaseError
        """
        message = "Error de conexión con la base de datos. Intente nuevamente en unos momentos."
        
        return cls(
            message=message,
            db_error_type="CONNECTION_ERROR",
            original_error=original_error,
            operation="database_connection"
        )
    
    @classmethod
    def transaction_error(cls, operation: str, original_error: Optional[Exception] = None) -> 'DatabaseError':
        """
        Crea un DatabaseError para errores de transacción
        
        Args:
            operation: Operación que falló en la transacción
            original_error: Excepción original
            
        Returns:
            Instancia de DatabaseError
        """
        message = "Error durante la operación de base de datos. Los cambios han sido revertidos."
        
        return cls(
            message=message,
            db_error_type="TRANSACTION_ERROR",
            original_error=original_error,
            operation=operation
        )


class AuthorizationError(ReservationError):
    """
    Error de autorización
    
    Se lanza cuando un usuario no tiene permisos suficientes para realizar
    una operación de reserva.
    """
    
    def __init__(self, message: str, user_id: Optional[str] = None, 
                 required_permission: Optional[str] = None,
                 resource_id: Optional[str] = None):
        details = {}
        if user_id:
            details['user_id'] = user_id
        if required_permission:
            details['required_permission'] = required_permission
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details=details,
            http_status=403
        )
        
        self.user_id = user_id
        self.required_permission = required_permission
        self.resource_id = resource_id
    
    @classmethod
    def insufficient_permissions(cls, user_id: str, operation: str) -> 'AuthorizationError':
        """
        Crea un AuthorizationError para permisos insuficientes
        
        Args:
            user_id: ID del usuario sin permisos
            operation: Operación que requiere permisos
            
        Returns:
            Instancia de AuthorizationError
        """
        message = f"No tiene permisos suficientes para {operation}"
        
        return cls(
            message=message,
            user_id=user_id,
            required_permission=operation
        )
    
    @classmethod
    def resource_access_denied(cls, user_id: str, resource_id: str) -> 'AuthorizationError':
        """
        Crea un AuthorizationError para acceso denegado a recurso
        
        Args:
            user_id: ID del usuario
            resource_id: ID del recurso denegado
            
        Returns:
            Instancia de AuthorizationError
        """
        message = "No tiene permisos para acceder a este recurso"
        
        return cls(
            message=message,
            user_id=user_id,
            resource_id=resource_id,
            required_permission="resource_access"
        )


class ResourceNotFoundError(ReservationError):
    """
    Error de recurso no encontrado
    
    Se lanza cuando se intenta acceder a un recurso que no existe
    en la base de datos.
    """
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} no encontrado"
        details = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            details=details,
            http_status=404
        )
        
        self.resource_type = resource_type
        self.resource_id = resource_id
    
    @classmethod
    def reservation_not_found(cls, reservation_id: str) -> 'ResourceNotFoundError':
        """
        Crea un ResourceNotFoundError para reserva no encontrada
        
        Args:
            reservation_id: ID de la reserva no encontrada
            
        Returns:
            Instancia de ResourceNotFoundError
        """
        return cls("Reserva", reservation_id)
    
    @classmethod
    def resource_not_found(cls, resource_id: str) -> 'ResourceNotFoundError':
        """
        Crea un ResourceNotFoundError para recurso no encontrado
        
        Args:
            resource_id: ID del recurso no encontrado
            
        Returns:
            Instancia de ResourceNotFoundError
        """
        return cls("Recurso", resource_id)
    
    @classmethod
    def user_not_found(cls, user_id: str) -> 'ResourceNotFoundError':
        """
        Crea un ResourceNotFoundError para usuario no encontrado
        
        Args:
            user_id: ID del usuario no encontrado
            
        Returns:
            Instancia de ResourceNotFoundError
        """
        return cls("Usuario", user_id)