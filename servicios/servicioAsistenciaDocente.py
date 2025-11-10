#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Servicio para gestión automática de asistencia docente
Implementa el registro automático de login/logout y cálculo de progreso
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from repositorio.postgres_repository.models import TeacherAttendance, Teacher, CourseGroup
from typing import Optional, Dict, List, Tuple


logger = logging.getLogger(__name__)


class ServicioAsistenciaDocente:
    """
    Servicio para manejo automático de asistencia docente
    Registra automáticamente login/logout y actualiza progreso de cursos
    """
    
    def __init__(self):
        self.logger = logger
    
    def registrar_login_automatico(self, teacher_id: str, ip_address: str, user_agent: str = '') -> Optional[TeacherAttendance]:
        """
        Registra automáticamente el login de un docente
        
        Args:
            teacher_id: ID del docente
            ip_address: Dirección IP del acceso
            user_agent: User agent del navegador
            
        Returns:
            TeacherAttendance: Registro de asistencia creado o None si hay error
        """
        try:
            with transaction.atomic():
                teacher = Teacher.objects.get(id=teacher_id)
                
                # Verificar si ya hay un login activo hoy
                today = timezone.now().date()
                existing_login = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    login_time__date=today,
                    logout_time__isnull=True
                ).first()
                
                if existing_login:
                    self.logger.info(f"Docente {teacher.user.get_full_name()} ya tiene sesión activa hoy")
                    return existing_login
                
                # Determinar tipo de acceso basado en IP
                access_type = self._determinar_tipo_acceso(ip_address)
                
                # Crear nuevo registro de asistencia
                attendance = TeacherAttendance.objects.create(
                    teacher=teacher,
                    login_time=timezone.now(),
                    ip_address=ip_address,
                    access_type=access_type,
                    user_agent=user_agent[:500]  # Limitar longitud
                )
                
                self.logger.info(
                    f"Login registrado para {teacher.user.get_full_name()} "
                    f"desde IP {ip_address} ({access_type})"
                )
                
                return attendance
                
        except Teacher.DoesNotExist:
            self.logger.error(f"Docente con ID {teacher_id} no encontrado")
            return None
        except Exception as e:
            self.logger.error(f"Error registrando login automático: {str(e)}")
            return None
    
    def registrar_logout_automatico(self, teacher_id: str) -> bool:
        """
        Registra automáticamente el logout de un docente
        
        Args:
            teacher_id: ID del docente
            
        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        try:
            with transaction.atomic():
                teacher = Teacher.objects.get(id=teacher_id)
                
                # Buscar sesión activa más reciente
                active_session = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    logout_time__isnull=True
                ).order_by('-login_time').first()
                
                if not active_session:
                    self.logger.warning(f"No se encontró sesión activa para {teacher.user.get_full_name()}")
                    return False
                
                # Registrar logout
                logout_time = timezone.now()
                active_session.logout_time = logout_time
                
                # El modelo calculará automáticamente la duración en el save()
                active_session.save()
                
                # Solo contar como clase si la sesión duró más de 30 minutos
                if active_session.is_valid_session:
                    self._actualizar_progreso_cursos(teacher, active_session.login_time.date())
                    active_session.triggered_progress_update = True
                    active_session.save()
                
                self.logger.info(
                    f"Logout registrado para {teacher.user.get_full_name()} "
                    f"- Duración: {active_session.duration_hours} horas"
                )
                
                return True
                
        except Teacher.DoesNotExist:
            self.logger.error(f"Docente con ID {teacher_id} no encontrado")
            return False
        except Exception as e:
            self.logger.error(f"Error registrando logout automático: {str(e)}")
            return False
    
    def calcular_estadisticas_asistencia(self, teacher_id: str, fecha_inicio: datetime = None, fecha_fin: datetime = None) -> Dict:
        """
        Calcula estadísticas de asistencia de un docente
        
        Args:
            teacher_id: ID del docente
            fecha_inicio: Fecha de inicio del período (opcional)
            fecha_fin: Fecha de fin del período (opcional)
            
        Returns:
            Dict: Estadísticas de asistencia
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Definir período por defecto (último mes)
            if not fecha_inicio:
                fecha_inicio = timezone.now() - timedelta(days=30)
            if not fecha_fin:
                fecha_fin = timezone.now()
            
            # Obtener registros del período
            registros = TeacherAttendance.objects.filter(
                teacher=teacher,
                login_time__date__range=[fecha_inicio.date(), fecha_fin.date()]
            )
            
            # Calcular estadísticas
            total_sesiones = registros.count()
            sesiones_completas = registros.filter(logout_time__isnull=False).count()
            
            # Calcular tiempo total de sesiones
            tiempo_total = timedelta()
            for registro in registros.filter(logout_time__isnull=False):
                duracion = registro.logout_time - registro.login_time
                if duracion >= timedelta(minutes=30):  # Solo sesiones válidas
                    tiempo_total += duracion
            
            # Calcular días únicos con asistencia
            dias_asistencia = registros.values('login_time__date').distinct().count()
            
            # Calcular días laborables en el período
            dias_laborables = self._calcular_dias_laborables(fecha_inicio.date(), fecha_fin.date())
            
            # Calcular porcentaje de asistencia
            porcentaje_asistencia = (dias_asistencia / dias_laborables * 100) if dias_laborables > 0 else 0
            
            return {
                'teacher_name': teacher.user.get_full_name(),
                'periodo': {
                    'inicio': fecha_inicio.date(),
                    'fin': fecha_fin.date()
                },
                'total_sesiones': total_sesiones,
                'sesiones_completas': sesiones_completas,
                'dias_asistencia': dias_asistencia,
                'dias_laborables': dias_laborables,
                'porcentaje_asistencia': round(porcentaje_asistencia, 2),
                'tiempo_total_horas': round(tiempo_total.total_seconds() / 3600, 2),
                'promedio_horas_dia': round((tiempo_total.total_seconds() / 3600) / max(dias_asistencia, 1), 2)
            }
            
        except Teacher.DoesNotExist:
            self.logger.error(f"Docente con ID {teacher_id} no encontrado")
            return {}
        except Exception as e:
            self.logger.error(f"Error calculando estadísticas: {str(e)}")
            return {}
    
    def obtener_impacto_progreso_cursos(self, teacher_id: str) -> List[Dict]:
        """
        Obtiene el impacto de la asistencia docente en el progreso de sus cursos
        
        Args:
            teacher_id: ID del docente
            
        Returns:
            List[Dict]: Lista con información de progreso por curso
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Obtener cursos asignados al docente
            course_groups = CourseGroup.objects.filter(teacher=teacher)
            
            resultados = []
            
            for course_group in course_groups:
                # Calcular días de asistencia para este curso (aproximado)
                dias_asistencia = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    logout_time__isnull=False
                ).count()
                
                # Calcular progreso basado en asistencia
                progreso_calculado = min((dias_asistencia / course_group.total_planned_classes) * 100, 100)
                
                resultados.append({
                    'course_group_id': str(course_group.id),
                    'course_name': course_group.course.name,
                    'group_code': course_group.group_code,
                    'total_planned_classes': course_group.total_planned_classes,
                    'classes_attended_by_teacher': dias_asistencia,
                    'current_progress': course_group.course_progress_percentage,
                    'calculated_progress': round(progreso_calculado, 2),
                    'progress_difference': round(progreso_calculado - course_group.course_progress_percentage, 2)
                })
            
            return resultados
            
        except Teacher.DoesNotExist:
            self.logger.error(f"Docente con ID {teacher_id} no encontrado")
            return []
        except Exception as e:
            self.logger.error(f"Error obteniendo impacto en progreso: {str(e)}")
            return []
    
    def _determinar_tipo_acceso(self, ip_address: str) -> str:
        """
        Determina el tipo de acceso basado en la dirección IP
        
        Args:
            ip_address: Dirección IP del acceso
            
        Returns:
            str: Tipo de acceso ('presential', 'remote', 'virtual', 'unknown')
        """
        # IPs de la universidad (ejemplo - ajustar según la realidad)
        university_ips = [
            '192.168.',  # Red interna
            '10.0.',     # Red interna alternativa
            '172.16.',   # Red privada
        ]
        
        # IPs de VPN conocidas (ejemplo)
        vpn_ips = [
            '10.8.',     # OpenVPN típico
            '10.9.',     # Otra configuración VPN
        ]
        
        # Verificar tipo de acceso
        for ip_prefix in university_ips:
            if ip_address.startswith(ip_prefix):
                return 'presential'
        
        for ip_prefix in vpn_ips:
            if ip_address.startswith(ip_prefix):
                return 'virtual'
        
        # Si es IP pública, asumir acceso remoto
        if not ip_address.startswith(('192.168.', '10.', '172.16.')):
            return 'remote'
        
        return 'unknown'
    
    def _actualizar_progreso_cursos(self, teacher: Teacher, fecha_clase: datetime.date) -> None:
        """
        Actualiza el progreso de los cursos del docente basado en su asistencia
        
        Args:
            teacher: Instancia del docente
            fecha_clase: Fecha de la clase asistida
        """
        try:
            # Obtener todos los cursos del docente
            course_groups = CourseGroup.objects.filter(teacher=teacher)
            
            for course_group in course_groups:
                # Contar días únicos de asistencia del docente
                dias_asistencia = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    logout_time__isnull=False,
                    login_time__date__lte=fecha_clase
                ).values('login_time__date').distinct().count()
                
                # Actualizar campos de progreso
                course_group.classes_attended_by_teacher = dias_asistencia
                
                # Calcular porcentaje de progreso
                if course_group.total_planned_classes > 0:
                    progreso = (dias_asistencia / course_group.total_planned_classes) * 100
                    course_group.course_progress_percentage = min(progreso, 100)
                
                course_group.save()
                
                self.logger.info(
                    f"Progreso actualizado para {course_group.course.name} - "
                    f"Grupo {course_group.group_code}: {course_group.course_progress_percentage:.1f}%"
                )
                
        except Exception as e:
            self.logger.error(f"Error actualizando progreso de cursos: {str(e)}")
    
    def _calcular_dias_laborables(self, fecha_inicio: datetime.date, fecha_fin: datetime.date) -> int:
        """
        Calcula el número de días laborables entre dos fechas
        
        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin
            
        Returns:
            int: Número de días laborables
        """
        dias_laborables = 0
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # Lunes = 0, Domingo = 6
            if fecha_actual.weekday() < 5:  # Lunes a Viernes
                dias_laborables += 1
            fecha_actual += timedelta(days=1)
        
        return dias_laborables
    
    def obtener_sesiones_activas(self) -> List[Dict]:
        """
        Obtiene todas las sesiones activas (sin logout)
        
        Returns:
            List[Dict]: Lista de sesiones activas
        """
        try:
            sesiones_activas = TeacherAttendance.objects.filter(
                logout_time__isnull=True
            ).select_related('teacher__user').order_by('-login_time')
            
            resultados = []
            for sesion in sesiones_activas:
                duracion = timezone.now() - sesion.login_time
                
                resultados.append({
                    'teacher_name': sesion.teacher.user.get_full_name(),
                    'teacher_email': sesion.teacher.user.institutional_email,
                    'login_time': sesion.login_time,
                    'ip_address': sesion.ip_address,
                    'access_type': sesion.get_access_type_display(),
                    'duration_minutes': int(duracion.total_seconds() / 60)
                })
            
            return resultados
            
        except Exception as e:
            self.logger.error(f"Error obteniendo sesiones activas: {str(e)}")
            return []