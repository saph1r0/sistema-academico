#!/usr/bin/env python3
"""
Script para probar que el dashboard y las vistas funcionan correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from presentacion.profesor.views import ProfesorDashboardView, ProfesorAsistenciaView, ProfesorNotasView

def crear_mock_user(user_id):
    """Crear un mock user para las pruebas"""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
            self.is_authenticated = True
        
        def get_full_name(self):
            return "Profesor Test"
    
    return MockUser(user_id)

def test_dashboard_view():
    """Probar la vista del dashboard"""
    print("=== PROBANDO VISTA DEL DASHBOARD ===\n")
    
    try:
        with connection.cursor() as cursor:
            # Buscar un profesor real con cursos asignados
            cursor.execute("""
                SELECT DISTINCT u.id
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                JOIN course_groups cg ON t.id = cg.teacher_id
                WHERE u.role = 'profesor'
                LIMIT 1;
            """)
            
            result = cursor.fetchone()
            if not result:
                print("❌ No se encontró profesor con cursos asignados")
                return
            
            user_id = result[0]
            print(f"✅ Probando con usuario ID: {user_id}")
            
            # Crear request mock
            factory = RequestFactory()
            request = factory.get('/profesor/dashboard/')
            request.user = crear_mock_user(user_id)
            
            # Probar la vista
            view = ProfesorDashboardView()
            view.request = request
            
            context = view.get_context_data()
            
            print("📊 RESULTADOS DEL DASHBOARD:")
            print(f"   - Total cursos: {context.get('total_courses', 0)}")
            print(f"   - Total estudiantes: {context.get('total_students', 0)}")
            print(f"   - Progreso promedio: {context.get('average_progress', 0)}%")
            
            if context.get('assigned_course'):
                curso = context['assigned_course']
                print(f"   - Curso asignado: {curso['name']}")
                print(f"   - Código: {curso['code']}")
                print(f"   - Grupo: {curso['group']}")
                print(f"   - Estudiantes en curso: {curso['students_count']}")
            else:
                print("   ⚠️  No hay curso asignado")
            
            if context.get('error'):
                print(f"   ❌ Error: {context['error']}")
            else:
                print("   ✅ Dashboard funcionando correctamente")
                
    except Exception as e:
        print(f"❌ Error probando dashboard: {str(e)}")
        import traceback
        traceback.print_exc()

def test_asistencia_view():
    """Probar la vista de asistencia"""
    print("\n=== PROBANDO VISTA DE ASISTENCIA ===\n")
    
    try:
        with connection.cursor() as cursor:
            # Buscar un profesor real con cursos asignados
            cursor.execute("""
                SELECT DISTINCT u.id
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                JOIN course_groups cg ON t.id = cg.teacher_id
                JOIN enrollments e ON cg.id = e.course_group_id
                WHERE u.role = 'profesor'
                LIMIT 1;
            """)
            
            result = cursor.fetchone()
            if not result:
                print("❌ No se encontró profesor con estudiantes matriculados")
                return
            
            user_id = result[0]
            print(f"✅ Probando con usuario ID: {user_id}")
            
            # Crear request mock
            factory = RequestFactory()
            request = factory.get('/profesor/asistencia/')
            request.user = crear_mock_user(user_id)
            
            # Probar la vista
            view = ProfesorAsistenciaView()
            view.request = request
            
            context = view.get_context_data()
            
            print("📋 RESULTADOS DE ASISTENCIA:")
            print(f"   - Cursos disponibles: {len(context.get('courses', []))}")
            print(f"   - Estudiantes: {len(context.get('students', []))}")
            
            if context.get('courses'):
                for course in context['courses']:
                    print(f"   - Curso: {course['code']} - {course['name']}")
            
            if context.get('students'):
                print(f"   - Primeros 3 estudiantes:")
                for i, student in enumerate(context['students'][:3]):
                    print(f"     {i+1}. {student['student_code']}: {student['user'].first_name} {student['user'].last_name}")
            
            if context.get('error'):
                print(f"   ❌ Error: {context['error']}")
            else:
                print("   ✅ Vista de asistencia funcionando correctamente")
                
    except Exception as e:
        print(f"❌ Error probando asistencia: {str(e)}")
        import traceback
        traceback.print_exc()

def test_notas_view():
    """Probar la vista de notas"""
    print("\n=== PROBANDO VISTA DE NOTAS ===\n")
    
    try:
        with connection.cursor() as cursor:
            # Buscar un profesor real con cursos asignados
            cursor.execute("""
                SELECT DISTINCT u.id
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                JOIN course_groups cg ON t.id = cg.teacher_id
                JOIN enrollments e ON cg.id = e.course_group_id
                WHERE u.role = 'profesor'
                LIMIT 1;
            """)
            
            result = cursor.fetchone()
            if not result:
                print("❌ No se encontró profesor con estudiantes matriculados")
                return
            
            user_id = result[0]
            print(f"✅ Probando con usuario ID: {user_id}")
            
            # Crear request mock
            factory = RequestFactory()
            request = factory.get('/profesor/notas/')
            request.user = crear_mock_user(user_id)
            
            # Probar la vista
            view = ProfesorNotasView()
            view.request = request
            
            context = view.get_context_data()
            
            print("📝 RESULTADOS DE NOTAS:")
            print(f"   - Cursos disponibles: {len(context.get('courses', []))}")
            print(f"   - Estudiantes: {len(context.get('students', []))}")
            
            if context.get('courses'):
                for course in context['courses']:
                    print(f"   - Curso: {course['code']} - {course['name']}")
            
            grade_stats = context.get('grade_stats', {})
            print(f"   - Promedio general: {grade_stats.get('average', 0)}")
            print(f"   - Total estudiantes: {grade_stats.get('total', 0)}")
            print(f"   - Aprobados: {grade_stats.get('approved', 0)}")
            
            if context.get('error'):
                print(f"   ❌ Error: {context['error']}")
            else:
                print("   ✅ Vista de notas funcionando correctamente")
                
    except Exception as e:
        print(f"❌ Error probando notas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Probando todas las vistas del profesor...\n")
    test_dashboard_view()
    test_asistencia_view()
    test_notas_view()
    print("\n=== PRUEBAS COMPLETADAS ===")
    print("\n✅ Si no hay errores, el dashboard del profesor debería mostrar:")
    print("   - Los cursos reales asignados al profesor logueado")
    print("   - Los estudiantes matriculados en esos cursos")
    print("   - Las estadísticas reales basadas en los datos de la base de datos")
    print("\n🎯 Ahora puedes acceder al dashboard del profesor en el navegador")