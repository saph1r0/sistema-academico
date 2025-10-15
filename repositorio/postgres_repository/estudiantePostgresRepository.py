"""
Implementación concreta del repositorio de Estudiantes usando Django ORM + PostgreSQL
"""
from typing import List, Optional
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from dominio.modelo.usuario.iEstudianteRepository import IEstudianteRepository
from dominio.modelo.usuario.estudiante import Estudiante
from repositorio.postgres_repository.models import EstudianteModel


class EstudiantePostgresRepository(IEstudianteRepository):
    """
    Adaptador que implementa IEstudianteRepository usando Django ORM
    """
    
    def _model_a_entidad(self, model: EstudianteModel) -> Estudiante:
        """Convierte un modelo Django a una entidad de dominio"""
        return Estudiante(
            id=model.id,
            codigo=model.codigo,
            apellidos=model.apellidos,
            nombres=model.nombres,
            correo_institucional=model.correo_institucional,
            estado=model.estado,
            fecha_creacion=model.fecha_creacion,
            fecha_actualizacion=model.fecha_actualizacion
        )
    
    def _entidad_a_model(self, entidad: Estudiante) -> EstudianteModel:
        """Convierte una entidad de dominio a un modelo Django"""
        model = EstudianteModel(
            codigo=entidad.codigo,
            apellidos=entidad.apellidos,
            nombres=entidad.nombres,
            correo_institucional=entidad.correo_institucional,
            estado=entidad.estado  
        )
        if entidad.id:
            model.id = entidad.id
        return model
    
    def guardar(self, estudiante: Estudiante) -> Estudiante:
        """
        Guarda un estudiante individual
        El estudiante inicia en estado DESACTIVADO
        """
        # Verificar si ya existe
        if self.existe_codigo(estudiante.codigo):
            raise ValueError(f"Ya existe un estudiante con código {estudiante.codigo}")
        
        model = self._entidad_a_model(estudiante)
        model.save()
        
        return self._model_a_entidad(model)
    
    @transaction.atomic
    def guardar_lista(self, estudiantes: List[Estudiante]) -> int:
        """
        Guarda una lista de estudiantes de forma transaccional
        Todos inician en estado DESACTIVADO
        Si uno falla, se hace rollback de todos
        """
        if not estudiantes:
            return 0
        
        # Validar que no haya duplicados en la lista
        codigos = [e.codigo for e in estudiantes]
        if len(codigos) != len(set(codigos)):
            raise ValueError("Hay códigos duplicados en la lista de estudiantes")
        
        # Verificar que no existan en la BD
        codigos_existentes = EstudianteModel.objects.filter(
            codigo__in=codigos
        ).values_list('codigo', flat=True)
        
        if codigos_existentes:
            raise ValueError(
                f"Los siguientes códigos ya existen: {', '.join(codigos_existentes)}"
            )
        
        # Crear todos los modelos
        modelos = [self._entidad_a_model(e) for e in estudiantes]
        
        # Guardar en bloque (más eficiente)
        EstudianteModel.objects.bulk_create(modelos)
        
        return len(modelos)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Estudiante]:
        """
        Busca un estudiante por su código único
        """
        try:
            model = EstudianteModel.objects.get(codigo=codigo)
            return self._model_a_entidad(model)
        except ObjectDoesNotExist:
            return None
    
    def buscar_por_correo(self, correo: str) -> Optional[Estudiante]:
        """
        Busca un estudiante por su correo institucional
        """
        try:
            model = EstudianteModel.objects.get(correo_institucional=correo)
            return self._model_a_entidad(model)
        except ObjectDoesNotExist:
            return None
    
    def listar_todos(self, estado: Optional[str] = None) -> List[Estudiante]:
        """
        Lista todos los estudiantes, opcionalmente filtrados por estado
        Estados posibles: DESACTIVADO, ACTIVO, RETIRADO, ABANDONO
        """
        queryset = EstudianteModel.objects.all()
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return [self._model_a_entidad(model) for model in queryset]
    
    def actualizar(self, estudiante: Estudiante) -> Estudiante:
        """
        Actualiza los datos de un estudiante existente
        """
        if not estudiante.id:
            raise ValueError("El estudiante debe tener un ID para ser actualizado")
        
        try:
            model = EstudianteModel.objects.get(id=estudiante.id)
            model.apellidos = estudiante.apellidos
            model.nombres = estudiante.nombres
            model.correo_institucional = estudiante.correo_institucional
            model.estado = estudiante.estado
            model.save()
            
            return self._model_a_entidad(model)
        except ObjectDoesNotExist:
            raise ValueError(f"No existe un estudiante con ID {estudiante.id}")
    
    def existe_codigo(self, codigo: str) -> bool:
        """
        Verifica si ya existe un estudiante con ese código
        """
        return EstudianteModel.objects.filter(codigo=codigo).exists()
    
    def contar_por_estado(self, estado: str) -> int:
        """
        Cuenta cuántos estudiantes hay en un estado específico
        Estados: DESACTIVADO, ACTIVO, RETIRADO, ABANDONO
        """
        return EstudianteModel.objects.filter(estado=estado).count()