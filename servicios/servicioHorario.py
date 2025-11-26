#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Servicio para gestión de horarios académicos con laboratorios
Arquitectura DDD - Capa de Aplicación
"""

from datetime import datetime, time
from typing import List, Dict, Optional, Tuple
from django.db.models import Q, Prefetch
from repositorio.postgres_repository.models import (
    Student, Teacher, Horario, Laboratory, LaboratoryEnrollment,
    Enrollment, CourseGroup, AcademicPeriod, Aula
)


def parse_time(value) -> time:
    """Convierte diversos formatos de tiempo a objeto time"""
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    try:
        return datetime.strptime(str(value), "%H:%M:%S").time()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(value), "%H:%M").time()
        except (ValueError, TypeError):
            return time(0, 0)


def intervals_conflict(start1: time, end1: time, start2: time, end2: time) -> bool:
    """Detecta si dos intervalos de tiempo se superponen"""
    start1_mins = start1.hour * 60 + start1.minute
    end1_mins = end1.hour * 60 + end1.minute
    start2_mins = start2.hour * 60 + start2.minute
    end2_mins = end2.hour * 60 + end2.minute
    
    return (start1_mins < end2_mins) and (start2_mins < end1_mins)


class ServicioHorario:
    """Servicio centralizado para gestión de horarios académicos"""
    
    DIAS_SEMANA = {
        'lunes': 1,
        'martes': 2,
        'miercoles': 3,
        'miércoles': 3,
        'jueves': 4,
        'viernes': 5,
        'sabado': 6,
        'sábado': 6,
        'domingo': 0
    }
    
    COLORES_CURSOS = [
        '#3b82f6',  # Azul
        '#10b981',  # Verde
        '#f59e0b',  # Naranja
        '#8b5cf6',  # Púrpura
        '#ec4899',  # Rosa
        '#14b8a6',  # Teal
    ]
    
    def __init__(self):
        self.periodo_activo = self._obtener_periodo_activo()
    
    def _obtener_periodo_activo(self) -> Optional[AcademicPeriod]:
        """Obtiene el período académico activo"""
        return AcademicPeriod.objects.filter(is_active=True).first()
    
    def obtener_horario_estudiante(self, student_id: int) -> Dict:
        """
        Obtiene el horario completo del estudiante (clases + laboratorios)
        Formato compatible con FullCalendar
        """
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return {
                'success': False, 
                'error': 'Estudiante no encontrado', 
                'events': []
            }
        
        if not self.periodo_activo:
            return {
                'success': False, 
                'error': 'No hay período académico activo', 
                'events': []
            }
        
        events = []
        color_index = 0
        
        # 1. OBTENER CLASES REGULARES
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_period=self.periodo_activo,
            status='active'
        ).select_related(
            'course_group__course',
            'course_group__teacher__user'
        ).prefetch_related(
            Prefetch(
                'course_group__horarios',
                queryset=Horario.objects.select_related('aula')
            )
        )
        
        for enrollment in enrollments:
            course_group = enrollment.course_group
            color = self.COLORES_CURSOS[color_index % len(self.COLORES_CURSOS)]
            
            # Obtener horarios del curso
            for horario in course_group.horarios.all():
                events.append({
                    'id': f'clase_{horario.id}',
                    'title': course_group.course.name,
                    'daysOfWeek': [self.DIAS_SEMANA.get(horario.dia_semana.lower(), 1)],
                    'startTime': parse_time(horario.hora_inicio).strftime('%H:%M'),
                    'endTime': parse_time(horario.hora_fin).strftime('%H:%M'),
                    'color': color,
                    'extendedProps': {
                        'type': 'clase',
                        'codigo': course_group.course.code,
                        'grupo': course_group.group_code,
                        'profesor': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar',
                        'aula': horario.aula.codigo if horario.aula else 'Por asignar',
                        'creditos': course_group.course.credits,
                        'dia': horario.dia_semana.capitalize()
                    }
                })
            
            color_index += 1
        
        # 2. OBTENER LABORATORIOS MATRICULADOS
        lab_enrollments = LaboratoryEnrollment.objects.filter(
            student=student,
            status='active'
        ).select_related(
            'laboratory__course_group__course',
            'laboratory__course_group__teacher__user',
            'laboratory__teacher__user'
        ).prefetch_related(
            Prefetch(
                'laboratory__horarios_set',
                queryset=Horario.objects.select_related('aula'),
                to_attr='lab_horarios'
            )
        )
        
        for lab_enrollment in lab_enrollments:
            laboratory = lab_enrollment.laboratory
            
            # Buscar horarios asociados al laboratorio
            lab_horarios = Horario.objects.filter(
                laboratory=laboratory
            ).select_related('aula')
            
            for horario in lab_horarios:
                events.append({
                    'id': f'lab_{horario.id}',
                    'title': f'{laboratory.course_group.course.name} - LAB',
                    'daysOfWeek': [self.DIAS_SEMANA.get(horario.dia_semana.lower(), 1)],
                    'startTime': parse_time(horario.hora_inicio).strftime('%H:%M'),
                    'endTime': parse_time(horario.hora_fin).strftime('%H:%M'),
                    'color': '#dc2626',  # Rojo para laboratorios
                    'extendedProps': {
                        'type': 'laboratorio',
                        'codigo': laboratory.lab_code,
                        'curso': laboratory.course_group.course.name,
                        'profesor': laboratory.teacher.user.get_full_name() if laboratory.teacher else 'Por asignar',
                        'aula': horario.aula.codigo if horario.aula else laboratory.lab_room,
                        'capacidad': laboratory.capacity,
                        'dia': horario.dia_semana.capitalize()
                    }
                })
        
        return {
            'success': True,
            'events': events,
            'student_name': student.user.get_full_name(),
            'student_code': student.student_code,
            'total_courses': enrollments.count(),
            'total_labs': lab_enrollments.count()
        }
        
    def obtener_horario_profesor(self, teacher_id: int) -> Dict:
        """
        Obtiene el horario completo del profesor (todas sus secciones + laboratorios)
        en el período académico activo.

        Formato compatible con FullCalendar (igual que en estudiante).
        """
        try:
            teacher = Teacher.objects.select_related('user').get(id=teacher_id)
        except Teacher.DoesNotExist:
            return {
                'success': False,
                'error': 'Profesor no encontrado',
                'events': []
            }

        if not self.periodo_activo:
            return {
                'success': False,
                'error': 'No hay período académico activo',
                'events': []
            }

        events: List[Dict] = []
        color_index = 0

        # ==========================================================
        # 1) OBTENER TODOS LOS COURSE_GROUP DONDE PARTICIPA EL PROFESOR
        #    - Como docente principal del curso (course_group.teacher)
        #    - Como docente de un laboratorio de ese curso (laboratory.teacher)
        # ==========================================================

        # IDs de CourseGroup donde el profesor dicta laboratorio
        lab_coursegroup_ids = (
            Laboratory.objects
            .filter(
                teacher=teacher,
                course_group__academic_period=self.periodo_activo
            )
            .exclude(course_group__isnull=True)
            .values_list('course_group_id', flat=True)
            .distinct()
        )

        course_groups = (
            CourseGroup.objects
            .filter(
                academic_period=self.periodo_activo
            )
            .filter(
                Q(teacher=teacher) | Q(id__in=lab_coursegroup_ids)
            )
            .select_related(
                'course',
                'teacher__user',
            )
            .prefetch_related(
                Prefetch(
                    'horarios',
                    queryset=Horario.objects.select_related('aula')
                )
            )
            .order_by('course__name', 'group_code')
            .distinct()
        )

        # ==========================================================
        # 2) GENERAR EVENTOS PARA CADA HORARIO DE CADA COURSE_GROUP
        # ==========================================================
        for course_group in course_groups:
            color = self.COLORES_CURSOS[color_index % len(self.COLORES_CURSOS)]

            for horario in course_group.horarios.all():
                events.append({
                    'id': f'clase_{horario.id}',
                    'title': course_group.course.name,
                    'daysOfWeek': [self.DIAS_SEMANA.get(horario.dia_semana.lower(), 1)],
                    'startTime': parse_time(horario.hora_inicio).strftime('%H:%M'),
                    'endTime': parse_time(horario.hora_fin).strftime('%H:%M'),
                    'color': color,
                    'extendedProps': {
                        'type': 'clase',
                        'codigo': course_group.course.code,
                        'grupo': course_group.group_code,
                        'profesor': course_group.teacher.user.get_full_name()
                                     if course_group.teacher else 'Sin asignar',
                        'aula': (
                            horario.aula.codigo
                            if hasattr(horario, 'aula') and horario.aula
                            else 'Por asignar'
                        ),
                        'creditos': getattr(course_group.course, 'credits', None),
                        'dia': horario.dia_semana.capitalize(),
                    }
                })

            color_index += 1

        # ==========================================================
        # 3) LABORATORIOS DONDE PARTICIPA EL PROFESOR
        #    (como responsable del lab o como docente del CourseGroup)
        # ==========================================================
        laboratories = (
            Laboratory.objects
            .filter(
                Q(teacher=teacher) | Q(course_group__teacher=teacher),
                course_group__academic_period=self.periodo_activo
            )
            .select_related(
                'course_group__course',
                'teacher__user',
            )
            .order_by('course_group__course__name', 'lab_code')
            .distinct()
        )

        for lab in laboratories:
            lab_horarios = (
                Horario.objects
                .filter(laboratory=lab)
                .select_related('aula')
            )

            for horario in lab_horarios:
                events.append({
                    'id': f'lab_{horario.id}',
                    'title': f'{lab.course_group.course.name} - LAB',
                    'daysOfWeek': [self.DIAS_SEMANA.get(horario.dia_semana.lower(), 1)],
                    'startTime': parse_time(horario.hora_inicio).strftime('%H:%M'),
                    'endTime': parse_time(horario.hora_fin).strftime('%H:%M'),
                    'color': '#dc2626',  # rojo laboratorios
                    'extendedProps': {
                        'type': 'laboratorio',
                        'codigo': lab.lab_code,
                        'curso': lab.course_group.course.name,
                        'grupo': lab.course_group.group_code,
                        'profesor': (
                            lab.teacher.user.get_full_name()
                            if lab.teacher
                            else teacher.user.get_full_name()
                        ),
                        'aula': (
                            horario.aula.codigo
                            if hasattr(horario, 'aula') and horario.aula
                            else lab.lab_room
                        ),
                        'capacidad': lab.capacity,
                        'dia': horario.dia_semana.capitalize(),
                    }
                })

        # ==========================================================
        # 4) RESUMEN
        # ==========================================================
        return {
            'success': True,
            'teacher_name': teacher.user.get_full_name(),
            'events': events,
            'total_eventos': len(events),

            # Totales en español
            'total_cursos': course_groups.count(),
            'total_laboratorios': laboratories.count(),

            # Alias en inglés para que el JS actual funcione sin romper nada
            'total_courses': course_groups.count(),
            'total_labs': laboratories.count(),
        }


    
    def obtener_laboratorios_estudiante(self, student_id: int) -> Dict:
        """Obtiene solo los laboratorios matriculados del estudiante"""
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Estudiante no encontrado',
                'laboratories': []
            }
        
        lab_enrollments = LaboratoryEnrollment.objects.filter(
            student=student,
            status='active'
        ).select_related(
            'laboratory__course_group__course',
            'laboratory__teacher__user'
        )
        
        laboratories = []
        for lab_enrollment in lab_enrollments:
            lab = lab_enrollment.laboratory
            
            # Obtener horarios del laboratorio
            horarios = Horario.objects.filter(
                laboratory=lab
            ).select_related('aula')
            
            horarios_list = []
            for h in horarios:
                horarios_list.append({
                    'dia': h.dia_semana.capitalize(),
                    'hora_inicio': parse_time(h.hora_inicio).strftime('%H:%M'),
                    'hora_fin': parse_time(h.hora_fin).strftime('%H:%M'),
                    'aula': h.aula.codigo if h.aula else lab.lab_room
                })
            
            laboratories.append({
                'id': str(lab.id),
                'codigo': lab.lab_code,
                'curso': lab.course_group.course.name,
                'profesor': lab.teacher.user.get_full_name() if lab.teacher else 'Sin asignar',
                'capacidad': lab.capacity,
                'horarios': horarios_list,
                'fecha_matricula': lab_enrollment.enrollment_date.strftime('%d/%m/%Y')
            })
        
        return {
            'success': True,
            'laboratories': laboratories,
            'total': len(laboratories)
        }
    
    def verificar_conflicto_horario(
        self,
        student_id: int,
        nuevo_dia: str,
        nueva_hora_inicio: time,
        nueva_hora_fin: time,
        excluir_lab_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si hay conflicto de horario para un estudiante
        Retorna: (tiene_conflicto, mensaje_error)
        """
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return True, "Estudiante no encontrado"
        
        nuevo_dia_lower = nuevo_dia.lower()
        
        # 1. Verificar conflictos con clases regulares
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_period=self.periodo_activo,
            status='active'
        ).select_related('course_group__course')
        
        for enrollment in enrollments:
            horarios = Horario.objects.filter(
                course_group=enrollment.course_group,
                dia_semana__iexact=nuevo_dia_lower
            )
            
            for horario in horarios:
                hora_inicio = parse_time(horario.hora_inicio)
                hora_fin = parse_time(horario.hora_fin)
                
                if intervals_conflict(nueva_hora_inicio, nueva_hora_fin, hora_inicio, hora_fin):
                    return True, f"Conflicto con {enrollment.course_group.course.name} ({hora_inicio.strftime('%H:%M')}-{hora_fin.strftime('%H:%M')})"
        
        # 2. Verificar conflictos con otros laboratorios
        lab_enrollments = LaboratoryEnrollment.objects.filter(
            student=student,
            status='active'
        ).select_related('laboratory__course_group__course')
        
        if excluir_lab_id:
            lab_enrollments = lab_enrollments.exclude(laboratory_id=excluir_lab_id)
        
        for lab_enrollment in lab_enrollments:
            lab_horarios = Horario.objects.filter(
                laboratory=lab_enrollment.laboratory,
                dia_semana__iexact=nuevo_dia_lower
            )
            
            for horario in lab_horarios:
                hora_inicio = parse_time(horario.hora_inicio)
                hora_fin = parse_time(horario.hora_fin)
                
                if intervals_conflict(nueva_hora_inicio, nueva_hora_fin, hora_inicio, hora_fin):
                    return True, f"Conflicto con laboratorio {lab_enrollment.laboratory.lab_code} ({hora_inicio.strftime('%H:%M')}-{hora_fin.strftime('%H:%M')})"
        
        return False, None
    
    def verificar_conflictos(self, student_id: int, nuevo_horario: Dict) -> Dict:
        """
        Verifica conflictos para el endpoint de API
        nuevo_horario debe contener: dia, hora_inicio, hora_fin
        """
        try:
            dia = nuevo_horario.get('dia', '')
            hora_inicio_str = nuevo_horario.get('hora_inicio', '')
            hora_fin_str = nuevo_horario.get('hora_fin', '')
            
            if not all([dia, hora_inicio_str, hora_fin_str]):
                return {
                    'success': False,
                    'error': 'Datos incompletos'
                }
            
            hora_inicio = parse_time(hora_inicio_str)
            hora_fin = parse_time(hora_fin_str)
            
            tiene_conflicto, mensaje = self.verificar_conflicto_horario(
                student_id, dia, hora_inicio, hora_fin
            )
            
            return {
                'success': True,
                'tiene_conflicto': tiene_conflicto,
                'mensaje': mensaje
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_resumen_horario(self, student_id: int) -> Dict:
        """Obtiene un resumen estadístico del horario del estudiante"""
        horario_data = self.obtener_horario_estudiante(student_id)
        
        if not horario_data['success']:
            return horario_data
        
        events = horario_data['events']
        
        # Calcular horas totales semanales
        total_horas = 0
        dias_ocupados = set()
        aulas_usadas = set()
        
        for event in events:
            start_time = datetime.strptime(event['startTime'], '%H:%M').time()
            end_time = datetime.strptime(event['endTime'], '%H:%M').time()
            
            duracion = (end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute)
            total_horas += duracion / 60
            
            dias_ocupados.update(event['daysOfWeek'])
            
            if 'aula' in event['extendedProps']:
                aulas_usadas.add(event['extendedProps']['aula'])
        
        return {
            'success': True,
            'total_horas_semanales': round(total_horas, 1),
            'dias_ocupados': len(dias_ocupados),
            'total_eventos': len(events),
            'total_aulas': len(aulas_usadas),
            'total_cursos': horario_data['total_courses'],
            'total_laboratorios': horario_data['total_labs']
        }


# Instancia global del servicio
servicio_horario = ServicioHorario()