"""
Tests unitarios para EstudiantePostgresRepository
"""
import pytest
from django.db import IntegrityError

from dominio.modelo.usuario.estudiante import Estudiante
from repositorio.postgres_repository.estudiantePostgresRepository import EstudiantePostgresRepository
from repositorio.postgres_repository.models import EstudianteModel


@pytest.mark.django_db
class TestEstudianteRepository:
    """
    Suite de tests para el repositorio de estudiantes
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Se ejecuta antes de cada test"""
        # Limpiar la base de datos
        EstudianteModel.objects.all().delete()
        
        # Crear instancia del repositorio
        self.repo = EstudiantePostgresRepository()
    
    def test_guardar_estudiante_exitoso(self):
        """Test: Guardar un estudiante correctamente con estado DESACTIVADO"""
        # Arrange
        estudiante = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
            # No se proporciona correo, se genera automáticamente
        )
        
        # Act
        resultado = self.repo.guardar(estudiante)
        
        # Assert
        assert resultado.id is not None
        assert resultado.codigo == "20223590"
        assert resultado.estado == "DESACTIVADO"  # CORREGIDO: Estado inicial
        assert resultado.correo_institucional == "perez.juan@unsa.edu.pe"  # Auto-generado
        assert resultado.fecha_creacion is not None
    
    def test_correo_generado_automaticamente(self):
        """Test: El correo se genera automáticamente con formato apellido.nombre@unsa.edu.pe"""
        # Arrange
        estudiante = Estudiante(
            codigo="20232284",
            apellidos="LOPEZ RUIZ",
            nombres="MARIA ELENA"
        )
        
        # Act
        resultado = self.repo.guardar(estudiante)
        
        # Assert
        assert resultado.correo_institucional == "lopez.maria@unsa.edu.pe"
    
    def test_correo_con_apellido_compuesto(self):
        """Test: Correo con apellidos compuestos toma el primer apellido"""
        # Arrange
        estudiante = Estudiante(
            codigo="20230573",
            apellidos="GARCIA TORRES",
            nombres="PEDRO LUIS ANTONIO"
        )
        
        # Act
        resultado = self.repo.guardar(estudiante)
        
        # Assert
        assert resultado.correo_institucional == "garcia.pedro@unsa.edu.pe"
    
    def test_estudiante_inicia_desactivado(self):
        """Test: Todo estudiante nuevo inicia en estado DESACTIVADO"""
        # Arrange
        estudiantes = [
            Estudiante(codigo="20223590", apellidos="PEREZ", nombres="JUAN"),
            Estudiante(codigo="20232284", apellidos="LOPEZ", nombres="MARIA"),
            Estudiante(codigo="20230573", apellidos="GARCIA", nombres="PEDRO")
        ]
        
        # Act
        self.repo.guardar_lista(estudiantes)
        
        # Assert
        todos = self.repo.listar_todos()
        for est in todos:
            assert est.estado == "DESACTIVADO"
    
    def test_activar_estudiante(self):
        """Test: Se puede activar un estudiante DESACTIVADO"""
        # Arrange
        estudiante = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
        )
        guardado = self.repo.guardar(estudiante)
        assert guardado.estado == "DESACTIVADO"
        
        # Act
        guardado.activar()
        actualizado = self.repo.actualizar(guardado)
        
        # Assert
        assert actualizado.estado == "ACTIVO"
        
        # Verificar en BD
        verificado = self.repo.buscar_por_codigo("20223590")
        assert verificado.estado == "ACTIVO"
    
    def test_guardar_estudiante_codigo_duplicado(self):
        """Test: No se puede guardar un estudiante con código duplicado"""
        # Arrange
        estudiante1 = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
        )
        estudiante2 = Estudiante(
            codigo="20223590",  # Mismo código
            apellidos="LOPEZ RUIZ",
            nombres="MARIA ELENA"
        )
        
        # Act
        self.repo.guardar(estudiante1)
        
        # Assert
        with pytest.raises(ValueError, match="Ya existe un estudiante"):
            self.repo.guardar(estudiante2)
    
    def test_buscar_por_codigo_existente(self):
        """Test: Buscar un estudiante por código que existe"""
        # Arrange
        estudiante = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
        )
        self.repo.guardar(estudiante)
        
        # Act
        resultado = self.repo.buscar_por_codigo("20223590")
        
        # Assert
        assert resultado is not None
        assert resultado.codigo == "20223590"
        assert resultado.apellidos == "PEREZ GOMEZ"
        assert resultado.estado == "DESACTIVADO"
    
    def test_buscar_por_codigo_no_existente(self):
        """Test: Buscar un estudiante que no existe retorna None"""
        # Act
        resultado = self.repo.buscar_por_codigo("99999999")
        
        # Assert
        assert resultado is None
    
    def test_buscar_por_correo_generado(self):
        """Test: Buscar estudiante por su correo auto-generado"""
        # Arrange
        estudiante = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
        )
        self.repo.guardar(estudiante)
        
        # Act
        resultado = self.repo.buscar_por_correo("perez.juan@unsa.edu.pe")
        
        # Assert
        assert resultado is not None
        assert resultado.codigo == "20223590"
    
    def test_guardar_lista_exitoso(self):
        """Test: Guardar una lista de estudiantes correctamente (todos DESACTIVADOS)"""
        # Arrange
        estudiantes = [
            Estudiante(
                codigo="20223590",
                apellidos="PEREZ GOMEZ",
                nombres="JUAN CARLOS"
            ),
            Estudiante(
                codigo="20232284",
                apellidos="LOPEZ RUIZ",
                nombres="MARIA ELENA"
            ),
            Estudiante(
                codigo="20230573",
                apellidos="GARCIA TORRES",
                nombres="PEDRO LUIS"
            )
        ]
        
        # Act
        cantidad = self.repo.guardar_lista(estudiantes)
        
        # Assert
        assert cantidad == 3
        
        # Verificar que todos estén DESACTIVADOS
        est1 = self.repo.buscar_por_codigo("20223590")
        est2 = self.repo.buscar_por_codigo("20232284")
        est3 = self.repo.buscar_por_codigo("20230573")
        
        assert est1.estado == "DESACTIVADO"
        assert est2.estado == "DESACTIVADO"
        assert est3.estado == "DESACTIVADO"
        
        # Verificar correos generados
        assert est1.correo_institucional == "perez.juan@unsa.edu.pe"
        assert est2.correo_institucional == "lopez.maria@unsa.edu.pe"
        assert est3.correo_institucional == "garcia.pedro@unsa.edu.pe"
    
    def test_guardar_lista_con_duplicados_en_lista(self):
        """Test: Guardar lista con códigos duplicados en la misma lista falla"""
        # Arrange
        estudiantes = [
            Estudiante(
                codigo="20223590",
                apellidos="PEREZ GOMEZ",
                nombres="JUAN CARLOS"
            ),
            Estudiante(
                codigo="20223590",  # Duplicado en la lista
                apellidos="LOPEZ RUIZ",
                nombres="MARIA ELENA"
            )
        ]
        
        # Act & Assert
        with pytest.raises(ValueError, match="duplicados en la lista"):
            self.repo.guardar_lista(estudiantes)
    
    def test_guardar_lista_con_codigo_existente_en_bd(self):
        """Test: Guardar lista cuando un código ya existe en BD falla (rollback)"""
        # Arrange
        estudiante_existente = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
        )
        self.repo.guardar(estudiante_existente)
        
        nuevos_estudiantes = [
            Estudiante(
                codigo="20223590",  # Ya existe en BD
                apellidos="OTRO APELLIDO",
                nombres="OTRO NOMBRE"
            ),
            Estudiante(
                codigo="20232284",
                apellidos="LOPEZ RUIZ",
                nombres="MARIA ELENA"
            )
        ]
        
        # Act & Assert
        with pytest.raises(ValueError, match="ya existen"):
            self.repo.guardar_lista(nuevos_estudiantes)
        
        # Verificar que no se guardó ninguno (rollback)
        assert self.repo.buscar_por_codigo("20232284") is None
    
    def test_listar_todos_sin_filtro(self):
        """Test: Listar todos los estudiantes sin filtro"""
        # Arrange
        estudiantes = [
            Estudiante(codigo="20223590", apellidos="PEREZ", nombres="JUAN"),
            Estudiante(codigo="20232284", apellidos="LOPEZ", nombres="MARIA")
        ]
        self.repo.guardar_lista(estudiantes)
        
        # Activar uno
        est1 = self.repo.buscar_por_codigo("20223590")
        est1.activar()
        self.repo.actualizar(est1)
        
        # Act
        resultado = self.repo.listar_todos()
        
        # Assert
        assert len(resultado) == 2
    
    def test_listar_todos_con_filtro_desactivado(self):
        """Test: Listar solo estudiantes DESACTIVADOS"""
        # Arrange
        estudiantes = [
            Estudiante(codigo="20223590", apellidos="PEREZ", nombres="JUAN"),
            Estudiante(codigo="20232284", apellidos="LOPEZ", nombres="MARIA"),
            Estudiante(codigo="20230573", apellidos="GARCIA", nombres="PEDRO")
        ]
        self.repo.guardar_lista(estudiantes)
        
        # Activar uno
        est1 = self.repo.buscar_por_codigo("20223590")
        est1.activar()
        self.repo.actualizar(est1)
        
        # Act
        desactivados = self.repo.listar_todos(estado="DESACTIVADO")
        activos = self.repo.listar_todos(estado="ACTIVO")
        
        # Assert
        assert len(desactivados) == 2
        assert len(activos) == 1
    
    def test_contar_por_estado_desactivado(self):
        """Test: Contar estudiantes DESACTIVADOS"""
        # Arrange
        estudiantes = [
            Estudiante(codigo="20223590", apellidos="PEREZ", nombres="JUAN"),
            Estudiante(codigo="20232284", apellidos="LOPEZ", nombres="MARIA"),
            Estudiante(codigo="20230573", apellidos="GARCIA", nombres="PEDRO")
        ]
        self.repo.guardar_lista(estudiantes)
        
        # Activar uno y retirar otro
        est1 = self.repo.buscar_por_codigo("20223590")
        est1.activar()
        self.repo.actualizar(est1)
        
        est2 = self.repo.buscar_por_codigo("20232284")
        est2.desactivar("RETIRADO")
        self.repo.actualizar(est2)
        
        # Act
        desactivados = self.repo.contar_por_estado("DESACTIVADO")
        activos = self.repo.contar_por_estado("ACTIVO")
        retirados = self.repo.contar_por_estado("RETIRADO")
        
        # Assert
        assert desactivados == 1
        assert activos == 1
        assert retirados == 1
    
    def test_existe_codigo(self):
        """Test: Verificar si un código existe"""
        # Arrange
        estudiante = Estudiante(
            codigo="20223590",
            apellidos="PEREZ GOMEZ",
            nombres="JUAN CARLOS"
        )
        self.repo.guardar(estudiante)
        
        # Act & Assert
        assert self.repo.existe_codigo("20223590") is True
        assert self.repo.existe_codigo("99999999") is False