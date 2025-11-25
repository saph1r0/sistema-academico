"""
Servicio para obtener datos del estudiante desde la base de datos
Integrado con el sistema de progreso real basado en asistencia docente
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from repositorio.postgres_repository.models import (
    Student, Enrollment, Course, CourseGroup, AcademicPeriod, 
    CourseTopicContent, TeacherAttendance
)

logger = logging.getLogger(__name__)

@dataclass
class CursoEstudiante:
    """Datos básicos de un curso matriculado por el estudiante"""
    id: int
    nombre: str
    codigo: str
    grupo: str
    periodo_academico: str
    estado: str
    progreso: float = 0.0  # Por ahora siempre 0, se implementará después

class ServicioEstudianteData:
    """
    Servicio para obtener información académica del estudiante
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def obtener_cursos_estudiante(self, student_id: int) -> List[CursoEstudiante]:
        """
        Obtiene la lista de cursos en los que está matriculado el estudiante con progreso real
        
        Args:
            student_id: ID del estudiante
            
        Returns:
            Lista de cursos matriculados con progreso real
        """
        try:
            self.logger.info(f"Obteniendo cursos para estudiante ID: {student_id}")
            
            # Obtener inscripciones activas del estudiante
            inscripciones = Enrollment.objects.filter(
                student_id=student_id,
                status='active'
            ).select_related(
                'course_group__course',
                'course_group__teacher__user',
                'academic_period'
            )
            
            cursos = []
            for inscripcion in inscripciones:
                # Obtener progreso real del CourseGroup
                progreso_real = inscripcion.course_group.course_progress_percentage
                
                curso_data = CursoEstudiante(
                    id=inscripcion.course_group.course.id,
                    nombre=inscripcion.course_group.course.name,
                    codigo=inscripcion.course_group.course.code,
                    grupo=inscripcion.course_group.group_code,
                    periodo_academico=inscripcion.academic_period.name,
                    estado=inscripcion.status,
                    progreso=round(progreso_real, 2)  # Usar progreso real del sistema
                )
                cursos.append(curso_data)
            
            self.logger.info(f"Encontrados {len(cursos)} cursos para el estudiante con progreso real")
            return cursos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo cursos del estudiante {student_id}: {str(e)}")
            return []
    
    def obtener_estudiante_por_usuario(self, user_id: int) -> Optional[Student]:
        """
        Obtiene el registro de estudiante asociado a un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Objeto Student o None si no existe
        """
        try:
            return Student.objects.get(user_id=user_id)
        except ObjectDoesNotExist:
            self.logger.warning(f"No se encontró registro de estudiante para usuario {user_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error obteniendo estudiante para usuario {user_id}: {str(e)}")
            return None
    
    def obtener_detalle_curso(self, course_id: int, student_id: int) -> Dict:
        """
        Obtiene el detalle de un curso específico para un estudiante con progreso real
        
        Args:
            course_id: ID del curso
            student_id: ID del estudiante
            
        Returns:
            Diccionario con detalles del curso incluyendo progreso real
        """
        try:
            # Verificar que el estudiante esté inscrito en el curso
            inscripcion = Enrollment.objects.filter(
                student_id=student_id,
                course_group__course_id=course_id,
                status='active'
            ).select_related(
                'course_group__course',
                'course_group__teacher__user'
            ).first()
            
            if not inscripcion:
                self.logger.warning(f"Estudiante {student_id} no está inscrito en curso {course_id}")
                return {}
            
            curso = inscripcion.course_group.course
            course_group = inscripcion.course_group
            
            # Obtener progreso real del curso basado en asistencia docente
            progreso_real = course_group.course_progress_percentage
            
            # Obtener temas reales del curso
            temas_reales = CourseTopicContent.objects.filter(
                course_group=course_group
            ).order_by('topic_order')
            
            # Si no hay temas reales, usar temas de ejemplo
            if temas_reales.exists():
                temas_lista = []
                for tema in temas_reales:
                    temas_lista.append({
                        "id": str(tema.id),
                        "nombre": tema.topic_title,
                        "descripcion": tema.topic_description,
                        "orden": tema.topic_order,
                        "porcentaje": tema.percentage_weight,
                        "completado": tema.is_completed,
                        "fecha_completado": tema.completion_date.isoformat() if tema.completion_date else None
                    })
                
                total_temas = len(temas_lista)
                temas_completados = sum(1 for tema in temas_lista if tema["completado"])
            else:
                # Usar temas de ejemplo si no hay temas reales
                temas_lista = [
                    {"nombre": "Introducción al curso", "completado": True, "id": "ejemplo_1"},
                    {"nombre": "Conceptos básicos", "completado": True, "id": "ejemplo_2"},
                    {"nombre": "Tema intermedio 1", "completado": False, "id": "ejemplo_3"},
                    {"nombre": "Tema intermedio 2", "completado": False, "id": "ejemplo_4"},
                    {"nombre": "Tema avanzado 1", "completado": False, "id": "ejemplo_5"},
                    {"nombre": "Tema avanzado 2", "completado": False, "id": "ejemplo_6"},
                    {"nombre": "Proyecto final", "completado": False, "id": "ejemplo_7"},
                ]
                
                # Calcular progreso básico para temas de ejemplo
                total_temas = len(temas_lista)
                temas_completados = int((progreso_real / 100.0) * total_temas)
                
                # Actualizar estado de completado en temas de ejemplo
                for i, tema in enumerate(temas_lista):
                    tema["completado"] = i < temas_completados
            
            # Obtener información del profesor
            profesor_info = None
            if course_group.teacher:
                profesor_info = {
                    'nombre': course_group.teacher.user.get_full_name(),
                    'codigo': course_group.teacher.teacher_code
                }
            
            # Obtener estadísticas de asistencia del profesor
            clases_asistidas = course_group.classes_attended_by_teacher
            total_clases_programadas = course_group.total_planned_classes
            
            detalle = {
                'id': curso.id,
                'nombre': curso.name,
                'codigo': curso.code,
                'grupo': course_group.group_code,
                'creditos': curso.credits,
                'progreso': round(progreso_real, 2),
                'temas': temas_lista,
                'total_temas': total_temas,
                'temas_completados': temas_completados,
                'profesor': profesor_info,
                'estadisticas_asistencia': {
                    'clases_asistidas_profesor': clases_asistidas,
                    'total_clases_programadas': total_clases_programadas,
                    'porcentaje_asistencia_profesor': round((clases_asistidas / total_clases_programadas * 100), 2) if total_clases_programadas > 0 else 0
                },
                'es_progreso_real': temas_reales.exists(),
                'mensaje_progreso': self._generar_mensaje_progreso(progreso_real, clases_asistidas, total_clases_programadas)
            }
            
            self.logger.info(f"Detalle del curso obtenido: {curso.name} - Progreso: {progreso_real}% - Temas: {temas_completados}/{total_temas}")
            
            return detalle
            
        except Exception as e:
            self.logger.error(f"Error obteniendo detalle del curso {course_id} para estudiante {student_id}: {str(e)}")
            return {}
    
    def obtener_estadisticas_estudiante(self, student_id: int) -> Dict:
        """
        Obtiene estadísticas básicas del estudiante con progreso real
        
        Args:
            student_id: ID del estudiante
            
        Returns:
            Diccionario con estadísticas basadas en datos reales
        """
        try:
            # Obtener inscripciones activas del estudiante
            inscripciones = Enrollment.objects.filter(
                student_id=student_id,
                status='active'
            ).select_related('course_group')
            
            total_cursos = inscripciones.count()
            
            if total_cursos > 0:
                # Calcular progreso promedio real basado en los CourseGroups
                progreso_total = 0
                asistencia_total = 0
                
                for inscripcion in inscripciones:
                    course_group = inscripcion.course_group
                    progreso_total += course_group.course_progress_percentage
                    
                    # Calcular asistencia del profesor como proxy de la actividad del curso
                    if course_group.total_planned_classes > 0:
                        asistencia_profesor = (course_group.classes_attended_by_teacher / course_group.total_planned_classes) * 100
                        asistencia_total += asistencia_profesor
                
                progreso_promedio = progreso_total / total_cursos
                asistencia_promedio = asistencia_total / total_cursos
            else:
                progreso_promedio = 0.0
                asistencia_promedio = 0.0
            
            # Contar laboratorios (por implementar completamente)
            total_laboratorios = 0  # Por ahora 0, se implementará después
            
            estadisticas = {
                'total_cursos': total_cursos,
                'asistencia_promedio': round(asistencia_promedio, 2),
                'progreso_promedio': round(progreso_promedio, 2),
                'total_laboratorios': total_laboratorios
            }
            
            self.logger.info(f"Estadísticas calculadas para estudiante {student_id}: {estadisticas}")
            
            return estadisticas
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas del estudiante {student_id}: {str(e)}")
            return {
                'total_cursos': 0,
                'asistencia_promedio': 0.0,
                'progreso_promedio': 0.0,
                'total_laboratorios': 0
            }
    
    def _generar_mensaje_progreso(self, progreso: float, clases_asistidas: int, total_clases: int) -> str:
        """
        Genera un mensaje descriptivo sobre el progreso del curso
        
        Args:
            progreso: Porcentaje de progreso actual
            clases_asistidas: Número de clases asistidas por el profesor
            total_clases: Total de clases programadas
            
        Returns:
            str: Mensaje descriptivo del progreso
        """
        try:
            if total_clases == 0:
                return "No hay información de clases programadas"
            
            porcentaje_asistencia = (clases_asistidas / total_clases) * 100
            
            if progreso >= 80:
                return f"Curso muy avanzado ({progreso:.1f}%). El profesor ha asistido a {clases_asistidas} de {total_clases} clases."
            elif progreso >= 60:
                return f"Curso bien avanzado ({progreso:.1f}%). El profesor ha asistido a {clases_asistidas} de {total_clases} clases."
            elif progreso >= 40:
                return f"Curso en progreso normal ({progreso:.1f}%). El profesor ha asistido a {clases_asistidas} de {total_clases} clases."
            elif progreso >= 20:
                return f"Curso en etapa inicial ({progreso:.1f}%). El profesor ha asistido a {clases_asistidas} de {total_clases} clases."
            else:
                return f"Curso recién iniciado ({progreso:.1f}%). El profesor ha asistido a {clases_asistidas} de {total_clases} clases."
                
        except Exception:
            return f"Progreso del curso: {progreso:.1f}%"