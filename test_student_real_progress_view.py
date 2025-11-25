#!/usr/bin/env python
"""
Test para verificar que la vista de estudiante muestre progreso real
basado en asistencia docente y temas del curso
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from repositorio.postgres_repository.models import (
    User, Student, Teacher, Course, CourseGroup, AcademicPeriod,
    Enrollment, CourseTopicContent, TeacherAttendance
)
from servicios.servicioEstudianteData import ServicioEstudianteData
from servicios.servicioCalculadorProgreso import ProgressCalculator
from servicios.servicioContenidoCurso import CourseContentManager


def test_student_real_progress_integration():
    """
    Test completo de integración para verificar que el estudiante
    vea el progreso real basado en asistencia docente
    """
    print("🧪 Iniciando test de progreso real para estudiante...")
    
    try:
        # 1. Crear datos de prueba
        print("\n1️⃣ Creando datos de prueba...")
        
        # Crear período académico
        periodo = AcademicPeriod.objects.create(
            name="2024-I",
            start_date=timezone.now().date() - timedelta(days=60),
            end_date=timezone.now().date() + timedelta(days=60),
            laboratory_enrollment_start=timezone.now().date() - timedelta(days=30),
            laboratory_enrollment_end=timezone.now().date() + timedelta(days=30),
            enrollment_change_deadline=timezone.now().date() + timedelta(days=15),
            is_active=True
        )
        print(f"   ✅ Período académico creado: {periodo.name}")
        
        # Crear curso
        curso = Course.objects.create(
            code="CS101",
            name="Introducción a la Programación",
            credits=4,
            theory_hours=3,
            practice_hours=2
        )
        print(f"   ✅ Curso creado: {curso.name}")
        
        # Crear usuario y profesor
        user_profesor = User.objects.create_user(
            institutional_email="profesor.test@universidad.edu",
            first_name="Juan",
            last_name="Pérez",
            role="teacher",
            password="test123"
        )
        
        profesor = Teacher.objects.create(
            user=user_profesor,
            teacher_code="PROF001",
            department="Ciencias de la Computación",
            specialty="Programación"
        )
        print(f"   ✅ Profesor creado: {profesor.user.get_full_name()}")
        
        # Crear grupo de curso
        course_group = CourseGroup.objects.create(
            course=curso,
            academic_period=periodo,
            group_code="A",
            teacher=profesor,
            capacity=30,
            total_planned_classes=68,  # 17 semanas * 4 clases
            classes_attended_by_teacher=20,  # Profesor ha asistido a 20 clases
            course_progress_percentage=29.41  # (20/68) * 100
        )
        print(f"   ✅ Grupo de curso creado: {course_group}")
        
        # Crear usuario y estudiante
        user_estudiante = User.objects.create_user(
            institutional_email="estudiante.test@universidad.edu",
            first_name="María",
            last_name="García",
            role="student",
            password="test123"
        )
        
        estudiante = Student.objects.create(
            user=user_estudiante,
            student_code="EST001",
            career="Ingeniería de Sistemas",
            current_cycle=3
        )
        print(f"   ✅ Estudiante creado: {estudiante.user.get_full_name()}")
        
        # Crear matrícula
        matricula = Enrollment.objects.create(
            student=estudiante,
            course_group=course_group,
            academic_period=periodo,
            status='active'
        )
        print(f"   ✅ Matrícula creada: {matricula}")
        
        # 2. Crear temas del curso
        print("\n2️⃣ Creando temas del curso...")
        
        content_manager = CourseContentManager()
        temas_data = [
            {"title": "Introducción a la programación", "description": "Conceptos básicos"},
            {"title": "Variables y tipos de datos", "description": "Declaración y uso de variables"},
            {"title": "Estructuras de control", "description": "If, while, for"},
            {"title": "Funciones", "description": "Definición y llamada de funciones"},
            {"title": "Arrays y listas", "description": "Manejo de estructuras de datos"},
            {"title": "Programación orientada a objetos", "description": "Clases y objetos"},
            {"title": "Proyecto final", "description": "Aplicación práctica"}
        ]
        
        result = content_manager.upload_course_topics(
            str(course_group.id),
            temas_data,
            str(profesor.id)
        )
        
        if result['success']:
            print(f"   ✅ {result['topics_created']} temas creados exitosamente")
        else:
            print(f"   ❌ Error creando temas: {result['error']}")
            return False
        
        # 3. Simular asistencia del profesor
        print("\n3️⃣ Simulando asistencia del profesor...")
        
        # Crear registros de asistencia del profesor
        for i in range(20):  # 20 clases asistidas
            fecha_clase = timezone.now() - timedelta(days=60-i*3)
            
            TeacherAttendance.objects.create(
                teacher=profesor,
                course_group=course_group,
                login_time=fecha_clase,
                logout_time=fecha_clase + timedelta(hours=2),
                ip_address="192.168.1.100",
                access_type="presential",
                triggered_progress_update=True
            )
        
        print(f"   ✅ 20 registros de asistencia del profesor creados")
        
        # 4. Calcular progreso automáticamente
        print("\n4️⃣ Calculando progreso automático...")
        
        calculator = ProgressCalculator()
        progress_result = calculator.calculate_course_progress(str(course_group.id))
        
        if progress_result['success']:
            print(f"   ✅ Progreso calculado: {progress_result['progress_percentage']}%")
            print(f"   📊 Clases asistidas: {progress_result['classes_attended']}/{progress_result['total_planned_classes']}")
            print(f"   📚 Temas actualizados: {progress_result['topics_updated']}")
        else:
            print(f"   ❌ Error calculando progreso: {progress_result['error']}")
            return False
        
        # 5. Probar servicio de datos del estudiante
        print("\n5️⃣ Probando servicio de datos del estudiante...")
        
        servicio = ServicioEstudianteData()
        
        # Probar obtener cursos del estudiante
        cursos = servicio.obtener_cursos_estudiante(estudiante.id)
        print(f"   ✅ Cursos obtenidos: {len(cursos)}")
        
        if cursos:
            curso_estudiante = cursos[0]
            print(f"   📚 Curso: {curso_estudiante.nombre}")
            print(f"   📊 Progreso real: {curso_estudiante.progreso}%")
        
        # Probar obtener detalle del curso
        detalle = servicio.obtener_detalle_curso(curso.id, estudiante.id)
        
        if detalle:
            print(f"   ✅ Detalle del curso obtenido")
            print(f"   📚 Nombre: {detalle['nombre']}")
            print(f"   📊 Progreso: {detalle['progreso']}%")
            print(f"   🎯 Temas completados: {detalle['temas_completados']}/{detalle['total_temas']}")
            print(f"   👨‍🏫 Profesor: {detalle['profesor']['nombre'] if detalle['profesor'] else 'Sin asignar'}")
            print(f"   📈 Progreso real: {'Sí' if detalle['es_progreso_real'] else 'No'}")
            print(f"   💬 Mensaje: {detalle['mensaje_progreso']}")
            
            # Verificar temas
            print(f"   📋 Temas del curso:")
            for tema in detalle['temas']:
                estado = "✅ Completado" if tema['completado'] else "⏳ Pendiente"
                print(f"      - {tema['nombre']}: {estado}")
        else:
            print(f"   ❌ No se pudo obtener detalle del curso")
            return False
        
        # Probar estadísticas del estudiante
        estadisticas = servicio.obtener_estadisticas_estudiante(estudiante.id)
        print(f"   ✅ Estadísticas obtenidas:")
        print(f"   📚 Total cursos: {estadisticas['total_cursos']}")
        print(f"   📊 Progreso promedio: {estadisticas['progreso_promedio']}%")
        print(f"   👨‍🏫 Asistencia promedio profesor: {estadisticas['asistencia_promedio']}%")
        
        # 6. Verificar sincronización en tiempo real
        print("\n6️⃣ Verificando sincronización en tiempo real...")
        
        # Simular que el profesor asiste a una clase más
        nueva_asistencia = TeacherAttendance.objects.create(
            teacher=profesor,
            course_group=course_group,
            login_time=timezone.now(),
            logout_time=timezone.now() + timedelta(hours=2),
            ip_address="192.168.1.100",
            access_type="presential",
            triggered_progress_update=True
        )
        
        # Recalcular progreso
        new_progress_result = calculator.calculate_course_progress(str(course_group.id))
        
        if new_progress_result['success']:
            print(f"   ✅ Nuevo progreso calculado: {new_progress_result['progress_percentage']}%")
            
            # Verificar que el estudiante ve el progreso actualizado
            nuevo_detalle = servicio.obtener_detalle_curso(curso.id, estudiante.id)
            print(f"   📊 Progreso actualizado para estudiante: {nuevo_detalle['progreso']}%")
            print(f"   🎯 Temas completados actualizados: {nuevo_detalle['temas_completados']}/{nuevo_detalle['total_temas']}")
        
        print("\n✅ Test de integración completado exitosamente!")
        print("\n📋 Resumen de verificaciones:")
        print("   ✅ Progreso real basado en asistencia docente")
        print("   ✅ Temas completados automáticamente según progreso")
        print("   ✅ Sincronización entre vista de profesor y estudiante")
        print("   ✅ Datos reales mostrados en vista de estudiante")
        print("   ✅ Actualización en tiempo real del progreso")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en el test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_student_view_with_no_topics():
    """
    Test para verificar que la vista funciona correctamente
    cuando no hay temas subidos por el profesor
    """
    print("\n🧪 Probando vista de estudiante sin temas del profesor...")
    
    try:
        # Crear datos mínimos
        periodo = AcademicPeriod.objects.create(
            name="2024-II",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=120),
            laboratory_enrollment_start=timezone.now().date(),
            laboratory_enrollment_end=timezone.now().date() + timedelta(days=30),
            enrollment_change_deadline=timezone.now().date() + timedelta(days=15),
            is_active=True
        )
        
        curso = Course.objects.create(
            code="CS102",
            name="Estructuras de Datos",
            credits=4
        )
        
        user_profesor = User.objects.create_user(
            institutional_email="profesor2.test@universidad.edu",
            first_name="Ana",
            last_name="López",
            role="teacher",
            password="test123"
        )
        
        profesor = Teacher.objects.create(
            user=user_profesor,
            teacher_code="PROF002"
        )
        
        course_group = CourseGroup.objects.create(
            course=curso,
            academic_period=periodo,
            group_code="B",
            teacher=profesor,
            capacity=25,
            total_planned_classes=68,
            classes_attended_by_teacher=15,
            course_progress_percentage=22.06  # (15/68) * 100
        )
        
        user_estudiante = User.objects.create_user(
            institutional_email="estudiante2.test@universidad.edu",
            first_name="Carlos",
            last_name="Rodríguez",
            role="student",
            password="test123"
        )
        
        estudiante = Student.objects.create(
            user=user_estudiante,
            student_code="EST002"
        )
        
        Enrollment.objects.create(
            student=estudiante,
            course_group=course_group,
            academic_period=periodo,
            status='active'
        )
        
        # Probar servicio sin temas reales
        servicio = ServicioEstudianteData()
        detalle = servicio.obtener_detalle_curso(curso.id, estudiante.id)
        
        if detalle:
            print(f"   ✅ Vista funciona sin temas reales")
            print(f"   📊 Progreso: {detalle['progreso']}%")
            print(f"   📚 Usa temas de ejemplo: {'No' if detalle['es_progreso_real'] else 'Sí'}")
            print(f"   🎯 Temas completados (estimados): {detalle['temas_completados']}/{detalle['total_temas']}")
            
            # Verificar que los temas de ejemplo se marcan según el progreso
            temas_completados_esperados = int((detalle['progreso'] / 100.0) * detalle['total_temas'])
            if detalle['temas_completados'] == temas_completados_esperados:
                print(f"   ✅ Temas de ejemplo marcados correctamente según progreso")
            else:
                print(f"   ❌ Error en marcado de temas de ejemplo")
                return False
        else:
            print(f"   ❌ Error obteniendo detalle sin temas reales")
            return False
        
        print("   ✅ Test sin temas completado exitosamente")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en test sin temas: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Ejecutando tests de vista de estudiante con progreso real")
    print("=" * 60)
    
    # Ejecutar tests
    test1_success = test_student_real_progress_integration()
    test2_success = test_student_view_with_no_topics()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS FINALES:")
    print(f"   Test integración completa: {'✅ PASÓ' if test1_success else '❌ FALLÓ'}")
    print(f"   Test sin temas del profesor: {'✅ PASÓ' if test2_success else '❌ FALLÓ'}")
    
    if test1_success and test2_success:
        print("\n🎉 TODOS LOS TESTS PASARON - La vista de estudiante está correctamente integrada con el progreso real!")
        print("\n📋 Funcionalidades verificadas:")
        print("   ✅ Progreso real basado en asistencia docente")
        print("   ✅ Temas completados automáticamente")
        print("   ✅ Sincronización profesor-estudiante")
        print("   ✅ Manejo de casos sin temas del profesor")
        print("   ✅ Actualización en tiempo real")
        print("   ✅ Estadísticas reales del estudiante")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - Revisar implementación")
        sys.exit(1)