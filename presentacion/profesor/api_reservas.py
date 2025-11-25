# presentacion/profesor/api_reservas.py
from __future__ import annotations

import json
import uuid
from datetime import datetime, time
from uuid import UUID

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Model
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
)
from django.utils.dateparse import parse_date, parse_time
from django.db import models as dj_models
from django.views.decorators.http import require_http_methods


# =========================
# Utilidades generales
# =========================

def _parse_slot(slot_str: str) -> tuple[time | None, time | None]:
    """
    '08:50/09:40' -> (time(8,50), time(9,40))
    """
    try:
        a, b = slot_str.split("/")
        return datetime.strptime(a.strip(), "%H:%M").time(), datetime.strptime(b.strip(), "%H:%M").time()
    except Exception:
        return None, None


def _overlaps(a_start: time, a_end: time, b_start: time, b_end: time) -> bool:
    """
    Hay solape si a_start < b_end y a_end > b_start
    """
    return (a_start < b_end) and (a_end > b_start)


def _weekday_name_iso(d):
    return ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"][d.weekday()]


def _to_obj(val, default):
    """
    Si viene string -> json.loads; si viene None -> default; si dict/list -> igual.
    """
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return default
    return default


# =========================
# Modelos dinámicos para las tablas reales
# =========================

class _DynBase(dj_models.Model):
    class Meta:
        abstract = True
        app_label = 'dynamic_models'
        managed = False


class ResourceDyn(_DynBase):
    """Modelo dinámico para la tabla resources"""
    id = dj_models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = dj_models.CharField(max_length=100)
    name = dj_models.CharField(max_length=200)
    type = dj_models.CharField(max_length=50)
    capacity = dj_models.IntegerField()
    is_active = dj_models.BooleanField(default=True)
    created_at = dj_models.DateTimeField(auto_now_add=True)
    
    class Meta(_DynBase.Meta):
        db_table = 'resources'


class ReservationDyn(_DynBase):
    """Modelo dinámico para la tabla reservations"""
    id = dj_models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_id = dj_models.UUIDField()
    requested_by = dj_models.UUIDField()
    course_group_id = dj_models.UUIDField(null=True, blank=True)
    laboratory_id = dj_models.UUIDField(null=True, blank=True)
    reservation_date = dj_models.DateField()
    start_time = dj_models.TimeField()
    end_time = dj_models.TimeField()
    status = dj_models.CharField(max_length=20, default='approved')
    purpose = dj_models.TextField(null=True, blank=True)
    approved_at = dj_models.DateTimeField(null=True, blank=True)
    created_at = dj_models.DateTimeField(auto_now_add=True)
    
    class Meta(_DynBase.Meta):
        db_table = 'reservations'


class CourseGroupDyn(_DynBase):
    """Modelo dinámico para la tabla course_groups"""
    id = dj_models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule_info = dj_models.JSONField(null=True, blank=True)
    classroom = dj_models.CharField(max_length=100, null=True, blank=True)
    group_code = dj_models.CharField(max_length=50, null=True, blank=True)
    
    class Meta(_DynBase.Meta):
        db_table = 'course_groups'


# =========================
# Lógica de ocupación
# =========================

def _ocupadas_por_clases(fecha, start_t, end_t):
    """
    Lee CourseGroup.schedule_info['slots'] y marca aulas ocupadas por CLASE.
    """
    dia = _weekday_name_iso(fecha)
    ocupadas = {}

    try:
        for cg in CourseGroupDyn.objects.all():
            info = _to_obj(cg.schedule_info, {})
            slots = _to_obj(info.get("slots"), [])
            classroom_fallback = cg.classroom

            for s in slots:
                s = _to_obj(s, {})
                if (s.get("day") or "").lower() != dia:
                    continue
                try:
                    s_start = datetime.strptime(s["start"], "%H:%M").time()
                    s_end   = datetime.strptime(s["end"],   "%H:%M").time()
                except Exception:
                    continue
                if _overlaps(s_start, s_end, start_t, end_t):
                    code = s.get("resource_code") or classroom_fallback
                    if code:
                        ocupadas[code] = {"reason": "class", "label": "Clase"}
    except Exception:
        pass  # Si hay error, simplemente no mostramos clases

    return ocupadas


