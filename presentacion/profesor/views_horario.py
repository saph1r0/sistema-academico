from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from servicios.servicioHorario import ServicioHorario

servicio_horario = ServicioHorario()


class TeacherScheduleView(LoginRequiredMixin, TemplateView):
    """Vista principal del horario del profesor"""
    template_name = "profesor/horarios/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = getattr(self.request.user, "teacher", None)

        if not teacher:
            context["error"] = "No se encontró el perfil de profesor."
            context["success"] = False
            return context

        data = servicio_horario.obtener_horario_profesor(teacher.id)
        context["success"] = data.get("success", False)
        context["teacher_name"] = data.get("teacher_name", "")
        context["total_eventos"] = data.get("total_eventos", 0)
        context["total_cursos"] = data.get("total_cursos", 0)
        context["total_laboratorios"] = data.get("total_laboratorios", 0)
        return context


class GetTeacherScheduleView(LoginRequiredMixin, View):
    """Devuelve el horario del profesor en formato JSON"""

    def get(self, request, *args, **kwargs):
        teacher = getattr(request.user, "teacher", None)
        if not teacher:
            return JsonResponse({"success": False, "error": "Usuario no es profesor."})
        data = servicio_horario.obtener_horario_profesor(teacher.id)
        return JsonResponse(data)
