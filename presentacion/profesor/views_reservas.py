#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para gestión de reservas de ambientes del profesor
Ahora incluye visualización del estado (Activo/Inactivo)
"""

import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from servicios.servicioReservas import servicio_reservas

# -----------------------------
# Página principal
# -----------------------------
@login_required
def reservas_ambientes_page(request):
    return render(request, 'profesor/templates/profesor/reservas/index.html')


# -----------------------------
# GET /profesor/reservas/estado/
# -----------------------------
@login_required
@require_GET
def reservas_estado(request):
    """
    Parámetros:
      ?date=YYYY-MM-DD
      &slot=HH:MM/HH:MM
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


# -----------------------------
# POST /profesor/reservas/api/
# body: { "resource_code": "A-101", "date": "YYYY-MM-DD", "slot": "07:00/07:50" }
# -----------------------------
@login_required
@require_POST
def reservas_api(request):
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
        reserva = servicio_reservas.crear_reserva(request.user, resource_code, date, slot)
    except ValueError as e:
        # Conflictos de negocio → 409
        return JsonResponse({'error': str(e)}, status=409)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'id': str(reserva.id)}, status=201)


# -----------------------------
# DELETE /profesor/reservas/api/<uuid:pk>/
# -----------------------------
@login_required
@require_http_methods(["DELETE"])
def reserva_api_detail(request, pk):
    try:
        servicio_reservas.eliminar_reserva(request.user, pk)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except PermissionError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'ok': True})


# -----------------------------
# GET /profesor/reservas/mis/
# -----------------------------
@login_required
@require_GET
def reservas_mis(request):
    """
    Devuelve TODAS las reservas del profesor autenticado con su estado.
    NO usa date ni slot.
    """
    qs = servicio_reservas.obtener_reservas_profesor(request.user)

    reservas = []
    for r in qs:
        # Determinar estado legible
        estado_display = 'Activo' if r.status == 'approved' else 'Inactivo'
        
        reservas.append({
            "id": str(r.id),
            "aula": r.classroom.name if r.classroom else 'N/A',
            "curso": r.course.name if r.course else 'N/A',
            "fecha": r.date.strftime("%Y-%m-%d"),
            "slot": f"{r.start_time.strftime('%H:%M')} - {r.end_time.strftime('%H:%M')}",
            "estado": r.status,  # approved o cancelled
            "estado_display": estado_display,  # Activo o Inactivo
        })

    return JsonResponse({"reservas": reservas})


@login_required
@require_http_methods(["GET"])
def api_restricciones_profesor(request):
    """
    GET /profesor/reservas/api/restricciones/
    
    Devuelve información sobre las restricciones del profesor actual
    """
    try:
        info = servicio_reservas.obtener_info_restricciones(request.user)
        return JsonResponse(info)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_validar_reserva_profesor(request):
    """
    POST /profesor/reservas/api/validar/
    Body: { "fecha": "2025-12-10" }
    
    Valida si el profesor puede hacer una reserva en la fecha indicada
    """
    import json
    from datetime import datetime
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        fecha_str = data.get('fecha')
        
        if not fecha_str:
            return JsonResponse({
                'success': False,
                'error': 'Fecha requerida'
            }, status=400)
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Formato de fecha inválido (usar YYYY-MM-DD)'
            }, status=400)
        
        # Validar restricciones
        puede_reservar, errores = servicio_reservas.validar_restricciones(
            request.user, fecha
        )
        
        return JsonResponse({
            'success': True,
            'puede_reservar': puede_reservar,
            'errores': errores,
            'mensaje': errores[0] if errores else 'Puedes reservar en esta fecha'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_reporte_semanal_profesor(request):
    """
    GET /profesor/reservas/api/reporte-semanal/
    
    Devuelve un reporte de todas las reservas de la semana actual
    """
    from datetime import datetime
    
    try:
        fecha_str = request.GET.get('fecha')
        
        if fecha_str:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        else:
            fecha = None
        
        reporte = servicio_reservas.obtener_reporte_semanal(fecha)
        
        return JsonResponse({
            'success': True,
            'reporte': reporte
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)