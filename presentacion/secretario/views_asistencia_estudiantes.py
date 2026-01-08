#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vistas de métricas de asistencia para secretario
Sistema completo de reportes, filtros y alertas
"""

from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, F, Case, When, FloatField
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from repositorio.postgres_repository.models import (
    SimpleAttendanceRecord, Student, CourseGroup, 
    Enrollment, Course, AcademicPeriod, Teacher
)


def es_admin_o_secretaria(user):
   
    return True 

#dashXasist

@login_required
@user_passes_test(es_admin_o_secretaria)
def dashboard_asistencia(request):
    """
    Dashboard principal con métricas generales y alertas
    """
    print(f"DEBUG: Accediendo a asistencia. Usuario: {request.user.username}")
    print(f"DEBUG: Grupos del usuario: {list(request.user.groups.values_list('name', flat=True))}")
    # Obtener parámetros de filtro
    curso_id = request.GET.get('curso')
    estudiante_id = request.GET.get('estudiante')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    periodo_id = request.GET.get('periodo')
    
    # Fechas por defecto: último mes
    if not fecha_inicio:
        fecha_inicio = (timezone.now().date() - timedelta(days=30))
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Query base de asistencias
    asistencias = SimpleAttendanceRecord.objects.filter(
        class_date__gte=fecha_inicio,
        class_date__lte=fecha_fin
    ).select_related(
        'student__user',
        'course_group__course',
        'recorded_by__user'
    )
    
    # Aplicar filtros
    if curso_id:
        asistencias = asistencias.filter(course_group_id=curso_id)
    
    if estudiante_id:
        asistencias = asistencias.filter(student_id=estudiante_id)
    
    if periodo_id:
        asistencias = asistencias.filter(course_group__academic_period_id=periodo_id)
    
 
    total_registros = asistencias.count()
    total_presentes = asistencias.filter(status='PRESENTE').count()
    total_faltas = asistencias.filter(status='FALTA').count()
    
    tasa_asistencia_global = (total_presentes / total_registros * 100) if total_registros > 0 else 0
    
    estudiantes_unicos = asistencias.values('student').distinct().count()
    
    cursos_activos = asistencias.values('course_group').distinct().count()
    
   
    estudiantes_riesgo = _obtener_estudiantes_en_riesgo(fecha_inicio, fecha_fin)
    
   
    cursos_stats = _obtener_estadisticas_por_curso(fecha_inicio, fecha_fin)
    

    evolucion_semanal = _obtener_evolucion_semanal(fecha_inicio, fecha_fin)
    
   
    cursos = CourseGroup.objects.select_related('course', 'academic_period').order_by('course__name')
    estudiantes = Student.objects.select_related('user').order_by('user__last_name')
    periodos = AcademicPeriod.objects.all().order_by('-start_date')
    
    context = {
        'page_title': 'Métricas de Asistencia',
        'metricas': {
            'total_registros': total_registros,
            'total_presentes': total_presentes,
            'total_faltas': total_faltas,
            'tasa_global': round(tasa_asistencia_global, 1),
            'estudiantes_unicos': estudiantes_unicos,
            'cursos_activos': cursos_activos,
        },
        'estudiantes_riesgo': estudiantes_riesgo,
        'cursos_stats': cursos_stats,
        'evolucion_semanal': evolucion_semanal,
        'cursos': cursos,
        'estudiantes': estudiantes,
        'periodos': periodos,
        'filtros': {
            'curso_id': curso_id,
            'estudiante_id': estudiante_id,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'periodo_id': periodo_id,
        }
    }
    
    return render(request, 'secretario/asistencia_estudiante/dashboard.html', context)


#reportXcurso

@login_required
@user_passes_test(es_admin_o_secretaria)
def reporte_por_curso(request, curso_id):
    """
    Reporte detallado de asistencia de un curso específico
    Lista todos los estudiantes con sus estadísticas
    """
    try:
        curso = CourseGroup.objects.select_related(
            'course', 'teacher__user', 'academic_period'
        ).get(id=curso_id)
    except CourseGroup.DoesNotExist:
        return render(request, 'secretario/asistencia_estudiante/error.html', {
            'error': 'Curso no encontrado'
        })
    
    # Obtener fechas del filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio:
        fecha_inicio = curso.academic_period.start_date
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Obtener estudiantes matriculados
    enrollments = Enrollment.objects.filter(
        course_group=curso,
        status='active'
    ).select_related('student__user')
    
    estudiantes_data = []
    
    for enrollment in enrollments:
        student = enrollment.student
        
        # Estadísticas de asistencia del estudiante en este curso
        registros = SimpleAttendanceRecord.objects.filter(
            student=student,
            course_group=curso,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total_clases = registros.count()
        total_presentes = registros.filter(status='PRESENTE').count()
        total_faltas = registros.filter(status='FALTA').count()
        
        porcentaje = (total_presentes / total_clases * 100) if total_clases > 0 else 0
        porcentaje_faltas = (total_faltas / total_clases * 100) if total_clases > 0 else 0
        
        # Determinar estado
        estado = 'normal'
        if porcentaje_faltas > 30:
            estado = 'critico'
        elif porcentaje_faltas > 20:
            estado = 'riesgo'
        elif porcentaje_faltas > 10:
            estado = 'alerta'
        
        estudiantes_data.append({
            'id': str(student.id),
            'codigo': student.student_code,
            'nombre': student.user.get_full_name(),
            'email': student.user.institutional_email,
            'total_clases': total_clases,
            'presentes': total_presentes,
            'faltas': total_faltas,
            'porcentaje_asistencia': round(porcentaje, 1),
            'porcentaje_faltas': round(porcentaje_faltas, 1),
            'estado': estado,
        })
    
    # Ordenar por porcentaje de faltas (descendente)
    estudiantes_data.sort(key=lambda x: x['porcentaje_faltas'], reverse=True)
    
    # Estadísticas del curso
    total_estudiantes = len(estudiantes_data)
    promedio_asistencia = sum(e['porcentaje_asistencia'] for e in estudiantes_data) / total_estudiantes if total_estudiantes > 0 else 0
    estudiantes_riesgo_count = len([e for e in estudiantes_data if e['estado'] in ['riesgo', 'critico']])
    
    context = {
        'page_title': f'Asistencia: {curso.course.name}',
        'curso': curso,
        'estudiantes': estudiantes_data,
        'estadisticas': {
            'total_estudiantes': total_estudiantes,
            'promedio_asistencia': round(promedio_asistencia, 1),
            'estudiantes_riesgo': estudiantes_riesgo_count,
        },
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'secretario/asistencia_estudiante/reporte_curso.html', context)


#reportXestudiante

@login_required
@user_passes_test(es_admin_o_secretaria)
def reporte_por_estudiante(request, estudiante_id):
    """
    Reporte detallado de un estudiante específico
    Muestra asistencia en todos sus cursos + promedio general
    """
    try:
        student = Student.objects.select_related('user').get(id=estudiante_id)
    except Student.DoesNotExist:
        return render(request, 'secretario/asistencia_estudiante/error.html', {
            'error': 'Estudiante no encontrado'
        })
    
    # Obtener fechas del filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio:
        fecha_inicio = (timezone.now().date() - timedelta(days=30))
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Obtener cursos matriculados
    enrollments = Enrollment.objects.filter(
        student=student,
        status='active'
    ).select_related('course_group__course', 'course_group__teacher__user')
    
    cursos_data = []
    total_clases_global = 0
    total_presentes_global = 0
    total_faltas_global = 0
    
    for enrollment in enrollments:
        course_group = enrollment.course_group
        
        # Estadísticas de asistencia en este curso
        registros = SimpleAttendanceRecord.objects.filter(
            student=student,
            course_group=course_group,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total_clases = registros.count()
        total_presentes = registros.filter(status='PRESENTE').count()
        total_faltas = registros.filter(status='FALTA').count()
        
        porcentaje = (total_presentes / total_clases * 100) if total_clases > 0 else 0
        porcentaje_faltas = (total_faltas / total_clases * 100) if total_clases > 0 else 0
        
        # Acumular para estadísticas globales
        total_clases_global += total_clases
        total_presentes_global += total_presentes
        total_faltas_global += total_faltas
        
        # Determinar estado
        estado = 'normal'
        if porcentaje_faltas > 30:
            estado = 'critico'
        elif porcentaje_faltas > 20:
            estado = 'riesgo'
        elif porcentaje_faltas > 10:
            estado = 'alerta'
        
        cursos_data.append({
            'id': str(course_group.id),
            'codigo': course_group.course.code,
            'nombre': course_group.course.name,
            'grupo': course_group.group_code,
            'profesor': course_group.teacher.user.get_full_name() if course_group.teacher else 'Sin asignar',
            'total_clases': total_clases,
            'presentes': total_presentes,
            'faltas': total_faltas,
            'porcentaje_asistencia': round(porcentaje, 1),
            'porcentaje_faltas': round(porcentaje_faltas, 1),
            'estado': estado,
        })
    
    # Ordenar por porcentaje de faltas (descendente)
    cursos_data.sort(key=lambda x: x['porcentaje_faltas'], reverse=True)
    
    # Estadísticas globales del estudiante
    porcentaje_global = (total_presentes_global / total_clases_global * 100) if total_clases_global > 0 else 0
    porcentaje_faltas_global = (total_faltas_global / total_clases_global * 100) if total_clases_global > 0 else 0
    
    estado_global = 'normal'
    if porcentaje_faltas_global > 30:
        estado_global = 'critico'
    elif porcentaje_faltas_global > 20:
        estado_global = 'riesgo'
    elif porcentaje_faltas_global > 10:
        estado_global = 'alerta'
    
    context = {
        'page_title': f'Asistencia: {student.user.get_full_name()}',
        'student': student,
        'cursos': cursos_data,
        'estadisticas_globales': {
            'total_clases': total_clases_global,
            'total_presentes': total_presentes_global,
            'total_faltas': total_faltas_global,
            'porcentaje_asistencia': round(porcentaje_global, 1),
            'porcentaje_faltas': round(porcentaje_faltas_global, 1),
            'estado': estado_global,
            'cursos_matriculados': len(cursos_data),
        },
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'secretario/asistencia_estudiante/reporte_estudiante.html', context)


#riesgoXestudiantes

@login_required
@user_passes_test(es_admin_o_secretaria)
def estudiantes_en_riesgo(request):
    """
    Lista completa de estudiantes con más del 20% de inasistencias
    Con opciones para notificar al docente
    """
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if not fecha_inicio:
        fecha_inicio = (timezone.now().date() - timedelta(days=30))
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    estudiantes_riesgo = _obtener_estudiantes_en_riesgo(fecha_inicio, fecha_fin)
    
    context = {
        'page_title': 'Estudiantes en Riesgo',
        'estudiantes_riesgo': estudiantes_riesgo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_riesgo': len(estudiantes_riesgo),
    }
    
    return render(request, 'secretario/asistencia_estudiante/estudiantes_riesgo.html', context)


    #funcXaux

def _obtener_estudiantes_en_riesgo(fecha_inicio, fecha_fin):
    """
    Detecta estudiantes con más del 20% de inasistencias
    Agrupa por curso para notificar al docente correspondiente
    """
    estudiantes_riesgo = []
    
    # Obtener todos los estudiantes activos
    students = Student.objects.filter(
        enrollment__status='active'
    ).distinct().select_related('user')
    
    for student in students:
        # Obtener cursos donde tiene más del 20% de faltas
        enrollments = Enrollment.objects.filter(
            student=student,
            status='active'
        ).select_related('course_group__course', 'course_group__teacher__user')
        
        cursos_problema = []
        
        for enrollment in enrollments:
            registros = SimpleAttendanceRecord.objects.filter(
                student=student,
                course_group=enrollment.course_group,
                class_date__gte=fecha_inicio,
                class_date__lte=fecha_fin
            )
            
            total = registros.count()
            if total == 0:
                continue
            
            faltas = registros.filter(status='FALTA').count()
            porcentaje_faltas = (faltas / total * 100)
            
            if porcentaje_faltas > 20:
                cursos_problema.append({
                    'curso': enrollment.course_group.course.name,
                    'curso_id': str(enrollment.course_group.id),
                    'grupo': enrollment.course_group.group_code,
                    'profesor': enrollment.course_group.teacher.user.get_full_name() if enrollment.course_group.teacher else 'Sin asignar',
                    'profesor_email': enrollment.course_group.teacher.user.institutional_email if enrollment.course_group.teacher else None,
                    'total_clases': total,
                    'faltas': faltas,
                    'porcentaje_faltas': round(porcentaje_faltas, 1),
                })
        
        if cursos_problema:
            estudiantes_riesgo.append({
                'id': str(student.id),
                'codigo': student.student_code,
                'nombre': student.user.get_full_name(),
                'email': student.user.institutional_email,
                'cursos_problema': cursos_problema,
                'total_cursos_problema': len(cursos_problema),
            })
    
    # Ordenar por número de cursos con problemas (descendente)
    estudiantes_riesgo.sort(key=lambda x: x['total_cursos_problema'], reverse=True)
    
    return estudiantes_riesgo


def _obtener_estadisticas_por_curso(fecha_inicio, fecha_fin):
    """Estadísticas de asistencia por curso"""
    cursos = CourseGroup.objects.select_related('course', 'teacher__user')
    
    cursos_stats = []
    
    for curso in cursos:
        registros = SimpleAttendanceRecord.objects.filter(
            course_group=curso,
            class_date__gte=fecha_inicio,
            class_date__lte=fecha_fin
        )
        
        total = registros.count()
        if total == 0:
            continue
        
        presentes = registros.filter(status='PRESENTE').count()
        porcentaje = (presentes / total * 100)
        
        cursos_stats.append({
            'id': str(curso.id),
            'nombre': curso.course.name,
            'codigo': curso.course.code,
            'grupo': curso.group_code,
            'profesor': curso.teacher.user.get_full_name() if curso.teacher else 'Sin asignar',
            'total_registros': total,
            'porcentaje_asistencia': round(porcentaje, 1),
        })
    
    # Ordenar por porcentaje de asistencia
    cursos_stats.sort(key=lambda x: x['porcentaje_asistencia'], reverse=True)
    
    return cursos_stats[:10] 


def _obtener_evolucion_semanal(fecha_inicio, fecha_fin):
    """Evolución semanal de la tasa de asistencia"""
    evolucion = []
    
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        semana_fin = min(fecha_actual + timedelta(days=6), fecha_fin)
        
        registros = SimpleAttendanceRecord.objects.filter(
            class_date__gte=fecha_actual,
            class_date__lte=semana_fin
        )
        
        total = registros.count()
        if total > 0:
            presentes = registros.filter(status='PRESENTE').count()
            porcentaje = (presentes / total * 100)
            
            evolucion.append({
                'semana': f"{fecha_actual.strftime('%d/%m')} - {semana_fin.strftime('%d/%m')}",
                'porcentaje': round(porcentaje, 1),
                'total_registros': total,
            })
        
        fecha_actual = semana_fin + timedelta(days=1)
    
    return evolucion