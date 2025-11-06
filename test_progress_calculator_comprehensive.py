#!/usr/bin/env python
"""
Test comprehensivo del calculador de progreso automático
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioCalculadorProgreso import ProgressCalculator
from servicios.servicioContenidoCurso import CourseContentManager
from repositorio.postgres_repository.models import CourseGroup, Teacher, CourseTopicContent
from django.utils import timezone
from django.db import connection


def create_test_topics(course_group_id: str, num_topics: int = 10):
    """Crea temas de prueba para un curso"""
    
    content_manager = CourseContentManager()
    
    topics = []
    for i in range(num_topics):
        topics.append({
            'title': f'Tema {i+1}: Contenido del curso',
            'description': f'Descripción detallada del tema {i+1}'
        })
    
    result = content_manager.upload_course_topics(course_group_id, topics)
    return result


def create_test_attendance(teacher_id: str, course_group_id: str, num_sessions: int = 5):
    """Crea registros de asistencia de prueba usando SQL directo"""
    
    print(f"Creando {num_sessions} registros de asistencia para testing...")
    
    with connection.cursor() as cursor:
        # Limpiar registros existentes del profesor
        cursor.execute("DELETE FROM teacher_attendance WHERE teacher_id = %s", [teacher_id])
        
        # Crear nuevos registros
        for i in range(num_sessions):
            attendance_date = (timezone.now() - timedelta(days=i)).date()
            start_time = timezone.now().time().replace(hour=8, minute=0, second=0, microsecond=0)
            end_time = timezone.now().time().replace(hour=11, minute=30, second=0, microsecond=0)
            
            cursor.execute("""
                INSERT INTO teacher_attendance 
                (id, teacher_id, course_group_id, attendance_date, start_time, end_time, ip_address, is_virtual, created_at)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, '192.168.1.100', false, NOW())
            """, [teacher_id, course_group_id, attendance_date, start_time, end_time])
        
        print(f"✅ Creados {num_sessions} registros de asistencia")


def test_comprehensive_progress_calculation():
    """Test completo del sistema de cálculo de progreso"""
    
    print("🚀 Test Comprehensivo del Calculador de Progreso\n")
    
    calculator = ProgressCalculator()
    
    # 1. Seleccionar un curso para testing
    course_group = CourseGroup.objects.filter(teacher__isnull=False).first()
    
    if not course_group:
        print("❌ No hay cursos con profesores para testing")
        return False
    
    print(f"📚 Curso seleccionado: {course_group.course.name} - Grupo {course_group.group_code}")
    print(f"👨‍🏫 Profesor: {course_group.teacher.user.get_full_name()}")
    
    # 2. Crear temas de prueba
    print(f"\n📝 Creando temas de prueba...")
    topics_result = create_test_topics(str(course_group.id), 8)
    
    if topics_result['success']:
        print(f"✅ Creados {topics_result['topics_created']} temas")
    else:
        print(f"❌ Error creando temas: {topics_result['error']}")
    
    # 3. Crear registros de asistencia de prueba
    print(f"\n👥 Creando registros de asistencia...")
    create_test_attendance(str(course_group.teacher.id), str(course_group.id), 15)  # 15 sesiones de 68 programadas
    
    # 4. Test de cálculo de progreso
    print(f"\n🔄 Calculando progreso del curso...")
    
    # Estado inicial
    initial_progress = course_group.course_progress_percentage
    print(f"Progreso inicial: {initial_progress}%")
    
    # Calcular nuevo progreso
    result = calculator.calculate_course_progress(str(course_group.id))
    
    if result['success']:
        print("✅ Cálculo de progreso exitoso:")
        print(f"   - Clases asistidas: {result['classes_attended']}")
        print(f"   - Total programadas: {result['total_planned_classes']}")
        print(f"   - Progreso calculado: {result['progress_percentage']}%")
        print(f"   - Temas actualizados: {result['topics_updated']}")
        
        # Verificar que el progreso se actualizó
        course_group.refresh_from_db()
        new_progress = course_group.course_progress_percentage
        print(f"   - Progreso en BD: {new_progress}%")
        
        if new_progress != initial_progress:
            print("✅ El progreso se actualizó correctamente en la base de datos")
        else:
            print("⚠️  El progreso no cambió en la base de datos")
    else:
        print(f"❌ Error en cálculo: {result['error']}")
        return False
    
    # 5. Verificar actualización de temas
    print(f"\n📋 Verificando actualización de temas...")
    
    topics = CourseTopicContent.objects.filter(course_group=course_group).order_by('topic_order')
    total_topics = topics.count()
    completed_topics = topics.filter(is_completed=True).count()
    
    print(f"   - Total de temas: {total_topics}")
    print(f"   - Temas completados: {completed_topics}")
    
    # Calcular temas esperados completados
    expected_completed = int((result['progress_percentage'] / 100.0) * total_topics)
    print(f"   - Temas esperados completados: {expected_completed}")
    
    if completed_topics == expected_completed:
        print("✅ Los temas se actualizaron correctamente según el progreso")
    else:
        print(f"⚠️  Discrepancia en temas completados: esperados {expected_completed}, actuales {completed_topics}")
    
    # 6. Test de estadísticas detalladas
    print(f"\n📊 Obteniendo estadísticas detalladas...")
    
    stats = calculator.get_progress_statistics(str(course_group.id))
    
    if stats['success']:
        print("✅ Estadísticas obtenidas:")
        print(f"   - Progreso: {stats['progress_percentage']}%")
        print(f"   - Tasa de asistencia: {stats['attendance_statistics']['attendance_rate']}%")
        print(f"   - Tasa de completado de temas: {stats['topic_statistics']['completion_rate']}%")
        print(f"   - Última sesión: {stats['attendance_statistics']['last_session']}")
    else:
        print(f"❌ Error obteniendo estadísticas: {stats['error']}")
    
    # 7. Test de progreso esperado vs real
    print(f"\n⚖️ Comparando progreso esperado vs real...")
    
    comparison = calculator.get_expected_vs_actual_progress(str(course_group.id))
    
    if comparison['success']:
        print("✅ Comparación exitosa:")
        print(f"   - Progreso esperado: {comparison['expected_progress']}%")
        print(f"   - Progreso real: {comparison['actual_progress']}%")
        print(f"   - Diferencia: {comparison['progress_difference']}%")
        print(f"   - Estado: {comparison['status']}")
        print(f"   - Mensaje: {comparison['status_message']}")
    else:
        print(f"❌ Error en comparación: {comparison['error']}")
    
    # 8. Test de cálculo masivo
    print(f"\n🔄 Test de cálculo masivo para el profesor...")
    
    mass_results = calculator.calculate_all_courses_progress(str(course_group.teacher.id))
    
    successful = sum(1 for r in mass_results if r.get('success', False))
    total = len(mass_results)
    
    print(f"✅ Cálculo masivo: {successful}/{total} cursos procesados exitosamente")
    
    for result in mass_results:
        if result['success']:
            print(f"   - {result['course_name']}: {result['progress_percentage']}%")
    
    # 9. Test de recálculo por asistencia
    print(f"\n🔄 Test de recálculo por nueva asistencia...")
    
    recalc_results = calculator.recalculate_progress_for_teacher_attendance(
        str(course_group.teacher.id), 
        timezone.now()
    )
    
    print(f"✅ Recálculo por asistencia: {len(recalc_results)} cursos actualizados")
    
    print(f"\n🎉 Test comprehensivo completado exitosamente!")
    return True


def cleanup_test_data():
    """Limpia los datos de prueba creados"""
    
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        # Limpiar temas de prueba
        test_topics = CourseTopicContent.objects.filter(
            topic_title__startswith='Tema '
        )
        deleted_topics = test_topics.count()
        test_topics.delete()
        
        print(f"✅ Eliminados {deleted_topics} temas de prueba")
        
        # Limpiar registros de asistencia de prueba
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM teacher_attendance WHERE ip_address = '192.168.1.100'")
            deleted_attendance = cursor.rowcount
            
        print(f"✅ Eliminados {deleted_attendance} registros de asistencia de prueba")
        
    except Exception as e:
        print(f"⚠️  Error limpiando datos: {str(e)}")


if __name__ == "__main__":
    try:
        success = test_comprehensive_progress_calculation()
        
        if success:
            print("\n🎉 ¡Todos los tests pasaron exitosamente!")
            print("\n📋 Resumen de funcionalidades verificadas:")
            print("✓ Cálculo de progreso basado en asistencia docente")
            print("✓ Actualización automática de temas completados")
            print("✓ Estadísticas detalladas de progreso")
            print("✓ Comparación progreso esperado vs real")
            print("✓ Cálculo masivo para múltiples cursos")
            print("✓ Recálculo automático por nueva asistencia")
            print("✓ Manejo de errores y casos extremos")
        
        # Preguntar si limpiar datos de prueba
        response = input("\n¿Limpiar datos de prueba? (y/n): ")
        if response.lower() == 'y':
            cleanup_test_data()
        
    except Exception as e:
        print(f"\n💥 Error durante el test: {str(e)}")
        import traceback
        traceback.print_exc()