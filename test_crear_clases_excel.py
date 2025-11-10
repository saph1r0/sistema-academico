#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test para el servicio de creación de clases desde Excel
"""
import os
import sys
import django
import tempfile
import pandas as pd

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioCreadorClases import CourseGroupCreator, TeacherData, CreationReport
from repositorio.postgres_repository.models import User, Teacher, Course, CourseGroup, AcademicPeriod


def create_test_excel():
    """Crea un archivo Excel de prueba"""
    # Datos de prueba
    test_data = {
        'Col0': ['Dato1', 'Dato2', 'Dato3'],
        'Curso': ['Matemática Aplicada', 'Ingeniería de Software', 'Base de Datos'],
        'Grupo': ['A', 'B', 'A'],
        'Col3': ['Extra1', 'Extra2', 'Extra3'],
        'Col4': ['Extra4', 'Extra5', 'Extra6'],
        'Docentes': ['GARCIA LOPEZ, JUAN CARLOS', 'MARTINEZ SILVA, MARIA ELENA', 'RODRIGUEZ TORRES, PEDRO LUIS'],
        'Correo': ['jgarcia@unsa.edu.pe', 'mmartinez@unsa.edu.pe', 'prodriguez@unsa.edu.pe']
    }
    
    df = pd.DataFrame(test_data)
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    df.to_excel(temp_file.name, index=False)
    temp_file.close()
    
    return temp_file.name


def test_teacher_data_extraction():
    """Test para extracción de datos de profesor"""
    print("=" * 50)
    print("TEST: Extracción de datos de profesor")
    print("=" * 50)
    
    # Crear datos de prueba
    test_cases = [
        {
            'name': 'GARCIA LOPEZ, JUAN CARLOS',
            'expected_first': 'Juan Carlos',
            'expected_last': 'Garcia Lopez'
        },
        {
            'name': 'MARIA ELENA MARTINEZ',
            'expected_first': 'Maria',
            'expected_last': 'Elena Martinez'
        }
    ]
    
    for case in test_cases:
        teacher_data = TeacherData(
            name=case['name'],
            email='test@unsa.edu.pe',
            course_name='Test Course',
            group_code='A'
        )
        
        print(f"Nombre original: {case['name']}")
        print(f"Primer nombre: {teacher_data.first_name} (esperado: {case['expected_first']})")
        print(f"Apellidos: {teacher_data.last_name} (esperado: {case['expected_last']})")
        
        assert teacher_data.first_name == case['expected_first'], f"Error en primer nombre"
        assert teacher_data.last_name == case['expected_last'], f"Error en apellidos"
        print("✓ Test pasado\n")


def test_course_group_creator():
    """Test para el creador de grupos de curso"""
    print("=" * 50)
    print("TEST: Creador de grupos de curso")
    print("=" * 50)
    
    # Crear archivo Excel de prueba
    excel_file = create_test_excel()
    
    try:
        # Obtener estado inicial
        initial_teachers = Teacher.objects.count()
        initial_courses = Course.objects.count()
        initial_groups = CourseGroup.objects.count()
        
        print(f"Estado inicial:")
        print(f"  Profesores: {initial_teachers}")
        print(f"  Cursos: {initial_courses}")
        print(f"  Grupos: {initial_groups}")
        
        # Crear instancia del servicio
        creator = CourseGroupCreator()
        
        # Ejecutar creación
        print(f"\nProcesando archivo: {excel_file}")
        report = creator.create_classes_from_excel(excel_file)
        
        # Verificar resultados
        print(f"\nResultados:")
        print(f"  Éxito: {report.success}")
        print(f"  Clases creadas: {report.classes_created}")
        print(f"  Profesores creados: {report.teachers_created}")
        print(f"  Cursos creados: {report.courses_created}")
        print(f"  Duplicados: {report.duplicates_found}")
        print(f"  Errores: {len(report.errors)}")
        print(f"  Advertencias: {len(report.warnings)}")
        
        # Verificar estado final
        final_teachers = Teacher.objects.count()
        final_courses = Course.objects.count()
        final_groups = CourseGroup.objects.count()
        
        print(f"\nEstado final:")
        print(f"  Profesores: {final_teachers} (+{final_teachers - initial_teachers})")
        print(f"  Cursos: {final_courses} (+{final_courses - initial_courses})")
        print(f"  Grupos: {final_groups} (+{final_groups - initial_groups})")
        
        # Verificaciones
        assert report.success, "El proceso debería ser exitoso"
        assert report.classes_created > 0, "Deberían crearse clases"
        assert final_groups > initial_groups, "Deberían aumentar los grupos"
        
        print("✓ Test de creación pasado")
        
        # Test de duplicados
        print(f"\n" + "=" * 30)
        print("TEST: Manejo de duplicados")
        print("=" * 30)
        
        # Ejecutar nuevamente el mismo archivo
        report2 = creator.create_classes_from_excel(excel_file)
        
        print(f"Segunda ejecución:")
        print(f"  Clases creadas: {report2.classes_created}")
        print(f"  Duplicados encontrados: {report2.duplicates_found}")
        
        # No deberían crearse nuevas clases, solo encontrar duplicados
        assert report2.classes_created == 0, "No deberían crearse clases duplicadas"
        assert report2.duplicates_found > 0, "Deberían encontrarse duplicados"
        
        print("✓ Test de duplicados pasado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(excel_file):
            os.unlink(excel_file)


def test_error_handling():
    """Test para manejo de errores"""
    print("=" * 50)
    print("TEST: Manejo de errores")
    print("=" * 50)
    
    creator = CourseGroupCreator()
    
    # Test archivo inexistente
    report = creator.create_classes_from_excel('archivo_inexistente.xlsx')
    assert not report.success, "Debería fallar con archivo inexistente"
    assert len(report.errors) > 0, "Debería reportar errores"
    print("✓ Test archivo inexistente pasado")
    
    # Test con datos inválidos
    invalid_data = {
        'Col0': ['', '', ''],
        'Curso': ['', '', ''],
        'Grupo': ['', '', ''],
        'Col3': ['', '', ''],
        'Col4': ['', '', ''],
        'Docentes': ['', '', ''],
        'Correo': ['', '', '']
    }
    
    df = pd.DataFrame(invalid_data)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    df.to_excel(temp_file.name, index=False)
    temp_file.close()
    
    try:
        report = creator.create_classes_from_excel(temp_file.name)
        assert report.success, "Debería ser exitoso aunque no procese datos"
        assert report.classes_created == 0, "No debería crear clases con datos inválidos"
        print("✓ Test datos inválidos pasado")
        
    finally:
        os.unlink(temp_file.name)


def test_summary_functionality():
    """Test para funcionalidad de resumen"""
    print("=" * 50)
    print("TEST: Funcionalidad de resumen")
    print("=" * 50)
    
    creator = CourseGroupCreator()
    summary = creator.get_creation_summary()
    
    print("Resumen obtenido:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Verificar que el resumen contiene las claves esperadas
    expected_keys = [
        'total_teachers', 'total_courses', 'total_course_groups',
        'groups_with_teacher', 'groups_without_teacher', 'teacher_assignment_percentage'
    ]
    
    for key in expected_keys:
        assert key in summary, f"Falta clave en resumen: {key}"
    
    print("✓ Test resumen pasado")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("🧪 INICIANDO TESTS DEL SERVICIO DE CREACIÓN DE CLASES")
    print("=" * 80)
    
    tests = [
        test_teacher_data_extraction,
        test_course_group_creator,
        test_error_handling,
        test_summary_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} - PASADO\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} - FALLIDO: {str(e)}\n")
    
    print("=" * 80)
    print("RESUMEN DE TESTS:")
    print(f"✅ Pasados: {passed}")
    print(f"❌ Fallidos: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        return True
    else:
        print("⚠️  Algunos tests fallaron")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)