def _ocupadas_por_reservas(fecha, start_t, end_t, user_id):
    """
    Marca aulas ocupadas por RESERVAS usando la tabla real.
    """
    ocupadas = {}

    try:
        # Consulta directa a la tabla reservations
        reservations = ReservationDyn.objects.filter(
            reservation_date=fecha,
            start_time__lt=end_t,
            end_time__gt=start_t
        )

        for r in reservations:
            # Obtener el código del recurso
            try:
                resource = ResourceDyn.objects.get(id=r.resource_id)
                code = resource.code
            except ResourceDyn.DoesNotExist:
                continue

            mine = (r.requested_by == user_id) if user_id is not None else False

            payload = {"reason": "reservation", "mine": mine}
            if mine:
                payload["id"] = str(r.id)

            ocupadas[code] = payload

    except Exception:
        pass  # Si hay error, simplemente no mostramos reservas

    return ocupadas


# =========================
# Endpoints
# =========================

@login_required
@require_http_methods(["GET"])
def estado_ocupacion(request):
    """
    GET /profesor/reservas/estado/?date=YYYY-MM-DD&slot=HH:MM/HH:MM
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    date_str = request.GET.get("date")
    if not date_str:
        return HttpResponseBadRequest("date requerido (YYYY-MM-DD)")
    fecha = parse_date(date_str)
    if not fecha:
        return HttpResponseBadRequest("date inválido")

    slot = request.GET.get("slot")
    start_t = end_t = None
    if slot:
        start_t, end_t = _parse_slot(slot)
    else:
        start_t = parse_time(request.GET.get("start") or "")
        end_t   = parse_time(request.GET.get("end") or "")
    if not (start_t and end_t):
        return HttpResponseBadRequest("slot o start/end requeridos (HH:MM/HH:MM)")

    # Mezclar clases + reservas (clase prevalece)
    by_classes = _ocupadas_por_clases(fecha, start_t, end_t)
    by_reservs = _ocupadas_por_reservas(fecha, start_t, end_t, request.user.id)

    merged = {**by_reservs, **by_classes}

    data = [{"code": k, **v} for k, v in merged.items()]
    return JsonResponse({"occupied": data})


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def crear_reserva(request):
    """
    POST /profesor/reservas/api/
    Body JSON: { "resource_code": "A-201", "date": "2025-11-06", "slot": "08:50/09:40", "purpose": "Clase extra" }
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    code = (data.get("resource_code") or "").strip()
    fecha = parse_date(data.get("date") or "")
    slot = data.get("slot")
    start_t = end_t = None
    if slot:
        start_t, end_t = _parse_slot(slot)
    else:
        start_t = parse_time(data.get("start") or "")
        end_t   = parse_time(data.get("end") or "")

    if not code:
        return HttpResponseBadRequest("resource_code requerido")
    if not fecha:
        return HttpResponseBadRequest("date requerido (YYYY-MM-DD)")
    if not (start_t and end_t):
        return HttpResponseBadRequest("slot o start/end requeridos (HH:MM/HH:MM)")

    # 1) Bloqueo por CLASE
    if code in _ocupadas_por_clases(fecha, start_t, end_t):
        return JsonResponse({"error": "Aula ocupada por clase"}, status=409)

    # 2) Comprobar que el recurso exista
    try:
        resource = ResourceDyn.objects.get(code=code)
    except ResourceDyn.DoesNotExist:
        return HttpResponseBadRequest("resource_code no existe")

    # 3) Colisión con otras reservas
    existing = ReservationDyn.objects.filter(
        resource_id=resource.id,
        reservation_date=fecha,
        start_time__lt=end_t,
        end_time__gt=start_t
    )

    if existing.exists():
        return JsonResponse({"error": "Aula ya reservada"}, status=409)

    # 4) Crear registro
    r = ReservationDyn.objects.create(
        resource_id=resource.id,
        requested_by=request.user.id,
        reservation_date=fecha,
        start_time=start_t,
        end_time=end_t,
        status="approved",
        purpose=data.get("purpose") or ""
    )

    return JsonResponse({"ok": True, "id": str(r.id)}, status=201)


@login_required
@require_http_methods(["DELETE"])
@transaction.atomic
def eliminar_reserva(request, pk):
    """
    DELETE /profesor/reservas/api/<uuid:pk>/
    """
    if request.method not in ("DELETE", "POST"):
        return HttpResponseNotAllowed(["DELETE", "POST"])

    try:
        _ = UUID(str(pk), version=4)
    except Exception:
        return HttpResponseBadRequest("id inválido")

    try:
        r = ReservationDyn.objects.get(id=pk)
    except ReservationDyn.DoesNotExist:
        return HttpResponseBadRequest("Reserva no existe")

    # Verificar que el usuario actual sea el dueño de la reserva
    if r.requested_by != request.user.id:
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden("No puedes borrar reservas de otro usuario")

    r.delete()
    return JsonResponse({"ok": True})