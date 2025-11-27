#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para gestión de reservas de ambientes del profesor
Reserva automática de 9 ambientes (3 pisos)
"""


import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from servicios.servicioReservas    import servicio_reservas

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
    Devuelve TODAS las reservas del profesor autenticado.
    NO usa date ni slot.
    """
    qs = servicio_reservas.obtener_reservas_profesor(request.user)

    reservas = []
    for r in qs:
        reservas.append({
            "id": str(r.id),
            "aula": r.classroom.name,  # o r.classroom.code según tu modelo
            "curso": r.course.name,
            "fecha": r.date.strftime("%Y-%m-%d"),
            "slot": f"{r.start_time.strftime('%H:%M')} - {r.end_time.strftime('%H:%M')}",
            "estado": r.status,            # o r.get_status_display()
        })

    return JsonResponse({"reservas": reservas})
