#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vista para visualización y gestión de reservas por Administrador y Secretaria
Incluye filtros avanzados y validaciones automáticas
"""

from datetime import datetime, timedelta, time
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

from repositorio.postgres_repository.models import (
    Reservation, Teacher, Classroom, Course, Horario, Aula
)


def es_admin_o_secretaria(user):
    """Verifica si el usuario es administrador o secretaria"""
    return user.is_staff or user.groups.filter(name__in=['Secretaria', 'Administrador']).exists()


@login_required
@user_passes_test(es_admin_o_secretaria)
def dashboard_reservas(request):
    """
    Vista principal del dashboard de reservas
    """
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    profesor_id = request.GET.get('profesor')
    aula_id = request.GET.get('aula')
    dia_semana = request.GET.get('dia')
    estado = request.GET.get('estado', 'all')
    
    # Fecha por defecto: últimos 30 días
    hoy = timezone.now().date()
    
    if not fecha_inicio:
        # Mostrar últimos 30 días por defecto
        fecha_inicio = hoy - timedelta(days=30)
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        except ValueError:
            fecha_inicio = hoy - timedelta(days=30)
    
    if not fecha_fin:
        # Mostrar hasta mañana para ver reservas futuras
        fecha_fin = hoy + timedelta(days=7)
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            fecha_fin = hoy + timedelta(days=7)
    
    print(f"=== DEBUG: Filtro fechas {fecha_inicio} a {fecha_fin} ===")
    
    # Query base
    reservas_query = Reservation.objects.filter(
        date__gte=fecha_inicio,
        date__lte=fecha_fin
    )
    
    print(f"Reservas en rango: {reservas_query.count()}")
    
    # Solo aplicar filtro de estado si no es 'all'
    if estado and estado != 'all':
        reservas_query = reservas_query.filter(status=estado)
    
    # Aplicar otros filtros
    if profesor_id:
        reservas_query = reservas_query.filter(teacher_id=profesor_id)
    
    if aula_id:
        reservas_query = reservas_query.filter(classroom_id=aula_id)
    
    if dia_semana:
        dias_map = {
            'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
            'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
        }
        dia_num = dias_map.get(dia_semana.lower())
        if dia_num is not None:
            reservas_query = reservas_query.filter(date__week_day=dia_num + 2)
    
    # Obtener reservas con relaciones
    reservas = reservas_query.select_related(
        'teacher__user',
        'classroom',
        'course'
    ).order_by('-date', 'start_time')[:100]
    
    print(f"Reservas a mostrar: {len(reservas)}")
    
    # Estadísticas
    estadisticas = {
        'total_reservas': reservas_query.count(),
        'aprobadas': reservas_query.filter(status='approved').count(),
        'pendientes': reservas_query.filter(status='pending').count(),
        'rechazadas': reservas_query.filter(status='rejected').count(),
        'canceladas': reservas_query.filter(status='cancelled').count(),
        'reservas_por_docente': {},
        'reservas_por_aula': {},
        'reservas_por_fecha': {}
    }
    
    # Agrupar por profesor
    try:
        from django.db.models import Count
        reservas_por_profesor = reservas_query.values(
            'teacher__user__first_name',
            'teacher__user__last_name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        for item in reservas_por_profesor:
            nombre = f"{item['teacher__user__first_name']} {item['teacher__user__last_name']}"
            estadisticas['reservas_por_docente'][nombre] = item['total']
    except Exception as e:
        print(f"Error estadísticas docente: {e}")
    
    # Agrupar por aula
    try:
        reservas_por_aula = reservas_query.values(
            'classroom__code',
            'classroom__name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        for item in reservas_por_aula:
            aula_nombre = f"{item['classroom__code']} - {item['classroom__name']}"
            estadisticas['reservas_por_aula'][aula_nombre] = item['total']
    except Exception as e:
        print(f"Error estadísticas aula: {e}")
    
    # Agrupar por fecha
    try:
        reservas_por_fecha = reservas_query.values('date').annotate(
            total=Count('id')
        ).order_by('date')
        
        for item in reservas_por_fecha:
            fecha_str = item['date'].strftime('%Y-%m-%d')
            estadisticas['reservas_por_fecha'][fecha_str] = item['total']
    except Exception as e:
        print(f"Error estadísticas fecha: {e}")
    
    # Listas para selectores
    profesores = Teacher.objects.select_related('user').all()
    aulas = Classroom.objects.filter(is_active=True).order_by('code')
    
    context = {
        'page_title': 'Dashboard de Reservas',
        'reservas': reservas,
        'estadisticas': estadisticas,
        'profesores': profesores,
        'aulas': aulas,
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'profesor_id': profesor_id,
            'aula_id': aula_id,
            'dia_semana': dia_semana,
            'estado': estado,
            'hoy': hoy,
        }
    }
    
    return render(request, 'administrador/recursos/index.html', context)


def _detectar_profesores_excedidos(fecha_inicio, fecha_fin):
    """
    Detecta profesores que han hecho más de 4 reservas en la semana
    """
    # Calcular inicio y fin de la semana actual
    inicio_semana = fecha_inicio - timedelta(days=fecha_inicio.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    profesores_count = Reservation.objects.filter(
        date__gte=inicio_semana,
        date__lte=fin_semana,
        status__in=['approved', 'pending']
    ).values(
        'teacher__id',
        'teacher__user__first_name',
        'teacher__user__last_name'
    ).annotate(
        total_reservas=Count('id')
    ).filter(
        total_reservas__gt=4
    ).order_by('-total_reservas')
    
    return [
        {
            'profesor_id': p['teacher__id'],
            'nombre': f"{p['teacher__user__first_name']} {p['teacher__user__last_name']}",
            'total': p['total_reservas'],
            'exceso': p['total_reservas'] - 4
        }
        for p in profesores_count
    ]


def _detectar_reservas_anticipadas(reservas):
    """
    Detecta reservas hechas con más de 3 días de anticipación
    """
    hoy = timezone.now().date()
    anticipadas = []
    
    for reserva in reservas:
        dias_anticipacion = (reserva.date - hoy).days
        if dias_anticipacion > 3:
            anticipadas.append({
                'id': str(reserva.id),
                'profesor': reserva.teacher.user.get_full_name(),
                'aula': reserva.classroom.code,
                'fecha': reserva.date,
                'dias_anticipacion': dias_anticipacion,
                'created_at': reserva.created_at
            })
    
    return sorted(anticipadas, key=lambda x: x['dias_anticipacion'], reverse=True)[:20]


# ... (resto del código de las API se mantiene igual)
@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["GET"])
def api_reservas_del_dia(request):
    """
    API: Devuelve todas las reservas del día actual
    GET /administrador/reservas/api/dia/
    """
    fecha = request.GET.get('fecha')
    if fecha:
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
    else:
        fecha = timezone.now().date()
    
    reservas = Reservation.objects.filter(
        date=fecha
    ).select_related(
        'teacher__user',
        'classroom',
        'course'
    ).order_by('start_time')
    
    data = []
    for r in reservas:
        data.append({
            'id': str(r.id),
            'profesor': r.teacher.user.get_full_name() if r.teacher else 'N/A',
            'profesor_id': r.teacher.id if r.teacher else None,
            'aula': r.classroom.code if r.classroom else 'N/A',
            'aula_nombre': r.classroom.name if r.classroom else 'N/A',
            'curso': r.course.name if r.course else 'N/A',
            'fecha': r.date.strftime('%Y-%m-%d'),
            'dia_semana': r.date.strftime('%A'),
            'hora_inicio': r.start_time.strftime('%H:%M'),
            'hora_fin': r.end_time.strftime('%H:%M'),
            'duracion_horas': (datetime.combine(r.date, r.end_time) - datetime.combine(r.date, r.start_time)).seconds / 3600,
            'proposito': r.purpose or '',
            'estado': r.status,
            'estado_display': r.get_status_display() if hasattr(r, 'get_status_display') else r.status,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    return JsonResponse({
        'success': True,
        'fecha': fecha.strftime('%Y-%m-%d'),
        'total': len(data),
        'reservas': data
    })


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["GET"])
def api_validar_restricciones(request):
    """
    API: Valida si un profesor puede hacer una nueva reserva
    GET /administrador/reservas/api/validar/?profesor_id=X&fecha=YYYY-MM-DD
    """
    profesor_id = request.GET.get('profesor_id')
    fecha_str = request.GET.get('fecha')
    
    if not all([profesor_id, fecha_str]):
        return JsonResponse({
            'success': False,
            'error': 'Parámetros incompletos'
        }, status=400)
    
    try:
        profesor = Teacher.objects.get(id=profesor_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except (Teacher.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Profesor o fecha inválidos'
        }, status=400)
    
    # VALIDACIÓN 1: Más de 4 reservas a la semana
    inicio_semana = fecha - timedelta(days=fecha.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    reservas_semana = Reservation.objects.filter(
        teacher=profesor,
        date__gte=inicio_semana,
        date__lte=fin_semana,
        status__in=['approved', 'pending']
    ).count()
    
    puede_reservar_semana = reservas_semana < 4
    
    # VALIDACIÓN 2: Más de 3 días de anticipación
    hoy = timezone.now().date()
    dias_anticipacion = (fecha - hoy).days
    puede_reservar_anticipacion = dias_anticipacion <= 3
    
    # Resultado
    validaciones = {
        'puede_reservar': puede_reservar_semana and puede_reservar_anticipacion,
        'reservas_semana': reservas_semana,
        'limite_semana': 4,
        'reservas_restantes': max(0, 4 - reservas_semana),
        'dias_anticipacion': dias_anticipacion,
        'limite_anticipacion': 3,
        'restricciones': []
    }
    
    if not puede_reservar_semana:
        validaciones['restricciones'].append(
            f"El profesor ya tiene {reservas_semana} reservas esta semana (límite: 4)"
        )
    
    if not puede_reservar_anticipacion:
        validaciones['restricciones'].append(
            f"La reserva es con {dias_anticipacion} días de anticipación (límite: 3 días)"
        )
    
    return JsonResponse({
        'success': True,
        'validaciones': validaciones,
        'profesor': profesor.user.get_full_name()
    })


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["GET"])
def api_reservas_por_filtro(request):
    """
    API: Filtra reservas por múltiples criterios
    GET /administrador/reservas/api/filtrar/?profesor=X&aula=Y&fecha_inicio=...
    """
    profesor_id = request.GET.get('profesor')
    aula_id = request.GET.get('aula')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    dia_semana = request.GET.get('dia')
    estado = request.GET.get('estado')
    
    # Query base
    reservas = Reservation.objects.select_related(
        'teacher__user', 'classroom', 'course'
    )
    
    # Aplicar filtros
    if profesor_id:
        reservas = reservas.filter(teacher_id=profesor_id)
    
    if aula_id:
        reservas = reservas.filter(classroom_id=aula_id)
    
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        reservas = reservas.filter(date__gte=fecha_inicio)
    
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        reservas = reservas.filter(date__lte=fecha_fin)
    
    if estado:
        reservas = reservas.filter(status=estado)
    
    if dia_semana:
        dias_map = {
            'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
            'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
        }
        dia_num = dias_map.get(dia_semana.lower())
        if dia_num is not None:
            reservas = reservas.filter(date__week_day=dia_num + 2)
    
    reservas = reservas.order_by('-date', 'start_time')[:200]
    
    data = []
    for r in reservas:
        data.append({
            'id': str(r.id),
            'profesor': r.teacher.user.get_full_name() if r.teacher else 'N/A',
            'aula': r.classroom.code if r.classroom else 'N/A',
            'curso': r.course.name if r.course else 'N/A',
            'fecha': r.date.strftime('%Y-%m-%d'),
            'dia_semana': r.date.strftime('%A'),
            'hora_inicio': r.start_time.strftime('%H:%M'),
            'hora_fin': r.end_time.strftime('%H:%M'),
            'estado': r.status,
            'proposito': r.purpose or ''
        })
    
    return JsonResponse({
        'success': True,
        'total': len(data),
        'reservas': data
    })


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["POST"])
def api_cancelar_reserva(request, reserva_id):
    """
    API: Permite a admin/secretaria cancelar una reserva
    POST /administrador/reservas/api/cancelar/<uuid>/
    """
    try:
        reserva = Reservation.objects.get(id=reserva_id)
    except Reservation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    
    # Solo cancelar si no está ya cancelada o rechazada
    if reserva.status in ['cancelled', 'rejected']:
        return JsonResponse({
            'success': False,
            'error': f'La reserva ya está {reserva.get_status_display()}'
        }, status=400)
    
    reserva.status = 'cancelled'
    reserva.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Reserva cancelada exitosamente',
        'reserva_id': str(reserva.id)
    })