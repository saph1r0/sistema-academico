from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from servicios.servicioHorario import ServicioHorario


servicio_horario = ServicioHorario()


class StudentScheduleView(LoginRequiredMixin, TemplateView):
    """Vista principal del horario del estudiante"""
    template_name = "estudiante/horarios/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estudiante = getattr(self.request.user, "student", None)

        if not estudiante:
            context["error"] = "No se encontró el perfil de estudiante."
            return context

        data = servicio_horario.obtener_horario_estudiante(estudiante.id)
        context["horario_json"] = data
        context["success"] = data.get("success", False)
        return context


class GetStudentScheduleView(LoginRequiredMixin, View):
    """Devuelve el horario del estudiante en formato JSON"""

    def get(self, request, *args, **kwargs):
        estudiante = getattr(request.user, "student", None)
        if not estudiante:
            return JsonResponse({"success": False, "error": "Usuario no es estudiante."})
        data = servicio_horario.obtener_horario_estudiante(estudiante.id)
        return JsonResponse(data)


class GetEnrolledLaboratoriesView(LoginRequiredMixin, View):
    """Obtiene los laboratorios en los que el estudiante está matriculado"""

    def get(self, request, *args, **kwargs):
        estudiante = getattr(request.user, "student", None)
        if not estudiante:
            return JsonResponse({"success": False, "error": "Usuario no es estudiante."})

        data = servicio_horario.obtener_laboratorios_estudiante(estudiante.id)
        return JsonResponse(data)


class CheckScheduleConflictView(LoginRequiredMixin, View):
    """Verifica si existe conflicto de horario antes de matricular"""

    def post(self, request, *args, **kwargs):
        estudiante = getattr(request.user, "student", None)
        if not estudiante:
            return JsonResponse({"success": False, "error": "Usuario no es estudiante."})

        nuevo_horario = request.POST.dict()
        result = servicio_horario.verificar_conflictos(estudiante.id, nuevo_horario)
        return JsonResponse(result)
