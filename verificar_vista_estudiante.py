#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar que la vista del estudiante funciona correctamente
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import Student, User, Enrollment
from servicios.servicioEstudianteData import ServicioEstudianteData

def main():
    """Verifica que la funcionalidad del estudiante funcione"""
    print("=" * 80)
    print("VERIFICACION DE VISTA DEL ESTUDIANTE")
    print("=" * 80)
    
    try:
        # Buscar un estudiante que tenga inscripciones
        estudiante_con_cursos = Student.objects.filter(
            enrollment__status='active'
        ).first()
        
        if not estudiante_con_cursos:
            print("No se encontraron estudiantes con cursos matriculados")
            return False
        
        print(f"Estudiante encontrado: {estudiante_con_cursos.student_code}")
        print(f"Usuario asociado: {estudiante_con_cursos.user.first_name} {estudiante_con_cursos.user.last_name}")
        
        # Probar el servicio de datos del estudiante
        servicio = ServicioEstudianteData()
        
        # Obtener cursos del estudiante
        cursos = servicio.obtener_cursos_estudiante(estudiante_con_cursos.id)
        print(f"\nCursos matriculados: {len(cursos)}")
        
        for i, curso in enumerate(cursos, 1):
            print(f"  {i}. {curso.nombre} ({curso.codigo}) - Grupo {curso.grupo}")
            
            # Probar detalle del curso
            detalle = servicio.obtener_detalle_curso(curso.id, estudiante_con_cursos.id)
            if detalle:
                print(f"     Progreso: {detalle.get('progreso', 0):.1f}%")
                print(f"     Temas: {detalle.get('temas_completados', 0)}/{detalle.get('total_temas', 0)}")
        
        # Obtener estadísticas
        estadisticas = servicio.obtener_estadisticas_estudiante(estudiante_con_cursos.id)
        print(f"\nEstadísticas:")
        print(f"  Total cursos: {estadisticas.get('total_cursos', 0)}")
        print(f"  Asistencia promedio: {estadisticas.get('asistencia_promedio', 0):.1f}%")
        print(f"  Progreso promedio: {estadisticas.get('progreso_promedio', 0):.1f}%")
        
        print("\n" + "=" * 80)
        print("INSTRUCCIONES PARA PROBAR EN EL NAVEGADOR:")
        print("=" * 80)
        print("1. Inicia el servidor: poetry run python manage.py runserver")
        print("2. Ve a: http://127.0.0.1:8000/")
        print(f"3. Inicia sesión con el usuario: {estudiante_con_cursos.user.institutional_email}")
        print("4. Deberías ver los cursos matriculados en el dashboard")
        print("5. Haz clic en cualquier curso para ver el detalle con:")
        print("   - Barra de progreso")
        print("   - Lista de temas")
        print("   - Estado de cada tema (completado/pendiente)")
        
        print("\n✓ VERIFICACION COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"Error durante la verificación: {e}")
        return False

if __name__ == '__main__':
    main()