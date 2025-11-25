#!/usr/bin/env python3
"""
Test script para verificar el servicio de gestión de contenido del curso
"""

import os
import sys
import django
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from servicios.servicioContenidoCurso import CourseContentManager
from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod, CourseTopicContent
)


def test_course_content_manager():
    """Test completo del servicio de gestión de contenido"""
    
    print("=== Test del Servicio de Gestión de Contenido del Curso ===\n")
    
    # Inicializar el servicio
    content_manager = CourseContentManager()
    
    try:
        with transaction.atomic():
            # 1. Crear datos de prueba
            print("1. Creando datos de prueba...")
            
            # Crear usuario profesor con timestamp para evitar duplicados
            import time
            timestamp = str(int(time.time()))
            
            teacher_user = User.objects.create_user(
                institutional_email=f'profesor.test.{timestamp}@universidad.edu',
                first_name='Juan',
                last_name='Pérez',
                role='teacher',
                password='test123'
            )
            
            # Crear profesor
            teacher = Teacher.objects.create(
                user=teacher_user,
                teacher_code=f'PROF{timestamp}',
                department='Ingeniería de Sistemas'
            )
            
            # Crear curso
            course = Course.objects.create(
                code=f'IS{timestamp}',
                name=f'Introducción a la Programación {timestamp}',
                credits=4,
                theory_hours=3,
                practice_hours=2
            )
            
            # Crear período académico
            period = AcademicPeriod.objects.create(
                name=f'2024-I-{timestamp}',
                start_date='2024-03-01',
                end_date='2024-07-31',
                laboratory_enrollment_start='2024-02-15',
                laboratory_enrollment_end='2024-02-28',
                enrollment_change_deadline='2024-03-15',
                is_active=True
            )
            
            # Crear grupo de curso
            course_group = CourseGroup.objects.create(
                course=course,
                academic_period=period,
                group_code='A',
                teacher=teacher,
                capacity=30,
                total_planned_classes=68,
                classes_attended_by_teacher=20,
                course_progress_percentage=30.0
            )
            
            print(f"   ✓ Creado curso: {course}")
            print(f"   ✓ Creado grupo: {course_group}")
            print(f"   ✓ Profesor asignado: {teacher.user.get_full_name()}")
            print(f"   ✓ Progreso actual: {course_group.course_progress_percentage}%\n")
            
            # 2. Test de cálculo de porcentajes
            print("2. Probando cálculo de porcentajes...")
            
            percentages_5 = content_manager.calculate_topic_percentages(5)
            percentages_10 = content_manager.calculate_topic_percentages(10)
            percentages_7 = content_manager.calculate_topic_percentages(7)
            
            print(f"   ✓ 5 temas: {percentages_5} (suma: {sum(percentages_5)})")
            print(f"   ✓ 10 temas: {percentages_10} (suma: {sum(percentages_10)})")
            print(f"   ✓ 7 temas: {percentages_7} (suma: {sum(percentages_7)})\n")
            
            # 3. Test de subida de temas
            print("3. Probando subida de temas...")
            
            topics_data = [
                {'title': 'Introducción a la Programación', 'description': 'Conceptos básicos'},
                {'title': 'Variables y Tipos de Datos', 'description': 'Declaración y uso de variables'},
                {'title': 'Estructuras de Control', 'description': 'If, while, for'},
                {'title': 'Funciones', 'description': 'Definición y uso de funciones'},
                {'title': 'Arrays y Listas', 'description': 'Manejo de estructuras de datos'},
                {'title': 'Programación Orientada a Objetos', 'description': 'Clases y objetos'},
                {'title': 'Manejo de Archivos', 'description': 'Lectura y escritura de archivos'},
                {'title': 'Excepciones', 'description': 'Manejo de errores'},
            ]
            
            result = content_manager.upload_course_topics(
                course_group_id=str(course_group.id),
                topics=topics_data,
                teacher_id=str(teacher.id)
            )
            
            if result['success']:
                print(f"   ✓ Temas creados exitosamente: {result['topics_created']}")
                print(f"   ✓ Mensaje: {result['message']}")
                
                # Mostrar algunos temas creados
                for i, topic in enumerate(result['topics'][:3]):
                    print(f"      - {topic['title']} ({topic['percentage']}%)")
                if len(result['topics']) > 3:
                    print(f"      ... y {len(result['topics']) - 3} más")
            else:
                print(f"   ✗ Error: {result['error']}")
                return
            
            print()
            
            # 4. Test de obtención de temas
            print("4. Probando obtención de temas...")
            
            topics_result = content_manager.get_course_topics(str(course_group.id))
            
            if topics_result['success']:
                print(f"   ✓ Total de temas: {topics_result['total_topics']}")
                print(f"   ✓ Temas completados: {topics_result['completed_topics']}")
                print(f"   ✓ Curso: {topics_result['course_group']}")
                
                # Mostrar estado de completado
                completed_count = 0
                for topic in topics_result['topics']:
                    if topic['completed']:
                        completed_count += 1
                        print(f"      ✓ {topic['title']} - COMPLETADO")
                    else:
                        print(f"      ○ {topic['title']} - PENDIENTE")
                
                print(f"   ✓ {completed_count} de {topics_result['total_topics']} temas completados automáticamente\n")
            else:
                print(f"   ✗ Error: {topics_result['error']}")
                return
            
            # 5. Test de actualización de progreso
            print("5. Probando actualización de progreso...")
            
            # Simular cambio de progreso
            course_group.course_progress_percentage = 50.0
            course_group.classes_attended_by_teacher = 34
            course_group.save()
            
            update_result = content_manager.update_topic_completion_by_progress(str(course_group.id))
            
            if update_result['success']:
                print(f"   ✓ {update_result['message']}")
                print(f"   ✓ Progreso actual: {update_result['current_progress']}%")
                print(f"   ✓ Temas que deberían estar completados: {update_result['completed_topics']}")
                print(f"   ✓ Temas actualizados: {update_result['topics_updated']}")
            else:
                print(f"   ✗ Error: {update_result['error']}")
                return
            
            print()
            
            # 6. Test de agregar tema individual
            print("6. Probando agregar tema individual...")
            
            new_topic = {'title': 'Proyecto Final', 'description': 'Desarrollo de proyecto integrador'}
            add_result = content_manager.add_single_topic(
                course_group_id=str(course_group.id),
                topic_data=new_topic,
                teacher_id=str(teacher.id)
            )
            
            if add_result['success']:
                print(f"   ✓ {add_result['message']}")
                print(f"   ✓ Tema creado: {add_result['topic_created']['title']}")
                print(f"   ✓ Total de temas ahora: {add_result['total_topics']}")
            else:
                print(f"   ✗ Error: {add_result['error']}")
                return
            
            print()
            
            # 7. Test de resumen de progreso
            print("7. Probando resumen de progreso...")
            
            summary = content_manager.get_course_progress_summary(str(course_group.id))
            
            if summary['success']:
                print(f"   ✓ Curso: {summary['course_name']} - Grupo {summary['group_code']}")
                print(f"   ✓ Profesor: {summary['teacher']}")
                print(f"   ✓ Progreso del curso: {summary['progress_percentage']}%")
                print(f"   ✓ Temas completados: {summary['completed_topics']}/{summary['total_topics']}")
                print(f"   ✓ Tasa de completado: {summary['completion_rate']:.1f}%")
                print(f"   ✓ Clases asistidas: {summary['classes_attended']}/{summary['total_planned_classes']}")
            else:
                print(f"   ✗ Error: {summary['error']}")
                return
            
            print()
            
            # 8. Test de temas completados
            print("8. Probando obtención de temas completados...")
            
            completed_topics = content_manager.get_completed_topics(str(course_group.id))
            
            print(f"   ✓ Temas completados encontrados: {len(completed_topics)}")
            for topic in completed_topics:
                print(f"      ✓ {topic['title']} (Orden: {topic['order']}, {topic['percentage']}%)")
            
            print()
            
            # 9. Test de validaciones
            print("9. Probando validaciones...")
            
            # Test con profesor incorrecto
            fake_teacher = Teacher.objects.create(
                user=User.objects.create_user(
                    institutional_email='fake@test.com',
                    first_name='Fake',
                    last_name='Teacher',
                    role='teacher',
                    password='test123'
                ),
                teacher_code='FAKE001'
            )
            
            invalid_result = content_manager.upload_course_topics(
                course_group_id=str(course_group.id),
                topics=[{'title': 'Test'}],
                teacher_id=str(fake_teacher.id)
            )
            
            if not invalid_result['success']:
                print(f"   ✓ Validación correcta: {invalid_result['error']}")
            else:
                print("   ✗ La validación debería haber fallado")
            
            # Test con curso inexistente
            invalid_course_result = content_manager.get_course_topics('00000000-0000-0000-0000-000000000000')
            
            if not invalid_course_result['success']:
                print(f"   ✓ Validación correcta: {invalid_course_result['error']}")
            else:
                print("   ✗ La validación debería haber fallado")
            
            print("\n=== TODOS LOS TESTS COMPLETADOS EXITOSAMENTE ===")
            
            # Rollback para limpiar datos de prueba
            raise Exception("Rollback intencional para limpiar datos de prueba")
            
    except Exception as e:
        if "Rollback intencional" in str(e):
            print("\n✓ Datos de prueba limpiados correctamente")
        else:
            print(f"\n✗ Error durante las pruebas: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    test_course_content_manager()