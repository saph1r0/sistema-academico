"""
Entidad de dominio: Estudiante
Representa un estudiante en el sistema académico
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Estudiante:
    """
    Entidad Estudiante del dominio (sin dependencias de framework)
    """
    codigo: str                     # CUI del estudiante
    apellidos: str
    nombres: str
    correo_institucional: Optional[str] = None  # automatico
    estado: str = "DESACTIVADO"     # Estado inicial: DESACTIVADO
    
    # Campos técnicos (opcionales, los asigna la BD)
    id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    def __post_init__(self):
        """Validaciones y reglas de negocio del dominio"""
        # --- Validaciones básicas ---
        if not self.codigo or len(self.codigo.strip()) < 6:
            raise ValueError("El código del estudiante debe tener al menos 6 caracteres")
        if not self.apellidos or not self.apellidos.strip():
            raise ValueError("Los apellidos son obligatorios")
        if not self.nombres or not self.nombres.strip():
            raise ValueError("Los nombres son obligatorios")

        # --- Normalizar texto ---
        self.apellidos = self.apellidos.strip().upper()
        self.nombres = self.nombres.strip().upper()

        # --- Generar correo institucional si no se proporcionó ---
        if not self.correo_institucional:
            primer_apellido = self.apellidos.split(" ")[0].lower()
            primer_nombre = self.nombres.split(" ")[0].lower()
            self.correo_institucional = f"{primer_apellido}.{primer_nombre}@unsa.edu.pe"

        # --- Validar formato de correo ---
        if '@' not in self.correo_institucional:
            raise ValueError("El correo institucional generado no es válido")

        # --- Validar estado ---
        if self.estado not in ["DESACTIVADO", "ACTIVO", "RETIRADO", "ABANDONO"]:
            raise ValueError("Estado debe ser: DESACTIVADO, ACTIVO, RETIRADO o ABANDONO")

    # --- Métodos de comportamiento ---
    def activar(self):
        """Activa al estudiante (por ejemplo, al ingresar por primera vez al sistema)"""
        self.estado = "ACTIVO"

    def desactivar(self, motivo: str):
        """Desactiva un estudiante por retiro o abandono"""
        if motivo not in ["RETIRADO", "ABANDONO"]:
            raise ValueError("Motivo debe ser RETIRADO o ABANDONO")
        self.estado = motivo

    def nombre_completo(self) -> str:
        """Retorna el nombre completo del estudiante"""
        return f"{self.apellidos}, {self.nombres}"

    def __eq__(self, other):
        """Dos estudiantes son iguales si tienen el mismo código"""
        return isinstance(other, Estudiante) and self.codigo == other.codigo

    def __hash__(self):
        """Hash basado en el código único"""
        return hash(self.codigo)
