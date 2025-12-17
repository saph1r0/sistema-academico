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
    Enrollment, AcademicPeriod, Horario, Aula , Course
)
from django.db.utils import ProgrammingError, OperationalError


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
        # No consultes la BD aquí
        pass

    def _obtener_periodo_activo(self):
        # Aquí sí haces la query real
        return AcademicPeriod.objects.filter(is_active=True).first()

    @property
    def periodo_activo(self):
        """
        Cada vez que alguien haga servicio_horario.periodo_activo
        se intentará leer de la BD. Si la BD no está lista (migrate),
        devolvemos None en vez de explotar.
        """
        try:
            return self._obtener_periodo_activo()
        except (ProgrammingError, OperationalError):
            # Durante migrate u operaciones donde aún no existe la tabla
            return None
    
    def obtener_cursos_con_laboratorio(self):
        """
        Obtiene la lista de cursos que tienen al menos un grupo de laboratorio asociado
        (Se requiere esta lógica para la vista de Secretaría)
        """
        # Encuentra IDs de cursos que tienen CourseGroups que a su vez tienen Laboratorios
        course_ids_with_labs = Course.objects.filter(
            coursegroup__laboratory__isnull=False
        ).values_list('id', flat=True).distinct()
        
        # Retorna los objetos Course (o los datos necesarios para la UI)
        return Course.objects.filter(id__in=course_ids_with_labs).order_by('name')

    def obtener_laboratorios_disponibles(self, student_id):
        from repositorio.postgres_repository.models import (
            Enrollment,
            Laboratory,
            LaboratoryEnrollment,
            Horario
        )

        try:
            # 1️⃣ Estudiante
            enrollment_qs = Enrollment.objects.filter(
                student_id=student_id,
                status='active'
            ).select_related(
                'course_group__course'
            )

            if not enrollment_qs.exists():
                return {
                    'success': True,
                    'laboratorios': [],
                    'total_disponibles': 0,
                    'en_periodo_matricula': self._verificar_periodo_matricula(),
                }

            # 2️⃣ CURSOS donde el estudiante está matriculado (A/B/C/D no importa)
            courses_ids = enrollment_qs.values_list(
                'course_group__course_id',
                flat=True
            )

            # 3️⃣ TODOS los LABs de esos cursos
            laboratories = Laboratory.objects.filter(
                course_group__course_id__in=courses_ids,  
                capacity__isnull=False,
                is_active=True
            ).select_related(
                'course_group__course',
                'teacher__user'
            )


            resultados = []

            for lab in laboratories:
                # 4️⃣ Matrículas actuales
                matriculados = LaboratoryEnrollment.objects.filter(
                    laboratory=lab,
                    status='active'
                ).count()

                cupos_disponibles = lab.capacity - matriculados
                tiene_cupos = cupos_disponibles > 0

                # 5️⃣ Ya matriculado en este LAB
                ya_matriculado = LaboratoryEnrollment.objects.filter(
                    laboratory=lab,
                    student_id=student_id,
                    status='active'
                ).exists()

                # 6️⃣ Horarios
                horarios_qs = Horario.objects.filter(
                    laboratory=lab
                ).select_related('aula')

                horarios = []
                for h in horarios_qs:
                    horarios.append({
                        'dia': h.dia_semana.capitalize(),
                        'hora_inicio': h.hora_inicio.strftime('%H:%M'),
                        'hora_fin': h.hora_fin.strftime('%H:%M'),
                    })

                # 7️⃣ Conflictos
                horario_principal = horarios_qs.first()
                tiene_conflicto, mensaje_conflicto = self._verificar_conflicto_horario(
                    student_id,
                    horario_principal
                ) if horario_principal else (False, '')

                resultados.append({
                    'id': lab.id,
                    'codigo': lab.lab_code,
                    'curso_nombre': lab.course_group.course.name,
                    'curso_codigo': lab.course_group.course.code,
                    'grupo': lab.course_group.group_code,
                    'profesor_nombre': lab.teacher.user.get_full_name() if lab.teacher else 'Por asignar',
                    'aula': lab.lab_room or 'Por asignar',
                    'horarios': horarios,
                    'capacidad': lab.capacity,
                    'matriculados': matriculados,
                    'cupos_disponibles': cupos_disponibles,
                    'tiene_cupos': tiene_cupos,
                    'porcentaje_ocupacion': int((matriculados / lab.capacity) * 100) if lab.capacity else 0,
                    'ya_matriculado': ya_matriculado,
                    'tiene_conflicto': tiene_conflicto,
                    'mensaje_conflicto': mensaje_conflicto,
                    'puede_matricularse': (
                        not ya_matriculado and
                        tiene_cupos and
                        not tiene_conflicto and
                        self._verificar_periodo_matricula()
                    )
                })

            return {
                'success': True,
                'laboratorios': resultados,
                'total_disponibles': len(resultados),
                'en_periodo_matricula': self._verificar_periodo_matricula(),
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
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
                dia_semana__iexact=lab_dia,
                laboratory__isnull=True   # 👈 SOLO teoría, no laboratorios

            )
            
            for h in horarios_curso:
                h_inicio = parse_time(h.hora_inicio)
                h_fin = parse_time(h.hora_fin)
                
                if intervals_conflict(lab_inicio, lab_fin, h_inicio, h_fin):
                    return True, (
                        f"Conflicto con {enrollment.course_group.course.name} "
                        f"({h_inicio.strftime('%H:%M')}-{h_fin.strftime('%H:%M')})"
                    )
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
            course_group__course=laboratory.course_group.course, 
            academic_period=self.periodo_activo,
            status='active'
        ).first()

        
        if not enrollment:
            return False, "No estás matriculado en este curso"
        
        # 3. Verificar si ya está matriculado en algún lab del mismo curso
        existing = LaboratoryEnrollment.objects.filter(
            student=student,
            laboratory__course_group__course=laboratory.course_group.course,
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
        enrollment.delete()
        #enrollment.status = 'withdrawn'
        #enrollment.save()
        
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