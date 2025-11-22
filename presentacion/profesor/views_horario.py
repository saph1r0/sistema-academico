from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from servicios.servicioHorario import ServicioHorario

servicio_horario = ServicioHorario()


class TeacherScheduleView(LoginRequiredMixin, TemplateView):
    """Vista principal del horario del docente"""
    template_name = "docente/horarios/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        docente = getattr(self.request.user, "teacher", None)

        if not docente:
            context["error"] = "No se encontró el perfil del docente."
            return context

        data = servicio_horario.obtener_horario_docente(docente.id)
        context["horario_json"] = data
        context["success"] = data.get("success", False)
        return context


class GetTeacherScheduleView(LoginRequiredMixin, View):
    """Devuelve el horario del docente en formato JSON"""

    def get(self, request, *args, **kwargs):
        docente = getattr(request.user, "teacher", None)
        if not docente:
            return JsonResponse({"success": False, "error": "Usuario no es docente."})
        data = servicio_horario.obtener_horario_docente(docente.id)
        return JsonResponse(data)
