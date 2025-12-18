from django.db.models import Count, Q
from repositorio.postgres_repository.models import SimpleAttendanceRecord, CourseGroup, Enrollment, Student
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ServicioReporteAsistencia:
    
    def generar_data_reporte(self, filtros):
        """
        Genera el reporte usando la tabla correcta: SimpleAttendanceRecord
        """
        try:
            tipo = filtros.get('tipo_reporte')
            ciclo = filtros.get('ciclo')
            
            data_reporte = {
                'titulo': 'REPORTE DE ASISTENCIA',
                'subtitulo': f'Periodo: {ciclo.name}',
                'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M"),
                'tablas': []
            }

            grupos = []
            if tipo == 'global':
                grupos = CourseGroup.objects.filter(academic_period=ciclo).select_related('course', 'teacher__user')
                data_reporte['titulo'] = "REPORTE GLOBAL DE ASISTENCIA"
            elif tipo == 'por_curso':
                codigo = filtros.get('curso_codigo')
                grupos = CourseGroup.objects.filter(academic_period=ciclo, course__code=codigo).select_related('course', 'teacher__user')
                data_reporte['titulo'] = f"REPORTE DE ASISTENCIA - CURSO: {codigo}"

            if tipo in ['global', 'por_curso']:
                for grupo in grupos:
                    # Alumnos matriculados
                    matriculas = Enrollment.objects.filter(course_group=grupo).select_related('student__user').order_by('student__user__last_name')
                    
                    if not matriculas.exists() and tipo == 'global': continue

                    filas = []
                    
                    for matricula in matriculas:
                        alumno = matricula.student
                        asistencias_qs = SimpleAttendanceRecord.objects.filter(
                            student=alumno,
                            course_group=grupo
                        )
                        
                        total_sesiones = asistencias_qs.count()
                        presentes = asistencias_qs.filter(status__icontains='PRESENTE').count()
                        otros_ok = asistencias_qs.filter(Q(status__icontains='TARDANZA') | Q(status__icontains='JUSTIFICADO')).count()
                        
                        presentes_totales = presentes + otros_ok
                        faltas = total_sesiones - presentes_totales
                        porcentaje = (presentes_totales / total_sesiones * 100) if total_sesiones > 0 else 0.0
                        
                        estado_str = "NORMAL"
                        if porcentaje < 70: estado_str = "INHABILITADO"
                        elif porcentaje < 85: estado_str = "EN RIESGO"

                        filas.append({
                            'cui': alumno.student_code,
                            'alumno': f"{alumno.user.last_name}, {alumno.user.first_name}",
                            'total': total_sesiones,
                            'presentes': presentes_totales,
                            'faltas': faltas,
                            'porcentaje': f"{porcentaje:.1f}%",
                            'estado': estado_str
                        })

                    if filas or tipo == 'por_curso':
                        data_reporte['tablas'].append({
                            'tipo': 'lista_curso',
                            'nombre_curso': f"{grupo.course.name} (G{grupo.group_code})",
                            'docente': f"{grupo.teacher.user.get_full_name() if grupo.teacher else 'Vacante'}",
                            'filas': filas
                        })
            elif tipo == 'por_estudiante':
                cui = filtros.get('estudiante_cui')
                estudiante = Student.objects.filter(student_code=cui).first()
                
                if estudiante:
                    data_reporte['subtitulo'] += f" | Estudiante: {estudiante.user.get_full_name()}"
                    
                    matriculas = Enrollment.objects.filter(student=estudiante, course_group__academic_period=ciclo)
                    
                    for matricula in matriculas:
                        grupo = matricula.course_group
                        
                        registros = SimpleAttendanceRecord.objects.filter(
                            student=estudiante, 
                            course_group=grupo
                        ).order_by('class_date')
                        
                        filas_detalle = []
                        presentes = 0
                        total = 0
                        
                        for reg in registros:
                            total += 1
                            estado = str(reg.status).upper() 
                            
                            es_presente = estado in ['PRESENTE', 'TARDANZA', 'JUSTIFICADO']
                            if es_presente: presentes += 1
                            
                            lbl = estado 
                            
                           
                            obs = getattr(reg, 'observation', '-') or '-'

                            filas_detalle.append({
                                'fecha': reg.class_date.strftime("%d/%m/%Y"), 
                                'estado': lbl,
                                'observacion': obs
                            })
                        
                        porc = (presentes / total * 100) if total > 0 else 0.0
                        
                        data_reporte['tablas'].append({
                            'tipo': 'kardex_estudiante',
                            'nombre_curso': f"{grupo.course.name} (G{grupo.group_code})",
                            'porcentaje_global': f"{porc:.1f}%",
                            'filas': filas_detalle
                        })

            return data_reporte

        except Exception as e:
            logger.error(f"Error reporte asistencia: {str(e)}")
            return None