#!/usr/bin/env python
"""
Test script para verificar el sistema de asistencia docente automática
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from repositorio.postgres_repository.models import Teacher, User, TeacherAttendance
from servicios.servicioAsistenciaDocente import ServicioAsistenciaDocente


def test_teacher_attendance_system():
    """Test completo del sistema de asistencia docente"""
    print("=== Test del Sistema de Asistencia Docente ===\n")
    
    # Inicializar servicio
    servicio = ServicioAsistenciaDocente()
    
    # 1. Buscar un docente existente o crear uno de prueba
    print("1. Buscando docente de prueba...")
    try:
        teacher = Teacher.objects.first()
        if not teacher:
            print("   No se encontraron docentes. Creando uno de prueba...")
            # Crear usuario docente de prueba
            user = User.objects.create_user(
                institutional_email='test.teacher@universidad.edu',
                first_name='Profesor',
                last_name='Prueba',
                role='teacher',
                password='test123'
            )
            teacher = Teacher.objects.create(
                user=user,
                teacher_code='TEST001',
                department='Sistemas',
                specialty='Programación'
            )
            print(f"   ✓ Docente creado: {teacher.user.get_full_name()}")
        else:
            print(f"   ✓ Usando docente existente: {teacher.user.get_full_name()}")
    except Exception as e:
        print(f"   ✗ Error creando/buscando docente: {e}")
        return False
    
    # 2. Test de registro de login automático
    print("\n2. Probando registro de login automático...")
    try:
        attendance = servicio.registrar_login_automatico(
            teacher_id=str(teacher.id),
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 Test Browser'
        )
        
        if attendance:
            print(f"   ✓ Login registrado exitosamente")
            print(f"   - ID: {attendance.id}")
            print(f"   - Hora: {attendance.login_time}")
            print(f"   - IP: {attendance.ip_address}")
            print(f"   - Tipo: {attendance.get_access_type_display()}")
        else:
            print("   ✗ Error registrando login")
            return False
    except Exception as e:
        print(f"   ✗ Error en login automático: {e}")
        return False
    
    # 3. Test de registro de logout automático
    print("\n3. Probando registro de logout automático...")
    try:
        # Simular que pasó tiempo (para testing, modificamos el login_time)
        attendance.login_time = timezone.now() - timedelta(hours=2)
        attendance.save()
        
        success = servicio.registrar_logout_automatico(str(teacher.id))
        
        if success:
            # Recargar el objeto para ver los cambios
            attendance.refresh_from_db()
            print(f"   ✓ Logout registrado exitosamente")
            print(f"   - Hora logout: {attendance.logout_time}")
            print(f"   - Duración: {attendance.duration_hours} horas")
            print(f"   - Sesión válida: {'Sí' if attendance.is_valid_session else 'No'}")
            print(f"   - Actualizó progreso: {'Sí' if attendance.triggered_progress_update else 'No'}")
        else:
            print("   ✗ Error registrando logout")
            return False
    except Exception as e:
        print(f"   ✗ Error en logout automático: {e}")
        return False
    
    # 4. Test de cálculo de estadísticas
    print("\n4. Probando cálculo de estadísticas...")
    try:
        stats = servicio.calcular_estadisticas_asistencia(str(teacher.id))
        
        if stats:
            print(f"   ✓ Estadísticas calculadas:")
            print(f"   - Docente: {stats['teacher_name']}")
            print(f"   - Total sesiones: {stats['total_sesiones']}")
            print(f"   - Sesiones completas: {stats['sesiones_completas']}")
            print(f"   - Días asistencia: {stats['dias_asistencia']}")
            print(f"   - Porcentaje asistencia: {stats['porcentaje_asistencia']}%")
            print(f"   - Tiempo total: {stats['tiempo_total_horas']} horas")
        else:
            print("   ✗ Error calculando estadísticas")
            return False
    except Exception as e:
        print(f"   ✗ Error en cálculo de estadísticas: {e}")
        return False
    
    # 5. Test de impacto en progreso de cursos
    print("\n5. Probando impacto en progreso de cursos...")
    try:
        impacto = servicio.obtener_impacto_progreso_cursos(str(teacher.id))
        
        print(f"   ✓ Impacto calculado para {len(impacto)} cursos:")
        for curso in impacto:
            print(f"   - {curso['course_name']} (Grupo {curso['group_code']})")
            print(f"     Progreso actual: {curso['current_progress']}%")
            print(f"     Progreso calculado: {curso['calculated_progress']}%")
    except Exception as e:
        print(f"   ✗ Error calculando impacto: {e}")
        return False
    
    # 6. Test de sesiones activas
    print("\n6. Probando obtención de sesiones activas...")
    try:
        # Crear una sesión activa (sin logout)
        active_attendance = servicio.registrar_login_automatico(
            teacher_id=str(teacher.id),
            ip_address='10.0.0.50',
            user_agent='Test Active Session'
        )
        
        sesiones_activas = servicio.obtener_sesiones_activas()
        
        print(f"   ✓ Sesiones activas encontradas: {len(sesiones_activas)}")
        for sesion in sesiones_activas:
            print(f"   - {sesion['teacher_name']}")
            print(f"     Login: {sesion['login_time']}")
            print(f"     Duración: {sesion['duration_minutes']} minutos")
            print(f"     Tipo: {sesion['access_type']}")
    except Exception as e:
        print(f"   ✗ Error obteniendo sesiones activas: {e}")
        return False
    
    print("\n=== ✓ Todos los tests completados exitosamente ===")
    return True


def cleanup_test_data():
    """Limpia los datos de prueba creados"""
    print("\n=== Limpiando datos de prueba ===")
    try:
        # Eliminar registros de asistencia de prueba
        TeacherAttendance.objects.filter(
            teacher__user__institutional_email='test.teacher@universidad.edu'
        ).delete()
        
        # Eliminar docente de prueba si fue creado
        Teacher.objects.filter(
            user__institutional_email='test.teacher@universidad.edu'
        ).delete()
        
        User.objects.filter(
            institutional_email='test.teacher@universidad.edu'
        ).delete()
        
        print("✓ Datos de prueba eliminados")
    except Exception as e:
        print(f"✗ Error limpiando datos: {e}")


if __name__ == '__main__':
    try:
        success = test_teacher_attendance_system()
        
        if success:
            print("\n🎉 Sistema de asistencia docente funcionando correctamente!")
        else:
            print("\n❌ Hay problemas en el sistema de asistencia docente")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
    finally:
        # Preguntar si limpiar datos de prueba
        try:
            response = input("\n¿Limpiar datos de prueba? (s/N): ").lower()
            if response in ['s', 'si', 'sí', 'y', 'yes']:
                cleanup_test_data()
        except:
            pass