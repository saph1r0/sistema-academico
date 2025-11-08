"""
Interface del repositorio de Estudiantes (Puerto del Dominio)
Define el contrato que debe cumplir cualquier implementación
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dominio.modelo.usuario.estudiante import Estudiante


class IEstudianteRepository(ABC):
    """
    Puerto del dominio: interface para persistencia de estudiantes
    Las implementaciones concretas irán en repositorio/
    """
    
    @abstractmethod
    def guardar(self, estudiante: Estudiante) -> Estudiante:
        """
        Guarda un estudiante individual
        El estudiante debe iniciar en estado DESACTIVADO
        Retorna el estudiante con su ID asignado
        
        Raises:
            ValueError: Si el código ya existe
        """
        pass
    
    @abstractmethod
    def guardar_lista(self, estudiantes: List[Estudiante]) -> int:
        """
        Guarda una lista de estudiantes de forma transaccional
        Si uno falla, se hace rollback de todos
        
        Returns:
            Cantidad de estudiantes guardados exitosamente
        
        Raises:
            ValueError: Si hay códigos duplicados
        """
        pass
    
    @abstractmethod
    def buscar_por_codigo(self, codigo: str) -> Optional[Estudiante]:
        """
        Busca un estudiante por su código único (CUI)
        
        Returns:
            Estudiante si existe, None en caso contrario
        """
        pass
    
    @abstractmethod
    def buscar_por_correo(self, correo: str) -> Optional[Estudiante]:
        """
        Busca un estudiante por su correo institucional
        
        Returns:
            Estudiante si existe, None en caso contrario
        """
        pass
    
    @abstractmethod
    def listar_todos(self, estado: Optional[str] = None) -> List[Estudiante]:
        """
        Lista todos los estudiantes, opcionalmente filtrados por estado
        
        Args:
            estado: Si se proporciona, filtra por ACTIVO, RETIRADO o ABANDONO
        
        Returns:
            Lista de estudiantes (puede estar vacía)
        """
        pass
    
    @abstractmethod
    def actualizar(self, estudiante: Estudiante) -> Estudiante:
        """
        Actualiza los datos de un estudiante existente
        
        Returns:
            Estudiante actualizado
        
        Raises:
            ValueError: Si el estudiante no existe
        """
        pass
    
    @abstractmethod
    def existe_codigo(self, codigo: str) -> bool:
        """
        Verifica si ya existe un estudiante con ese código
        
        Returns:
            True si existe, False en caso contrario
        """
        pass
    
    @abstractmethod
    def contar_por_estado(self, estado: str) -> int:
        """
        Cuenta cuántos estudiantes hay en un estado específico
        
        Returns:
            Cantidad de estudiantes en ese estado
        """
        pass
