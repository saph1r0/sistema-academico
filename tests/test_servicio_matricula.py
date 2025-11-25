import sys, os
import pytest
from servicios.servicioMatricula import ServicioMatricula
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



# Ruta al Excel de prueba
EXCEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "../alumnos_450_1703240_B_A (1).xlsx"
)

@pytest.fixture
def servicio_matricula():
    return ServicioMatricula()

def test_procesar_lista_matricula(servicio_matricula):
    # periodo_id ficticio
    periodo_id = 2025

    # Ejecutar el servicio
    estudiantes = servicio_matricula.procesar_lista_matricula(EXCEL_PATH, periodo_id)

    # Validar que devuelve lista de estudiantes
    assert isinstance(estudiantes, list)
    assert len(estudiantes) > 0

    # Tomar un estudiante de ejemplo
    est = estudiantes[0]

    # Validar atributos generados
    assert hasattr(est, "cui")
    assert hasattr(est, "nombres")
    assert hasattr(est, "apellidos")
    assert hasattr(est, "correo")
    assert hasattr(est, "password")
    assert hasattr(est, "anio_ingreso")

    # Validar que el correo sigue el patrón esperado
    assert est.correo.endswith("@unsa.edu.pe")

    # Validar que la contraseña sea el CUI
    assert est.password == est.cui

    # Validar que el año de ingreso tenga 4 dígitos
    assert len(str(est.anio_ingreso)) == 4
