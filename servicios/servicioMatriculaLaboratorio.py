#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Servicio de Matrícula de Laboratorios
Arquitectura DDD - Capa de Aplicación
Maneja matrícula, desmatrícula y validaciones de laboratorios
"""

from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q

from repositorio.postgres_repository.models import (
    Student, Laboratory, LaboratoryEnrollment, CourseGroup,
    Enrollment, AcademicPeriod, Horario, Aula
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


class ServicioMatriculaLaboratorio:
    """
    Servicio para gestión de matrícula en laboratorios
    Implementa reglas de negocio y validaciones
    """
    
    # Días de plazo para cambios (3 días desde la matrícula)
    DIAS_CAMBIO = 3
    
    def __init__(self):
        self.periodo_activo = self._obtener_periodo_activo()
    
    def _obtener_periodo_activo(self) -> Optional[AcademicPeriod]:
        """Obtiene el período académico activo"""
        return AcademicPeriod.objects.filter(is_active=True).first()
    
    def obtener_laboratorios_disponibles(self, student_id: int) -> Dict:
        """
        Obtiene todos los laboratorios disponibles para el estudiante
        Incluye validaciones de conflictos y cupos
        """
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return {
                'success': False,
                'error': 'Estudiante no encontrado',
                'laboratorios': []
            }
        
        if not self.periodo_activo:
            return {
                'success': False,
                'error': 'No hay período académico activo',
                'laboratorios': []
            }
        
        # Verificar si está en período de matrícula
        en_periodo = self._verificar_periodo_matricula()
        
        # Obtener cursos matriculados del estudiante
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_period=self.periodo_activo,
            status='active'
        ).select_related('course_group__course')
        
        laboratorios_disponibles = []
        
        for enrollment in enrollments:
            course_group = enrollment.course_group
            
            # Buscar laboratorios para este grupo de curso
            laboratories = Laboratory.objects.filter(
                course_group=course_group,
                is_active=True
            ).select_related('teacher__user').prefetch_related(
                'horarios_set__aula'
            )
            
            if not laboratories.exists():
                continue
            
            # Verificar si ya está matriculado en algún laboratorio de este curso
            matricula_actual = LaboratoryEnrollment.objects.filter(
                student=student,
                laboratory__course_group=course_group,
                status='active'
            ).select_related('laboratory').first()
            
            for lab in laboratories:
                # Obtener horarios del laboratorio
                lab_horarios = Horario.objects.filter(
                    laboratory=lab
                ).select_related('aula')
                
                if not lab_horarios.exists():
                    continue
                
                # Calcular disponibilidad
                cupos_data = self._calcular_cupos(lab)
                
                # Verificar conflictos de horario
                conflicto, mensaje_conflicto = self._verificar_conflicto_horario(
                    student, lab_horarios.first() if lab_horarios else None
                )
                
                # Construir información del laboratorio
                horarios_info = []
                for h in lab_horarios:
                    horarios_info.append({
                        'dia': h.dia_semana.capitalize(),
                        'hora_inicio': parse_time(h.hora_inicio).strftime('%H:%M'),
                        'hora_fin': parse_time(h.hora_fin).strftime('%H:%M'),
                        'aula': h.aula.codigo if h.aula else lab.lab_room or 'Por asignar'
                    })
                
                # Determinar estado de matrícula
                ya_matriculado = matricula_actual and matricula_actual.laboratory.id == lab.id
                puede_matricularse = (
                    en_periodo and
                    not conflicto and
                    cupos_data['tiene_cupos'] and
                    not matricula_actual
                )
                
                # Información de matrícula actual si existe
                info_matricula = None
                puede_desmatricularse = False
                if matricula_actual and matricula_actual.laboratory.id == lab.id:
                    puede_desmatricularse = self._puede_desmatricularse(matricula_actual)
                    info_matricula = {
                        'fecha_matricula': matricula_actual.enrollment_date.strftime('%d/%m/%Y'),
                        'puede_cambiar': puede_desmatricularse,
                        'dias_restantes': self._calcular_dias_restantes(matricula_actual)
                    }
                
                laboratorios_disponibles.append({
                    'id': str(lab.id),
                    'codigo': lab.lab_code,
                    'curso_id': str(course_group.id),
                    'curso_nombre': course_group.course.name,
                    'curso_codigo': course_group.course.code,
                    'grupo': course_group.group_code,
                    'profesor_nombre': lab.teacher.user.get_full_name() if lab.teacher else 'Por asignar',
                    'horarios': horarios_info,
                    'aula': horarios_info[0]['aula'] if horarios_info else 'Por asignar',
                    'capacidad': lab.capacity,
                    'matriculados': cupos_data['matriculados'],
                    'cupos_disponibles': cupos_data['disponibles'],
                    'porcentaje_ocupacion': cupos_data['porcentaje'],
                    'tiene_cupos': cupos_data['tiene_cupos'],
                    'tiene_conflicto': conflicto,
                    'mensaje_conflicto': mensaje_conflicto,
                    'ya_matriculado': ya_matriculado,
                    'puede_matricularse': puede_matricularse,
                    'puede_desmatricularse': puede_desmatricularse,
                    'info_matricula': info_matricula,
                    'en_periodo_matricula': en_periodo
                })
        
        return {
            'success': True,
            'laboratorios': laboratorios_disponibles,
            'en_periodo_matricula': en_periodo,
            'total_disponibles': len(laboratorios_disponibles)
        }
    
    def _verificar_periodo_matricula(self) -> bool:
        """Verifica si estamos en período de matrícula de laboratorios"""
        if not self.periodo_activo:
            return False
        
        now = timezone.now().date()
        return (
            self.periodo_activo.laboratory_enrollment_start <= now <= self.periodo_activo.laboratory_enrollment_end
        )
    
    def _calcular_cupos(self, laboratory: Laboratory) -> Dict:
        """Calcula cupos disponibles y porcentaje de ocupación"""
        matriculados = LaboratoryEnrollment.objects.filter(
            laboratory=laboratory,
            status='active'
        ).count()
        
        disponibles = laboratory.capacity - matriculados
        porcentaje = int((matriculados / laboratory.capacity) * 100) if laboratory.capacity > 0 else 100
        
        return {
            'matriculados': matriculados,
            'disponibles': disponibles,
            'porcentaje': porcentaje,
            'tiene_cupos': disponibles > 0
        }
    
    def _verificar_conflicto_horario(
        self, 
        student: Student, 
        horario_lab: Optional[Horario]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si hay conflicto con el horario del estudiante
        Retorna: (tiene_conflicto, mensaje)
        """
        if not horario_lab:
            return False, None
        
        lab_dia = horario_lab.dia_semana.lower()
        lab_inicio = parse_time(horario_lab.hora_inicio)
        lab_fin = parse_time(horario_lab.hora_fin)
        
        # 1. Verificar conflictos con clases regulares
        enrollments = Enrollment.objects.filter(
            student=student,
            academic_period=self.periodo_activo,
            status='active'
        )
        
        for enrollment in enrollments:
            horarios_curso = Horario.objects.filter(
                course_group=enrollment.course_group,
                dia_semana__iexact=lab_dia
            )
            
            for h in horarios_curso:
                h_inicio = parse_time(h.hora_inicio)
                h_fin = parse_time(h.hora_fin)
                
                if intervals_conflict(lab_inicio, lab_fin, h_inicio, h_fin):
                    return True, f"Conflicto con {enrollment.course_group.course.name} ({h_inicio.strftime('%H:%M')}-{h_fin.strftime('%H:%M')})"
        
        # 2. Verificar conflictos con otros laboratorios
        lab_enrollments = LaboratoryEnrollment.objects.filter(
            student=student,
            status='active'
        ).exclude(laboratory=horario_lab.laboratory if hasattr(horario_lab, 'laboratory') else None)
        
        for lab_enroll in lab_enrollments:
            horarios_lab_actual = Horario.objects.filter(
                laboratory=lab_enroll.laboratory,
                dia_semana__iexact=lab_dia
            )
            
            for h in horarios_lab_actual:
                h_inicio = parse_time(h.hora_inicio)
                h_fin = parse_time(h.hora_fin)
                
                if intervals_conflict(lab_inicio, lab_fin, h_inicio, h_fin):
                    return True, f"Conflicto con laboratorio {lab_enroll.laboratory.lab_code}"
        
        return False, None
    
    def _puede_desmatricularse(self, enrollment: LaboratoryEnrollment) -> bool:
        """Verifica si el estudiante puede desmatricularse (dentro de 3 días)"""
        dias_transcurridos = (timezone.now().date() - enrollment.enrollment_date).days
        return dias_transcurridos <= self.DIAS_CAMBIO
    
    def _calcular_dias_restantes(self, enrollment: LaboratoryEnrollment) -> int:
        """Calcula días restantes para poder cambiar"""
        dias_transcurridos = (timezone.now().date() - enrollment.enrollment_date).days
        dias_restantes = self.DIAS_CAMBIO - dias_transcurridos
        return max(0, dias_restantes)
    
    @transaction.atomic
    def matricular_laboratorio(
        self, 
        student_id: int, 
        laboratory_id: str
    ) -> Tuple[bool, str]:
        """
        Matricula un estudiante en un laboratorio
        Retorna: (éxito, mensaje)
        """
        try:
            student = Student.objects.select_for_update().get(id=student_id)
            laboratory = Laboratory.objects.select_for_update().get(id=laboratory_id, is_active=True)
        except (Student.DoesNotExist, Laboratory.DoesNotExist) as e:
            return False, "Estudiante o laboratorio no encontrado"
        
        # 1. Verificar período de matrícula
        if not self._verificar_periodo_matricula():
            return False, "Fuera del período de matrícula de laboratorios"
        
        # 2. Verificar que esté matriculado en el curso
        enrollment = Enrollment.objects.filter(
            student=student,
            course_group=laboratory.course_group,
            academic_period=self.periodo_activo,
            status='active'
        ).first()
        
        if not enrollment:
            return False, "No estás matriculado en este curso"
        
        # 3. Verificar si ya está matriculado en algún lab del mismo curso
        existing = LaboratoryEnrollment.objects.filter(
            student=student,
            laboratory__course_group=laboratory.course_group,
            status='active'
        ).first()
        
        if existing:
            return False, f"Ya estás matriculado en {existing.laboratory.lab_code}"
        
        # 4. Verificar cupos
        cupos = self._calcular_cupos(laboratory)
        if not cupos['tiene_cupos']:
            return False, "No hay cupos disponibles"
        
        # 5. Verificar conflictos de horario
        horario_lab = Horario.objects.filter(laboratory=laboratory).first()
        tiene_conflicto, mensaje = self._verificar_conflicto_horario(student, horario_lab)
        
        if tiene_conflicto:
            return False, f"Conflicto de horario: {mensaje}"
        
        # 6. Crear matrícula
        LaboratoryEnrollment.objects.create(
            student=student,
            laboratory=laboratory,
            enrollment_date=timezone.now().date(),
            status='active'
        )
        
        # 7. Actualizar contador
        laboratory.enrolled_students = cupos['matriculados'] + 1
        laboratory.save()
        
        return True, f"✅ Matriculado exitosamente en {laboratory.lab_code}"
    
    @transaction.atomic
    def desmatricular_laboratorio(
        self, 
        student_id: int, 
        laboratory_id: str
    ) -> Tuple[bool, str]:
        """
        Desmatricula un estudiante de un laboratorio
        Retorna: (éxito, mensaje)
        """
        try:
            student = Student.objects.get(id=student_id)
            enrollment = LaboratoryEnrollment.objects.select_for_update().get(
                student=student,
                laboratory_id=laboratory_id,
                status='active'
            )
        except (Student.DoesNotExist, LaboratoryEnrollment.DoesNotExist):
            return False, "Matrícula no encontrada"
        
        # 1. Verificar plazo de 3 días
        if not self._puede_desmatricularse(enrollment):
            dias_transcurridos = (timezone.now().date() - enrollment.enrollment_date).days
            return False, f"Ya pasaron más de {self.DIAS_CAMBIO} días desde la matrícula ({dias_transcurridos} días). No puedes desmatricularte."
        
        # 2. Retirar matrícula
        laboratory = enrollment.laboratory
        enrollment.status = 'withdrawn'
        enrollment.save()
        
        # 3. Actualizar contador
        active_count = LaboratoryEnrollment.objects.filter(
            laboratory=laboratory,
            status='active'
        ).count()
        
        laboratory.enrolled_students = active_count
        laboratory.save()
        
        dias_restantes = self._calcular_dias_restantes(enrollment)
        return True, f"✅ Desmatriculado de {laboratory.lab_code}"


# Instancia global del servicio
servicio_matricula_laboratorio = ServicioMatriculaLaboratorio()