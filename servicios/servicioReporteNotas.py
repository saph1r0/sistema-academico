from django.db.models import Avg, Q
from repositorio.postgres_repository.models import PhaseGrade, Enrollment
import logging

logger = logging.getLogger(__name__)

class ServicioReporteNotas:
   

    def obtener_dashboard_admin(self, filtros=None):
     
        try:
            notas_qs = PhaseGrade.objects.all().select_related(
                'student__user', 
                'course_group__course'
            )
            
            total_registros = notas_qs.values('student').distinct().count()
            
            if total_registros == 0:
                return self._retornar_vacio()

            promedio_agg = notas_qs.aggregate(Avg('final_phase_grade'))['final_phase_grade__avg']
            promedio_global = float(promedio_agg) if promedio_agg else 0.0
            
           
            riesgo_qs = notas_qs.filter(
                Q(final_phase_grade__lt=10.5) | 
                (Q(final_phase_grade__isnull=True) & Q(partial_grade__lt=10.5))
            ).values(
                'student__student_code',      
                'student__user__first_name', 
                'student__user__last_name', 
                'course_group__course__name',
                'course_group__group_code',
                'final_phase_grade',
                'partial_grade'
            ).order_by('student__user__last_name')

            mapa_alumnos_riesgo = {}

            for item in riesgo_qs:
                cui = item['student__student_code']
                
                if cui not in mapa_alumnos_riesgo:
                    mapa_alumnos_riesgo[cui] = {
                        'nombre': f"{item['student__user__last_name']} {item['student__user__first_name']}",
                        'codigo': cui,
                        'cursos': [] 
                    }
                
                nota_val = item['final_phase_grade'] if item['final_phase_grade'] is not None else item['partial_grade']
                nota_float = float(nota_val) if nota_val else 0.0
                
                mapa_alumnos_riesgo[cui]['cursos'].append({
                    'nombre': f"{item['course_group__course__name']} ({item['course_group__group_code']})",
                    'nota': nota_float
                })

            estudiantes_riesgo = list(mapa_alumnos_riesgo.values())

            aprobados_count = notas_qs.filter(
                Q(final_phase_grade__gte=10.5) | 
                (Q(final_phase_grade__isnull=True) & Q(partial_grade__gte=10.5))
            ).count()
            
            total_filas_notas = notas_qs.count()
            
            tasa_aprobacion = 0.0
            if total_filas_notas > 0:
                tasa_aprobacion = (aprobados_count / total_filas_notas) * 100
                if tasa_aprobacion > 100: tasa_aprobacion = 100.0

            cursos_criticos_qs = notas_qs.filter(
                final_phase_grade__isnull=False
            ).values('course_group__course__name').annotate(
                promedio=Avg('final_phase_grade')
            ).order_by('promedio')[:5]

            cursos_criticos = []
            for curso in cursos_criticos_qs:
                cursos_criticos.append({
                    'course_group__course__name': curso['course_group__course__name'],
                    'promedio': float(round(curso['promedio'], 2))
                })

            return {
                'promedio_global': round(promedio_global, 2),
                'total_evaluados': total_registros, 
                'tasa_aprobacion': round(tasa_aprobacion, 1),
                'cantidad_riesgo': len(estudiantes_riesgo), 
                'estudiantes_riesgo': estudiantes_riesgo,
                'cursos_criticos': cursos_criticos
            }

        except Exception as e:
            logger.error(f"Error calculando dashboard de notas: {str(e)}")
            return self._retornar_vacio()

    def _retornar_vacio(self):
        
        return {
            'promedio_global': 0.0,
            'total_evaluados': 0,
            'tasa_aprobacion': 0.0,
            'cantidad_riesgo': 0,
            'estudiantes_riesgo': [],
            'cursos_criticos': []
        }

    def obtener_lista_alumnos_curso(self, curso_id):
       
        try:
            matriculas = Enrollment.objects.filter(
                course_group_id=curso_id, 
                status='active'
            ).select_related('student__user').order_by('student__user__last_name')
            
            lista = []
            for m in matriculas:
                lista.append({
                    'cui': m.student.student_code,
                    'nombre_completo': f"{m.student.user.last_name} {m.student.user.first_name}"
                })
            return lista
        except Exception as e:
            logger.error(f"Error obteniendo lista alumnos: {str(e)}")
            return []

    def buscar_notas_detalladas(self, curso_id=None, busqueda=None):
        try:
            notas_qs = PhaseGrade.objects.all().select_related(
                'student__user', 
                'course_group__course'
            ).order_by('student__user__last_name')

            if curso_id:
                notas_qs = notas_qs.filter(course_group_id=curso_id)

            if busqueda:
                notas_qs = notas_qs.filter(
                    Q(student__user__first_name__icontains=busqueda) |
                    Q(student__user__last_name__icontains=busqueda) |
                    Q(student__student_code__icontains=busqueda)
                )

            if not curso_id and not busqueda:
                return []

            resultados = []
            for registro in notas_qs[:50]: 
                nota_val = registro.final_phase_grade if registro.final_phase_grade is not None else registro.partial_grade
                nota_float = float(nota_val) if nota_val else 0.0
                
                estado = "APROBADO" if nota_float >= 10.5 else "DESAPROBADO"
                color_estado = "green" if nota_float >= 10.5 else "red"

                resultados.append({
                    'estudiante': f"{registro.student.user.last_name} {registro.student.user.first_name}",
                    'codigo': registro.student.student_code,
                    'curso': registro.course_group.course.name,
                    'grupo': registro.course_group.group_code,
                    'fase': registro.get_phase_display(), 
                    'nota': nota_float,
                    'estado': estado,
                    'color': color_estado
                })
            
            return resultados

        except Exception as e:
            logger.error(f"Error buscando notas: {str(e)}")
            return []