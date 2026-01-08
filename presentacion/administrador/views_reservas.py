#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vista para visualización y gestión de reservas por Administrador
Incluye:
- Dashboard con gráficos y reportes
- Sistema de reservas (igual que profesor pero sin restricciones)
- Cancelación de cualquier reserva
"""

import json
from datetime import datetime, timedelta, time
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from repositorio.postgres_repository.models import (
    Reservation, Teacher, Classroom, Course
)
from servicios.servicioReservas import servicio_reservas


def es_admin_o_secretaria(user):
    """Verifica si el usuario es administrador o secretaria"""
    return user.is_staff or user.groups.filter(name__in=['Secretaria', 'Administrador']).exists()


# ==========================
# DASHBOARD DE REPORTES
# ==========================

@login_required
@user_passes_test(es_admin_o_secretaria)
def dashboard_reservas(request):
    """
    Vista principal del dashboard de reservas con gráficos
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
        fecha_inicio = hoy - timedelta(days=30)
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        except ValueError:
            fecha_inicio = hoy - timedelta(days=30)
    
    if not fecha_fin:
        fecha_fin = hoy + timedelta(days=7)
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            fecha_fin = hoy + timedelta(days=7)
    
    # Query base
    reservas_query = Reservation.objects.filter(
        date__gte=fecha_inicio,
        date__lte=fecha_fin
    )
    
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
        reservas_por_profesor = reservas_query.values(
            'teacher__user__first_name',
            'teacher__user__last_name'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        for item in reservas_por_profesor:
            if item['teacher__user__first_name']:
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


# ==========================
# SISTEMA DE RESERVAS ADMIN
# ==========================

@login_required
@user_passes_test(es_admin_o_secretaria)
def reservas_admin_page(request):
    """
    Página de reservas para administrador (igual que profesor pero sin restricciones)
    """
    return render(request, 'administrador/recursos/reservas_admin.html')


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_GET
def reservas_admin_estado(request):
    """
    GET /administrador/reservas/estado/
    Obtiene el estado de ocupación de ambientes
    """
    date_str = request.GET.get('date')
    slot = request.GET.get('slot')

    if not date_str or not slot:
        return JsonResponse({'error': 'Faltan parámetros (date, slot).'}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido.'}, status=400)

    try:
        occupied = servicio_reservas.obtener_estado(date, slot, request.user)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'occupied': occupied})


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_POST
def reservas_admin_crear(request):
    """
    POST /administrador/reservas/api/
    Crea una nueva reserva (admin sin restricciones)
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    resource_code = data.get('resource_code')
    date_str = data.get('date')
    slot = data.get('slot')

    if not all([resource_code, date_str, slot]):
        return JsonResponse({'error': 'Parámetros incompletos.'}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido.'}, status=400)

    try:
        reserva = servicio_reservas.crear_reserva(
            request.user, 
            resource_code, 
            date, 
            slot,
            purpose=f"Reserva administrativa - {resource_code}"
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=409)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'id': str(reserva.id)}, status=201)


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["DELETE"])
def reservas_admin_cancelar(request, pk):
    """
    DELETE /administrador/reservas/api/<uuid:pk>/
    Cancela una reserva (cambia estado a cancelled/Inactivo)
    """
    try:
        servicio_reservas.eliminar_reserva(request.user, pk)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except PermissionError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'ok': True})


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_GET
def reservas_admin_todas(request):
    """
    GET /administrador/reservas/mis/
    Devuelve TODAS las reservas del sistema con estado
    """
    qs = servicio_reservas.obtener_reservas_profesor(request.user)

    reservas = []
    for r in qs:
        estado_display = 'Activo' if r.status == 'approved' else 'Inactivo'
        profesor_nombre = r.teacher.user.get_full_name() if r.teacher else 'Reserva administrativa'
        
        reservas.append({
            "id": str(r.id),
            "aula": r.classroom.name if r.classroom else 'N/A',
            "curso": r.course.name if r.course else 'N/A',
            "profesor": profesor_nombre,
            "fecha": r.date.strftime("%Y-%m-%d"),
            "slot": f"{r.start_time.strftime('%H:%M')} - {r.end_time.strftime('%H:%M')}",
            "estado": r.status,
            "estado_display": estado_display,
        })

    return JsonResponse({"reservas": reservas})


# ==========================
# APIs ADICIONALES
# ==========================

@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["GET"])
def api_reservas_del_dia(request):
    """
    API: Devuelve todas las reservas del día actual
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
            'profesor': r.teacher.user.get_full_name() if r.teacher else 'Reserva administrativa',
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
            'estado_display': 'Activo' if r.status == 'approved' else 'Inactivo',
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
@require_http_methods(["POST"])
def api_cancelar_reserva_dashboard(request, reserva_id):
    """
    API: Permite cancelar una reserva desde el dashboard
    POST /administrador/reservas/api/cancelar/<uuid>/
    """
    try:
        reserva = Reservation.objects.get(id=reserva_id)
    except Reservation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Reserva no encontrada'
        }, status=404)
    
    # Solo cancelar si no está ya cancelada
    if reserva.status == 'cancelled':
        return JsonResponse({
            'success': False,
            'error': 'La reserva ya está cancelada'
        }, status=400)
    
    reserva.status = 'cancelled'
    reserva.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Reserva cancelada exitosamente',
        'reserva_id': str(reserva.id)
    })


@login_required
@user_passes_test(es_admin_o_secretaria)
@require_http_methods(["GET"])
def api_restricciones_admin(request):
    """
    GET /administrador/reservas/api/restricciones/
    Devuelve info de restricciones (admin no tiene restricciones)
    """
    try:
        info = servicio_reservas.obtener_info_restricciones(request.user)
        return JsonResponse(info)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)