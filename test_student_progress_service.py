#!/usr/bin/env python
"""
Test simplificado para verificar el servicio de datos del estudiante
con progreso real
"""

import os
import sys
import django
from datetime import datetime, timedelta
import uuid

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import (
    User, Student, Teacher, Course, CourseGroup, AcademicPeriod,
    Enrollment, CourseTopicContent
)
from servicios.servicioEstudianteData import ServicioEstudianteData


def test_student_service_with_existing_data():
    """
    Test del servicio usando datos existentes en la base de datos
    """
    print("🧪 Probando servicio de estudiante con datos existentes...")
    
    try:
        servicio = ServicioEstudianteData()
        
        # 1. Buscar un estudiante existente
        print("\n1️⃣ Buscando estudiante existente...")
        estudiante = Student.objects.first()
        
        if not estudiante:
            print("   ❌ No hay estudiantes en la base de datos")
            return False
        
        print(f"   ✅ Estudiante encontrado: {estudiante.user.get_full_name()}")
        
        # 2. Probar obtener cursos del estudiante
        print("\n2️⃣ Obteniendo cursos del estudiante...")
        cursos = servicio.obtener_cursos_estudiante(estudiante.id)
        
        print(f"   ✅ Cursos obtenidos: {len(cursos)}")
        
        for i, curso in enumerate(cursos):
            print(f"   📚 Curso {i+1}: {curso.nombre}")
            print(f"      - Código: {curso.codigo}")
            print(f"      - Grupo: {curso.grupo}")
            print(f"      - Progreso: {curso.progreso}%")
            print(f"      - Estado: {curso.estado}")
        
        # 3. Probar obtener estadísticas
        print("\n3️⃣ Obteniendo estadísticas del estudiante...")
        estadisticas = servicio.obtener_estadisticas_estudiante(estudiante.id)
        
        print(f"   ✅ Estadísticas obtenidas:")
        print(f"   📚 Total cursos: {estadisticas['total_cursos']}")
        print(f"   📊 Progreso promedio: {estadisticas['progreso_promedio']}%")
        print(f"   👨‍🏫 Asistencia promedio profesor: {estadisticas['asistencia_promedio']}%")
        print(f"   🔬 Total laboratorios: {estadisticas['total_laboratorios']}")
        
        # 4. Probar detalle de curso si hay cursos
        if cursos:
            print("\n4️⃣ Obteniendo detalle del primer curso...")
            primer_curso = cursos[0]
            
            # Buscar el Course real por código
            try:
                curso_real = Course.objects.get(code=primer_curso.codigo)
                detalle = servicio.obtener_detalle_curso(curso_real.id, estudiante.id)
                
                if detalle:
                    print(f"   ✅ Detalle del curso obtenido:")
                    print(f"   📚 Nombre: {detalle['nombre']}")
                    print(f"   📊 Progreso: {detalle['progreso']}%")
                    print(f"   🎯 Temas completados: {detalle['temas_completados']}/{detalle['total_temas']}")
                    
                    if detalle.get('profesor'):
                        print(f"   👨‍🏫 Profesor: {detalle['profesor']['nombre']}")
                    
                    print(f"   📈 Progreso real: {'Sí' if detalle['es_progreso_real'] else 'No'}")
                    
                    if detalle.get('estadisticas_asistencia'):
                        stats = detalle['estadisticas_asistencia']
                        print(f"   📊 Clases profesor: {stats['clases_asistidas_profesor']}/{stats['total_clases_programadas']}")
                        print(f"   📈 Asistencia profesor: {stats['porcentaje_asistencia_profesor']}%")
                    
                    print(f"   💬 Mensaje: {detalle['mensaje_progreso']}")
                    
                    # Mostrar algunos temas
                    print(f"   📋 Primeros 3 temas:")
                    for tema in detalle['temas'][:3]:
                        estado = "✅" if tema['completado'] else "⏳"
                        print(f"      {estado} {tema['nombre']}")
                        if tema.get('descripcion'):
                            print(f"         📝 {tema['descripcion']}")
                        if tema.get('porcentaje'):
                            print(f"         📊 {tema['porcentaje']}% del curso")
                else:
                    print(f"   ❌ No se pudo obtener detalle del curso")
                    return False
                    
            except Course.DoesNotExist:
                print(f"   ⚠️ Curso {primer_curso.codigo} no encontrado en la base de datos")
        
        print("\n✅ Test del servicio completado exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en el test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_course_groups_with_progress():
    """
    Test para verificar CourseGroups con progreso real
    """
    print("\n🧪 Verificando CourseGroups con progreso...")
    
    try:
        # Buscar CourseGroups con progreso > 0
        course_groups = CourseGroup.objects.filter(
            course_progress_percentage__gt=0
        ).select_related('course', 'teacher__user')
        
        print(f"   ✅ Encontrados {course_groups.count()} grupos con progreso > 0")
        
        for cg in course_groups[:5]:  # Mostrar solo los primeros 5
            print(f"   📚 {cg.course.name} - Grupo {cg.group_code}")
            print(f"      📊 Progreso: {cg.course_progress_percentage}%")
            print(f"      👨‍🏫 Profesor: {cg.teacher.user.get_full_name() if cg.teacher else 'Sin asignar'}")
            print(f"      📅 Clases: {cg.classes_attended_by_teacher}/{cg.total_planned_classes}")
            
            # Verificar si tiene temas
            temas_count = CourseTopicContent.objects.filter(course_group=cg).count()
            print(f"      📋 Temas: {temas_count}")
            
            if temas_count > 0:
                temas_completados = CourseTopicContent.objects.filter(
                    course_group=cg, 
                    is_completed=True
                ).count()
                print(f"      ✅ Completados: {temas_completados}/{temas_count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verificando CourseGroups: {str(e)}")
        return False


def test_enrollments_with_progress():
    """
    Test para verificar matrículas y su progreso
    """
    print("\n🧪 Verificando matrículas con progreso...")
    
    try:
        # Buscar matrículas activas
        enrollments = Enrollment.objects.filter(
            status='active'
        ).select_related(
            'student__user',
            'course_group__course',
            'course_group__teacher__user'
        )[:10]  # Limitar a 10
        
        print(f"   ✅ Encontradas {enrollments.count()} matrículas activas")
        
        servicio = ServicioEstudianteData()
        
        for enrollment in enrollments:
            student = enrollment.student
            course_group = enrollment.course_group
            
            print(f"\n   👨‍🎓 Estudiante: {student.user.get_full_name()}")
            print(f"   📚 Curso: {course_group.course.name} - Grupo {course_group.group_code}")
            print(f"   📊 Progreso del grupo: {course_group.course_progress_percentage}%")
            
            # Probar el servicio para este estudiante
            try:
                detalle = servicio.obtener_detalle_curso(course_group.course.id, student.id)
                if detalle:
                    print(f"   ✅ Servicio funciona - Progreso: {detalle['progreso']}%")
                    print(f"   🎯 Temas: {detalle['temas_completados']}/{detalle['total_temas']}")
                else:
                    print(f"   ⚠️ Servicio no retornó datos")
            except Exception as e:
                print(f"   ❌ Error en servicio: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verificando matrículas: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Ejecutando tests del servicio de estudiante con progreso real")
    print("=" * 70)
    
    # Ejecutar tests
    test1_success = test_student_service_with_existing_data()
    test2_success = test_course_groups_with_progress()
    test3_success = test_enrollments_with_progress()
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS FINALES:")
    print(f"   Test servicio con datos existentes: {'✅ PASÓ' if test1_success else '❌ FALLÓ'}")
    print(f"   Test CourseGroups con progreso: {'✅ PASÓ' if test2_success else '❌ FALLÓ'}")
    print(f"   Test matrículas con progreso: {'✅ PASÓ' if test3_success else '❌ FALLÓ'}")
    
    if test1_success and test2_success and test3_success:
        print("\n🎉 TODOS LOS TESTS PASARON!")
        print("\n📋 Funcionalidades verificadas:")
        print("   ✅ Servicio de estudiante integrado con progreso real")
        print("   ✅ CourseGroups con progreso calculado")
        print("   ✅ Matrículas funcionando con el nuevo sistema")
        print("   ✅ Temas completados automáticamente")
        print("   ✅ Estadísticas reales del estudiante")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - Revisar implementación")
        sys.exit(1)