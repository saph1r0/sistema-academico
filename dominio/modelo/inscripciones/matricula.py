"""
Entidad de dominio: Matricula
Representa la matrícula de un estudiante en un curso específico

REGLAS DE NEGOCIO CRÍTICAS:
- La matrícula la crea la SECRETARIA subiendo un Excel (RF08)
- El estudiante NO puede retirarse (requisito del proyecto)
- El estudiante NO puede cambiar de grupo (requisito del proyecto)
- La matrícula es PERMANENTE durante todo el ciclo académico
- SOLO la Secretaría puede modificarla con RF09 (casos excepcionales administrativos)
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Matricula:
    """
    Entidad Matricula del dominio
    Relaciona un estudiante con un curso en un ciclo académico
    Esta matrícula es PERMANENTE (teoría)
    """
    estudiante_codigo: str  # CUI del estudiante
    curso_codigo: str  
    ciclo: str  
    grupo: str  
    orden: int 
    
    # Campos técnicos
    id: Optional[int] = None
    fecha_matricula: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de dominio"""
        if not self.estudiante_codigo or len(self.estudiante_codigo) < 6:
            raise ValueError("El código del estudiante es obligatorio y debe ser válido")
        
        if not self.curso_codigo:
            raise ValueError("El código del curso es obligatorio")
        
        if not self.ciclo or len(self.ciclo) < 6:
            raise ValueError("El ciclo debe tener formato válido (Ej: 2025-B)")
        
        if not self.grupo or self.grupo not in ["A", "B", "C", "D"]:
            raise ValueError("El grupo debe ser una letra válida (A-D)")
        
        if self.orden < 1:
            raise ValueError("El orden debe ser un número positivo")
        
        # Normalizar
        self.grupo = self.grupo.upper()
        self.ciclo = self.ciclo.upper()
    
    def clave_unica(self) -> str:
        """
        Genera una clave única para esta matrícula
        Un estudiante solo puede estar matriculado UNA VEZ en un curso por ciclo
        """
        return f"{self.estudiante_codigo}_{self.curso_codigo}_{self.ciclo}"
    
    def __eq__(self, other):
        """Dos matrículas son iguales si tienen la misma clave única"""
        if not isinstance(other, Matricula):
            return False
        return self.clave_unica() == other.clave_unica()
    
    def __hash__(self):
        """Hash basado en la clave única"""
        return hash(self.clave_unica())
