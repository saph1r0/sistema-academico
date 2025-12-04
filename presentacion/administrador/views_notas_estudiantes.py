from django.views.generic import TemplateView, View
from .mixins import AdminRequiredMixin
from servicios.servicioReporteNotas import ServicioReporteNotas 
from repositorio.postgres_repository.models import CourseGroup
from django.http import JsonResponse
import json

class AdminNotasAlumnosAPIView(AdminRequiredMixin, View):

    
    def get(self, request, *args, **kwargs):
        curso_id = request.GET.get('curso_id')
        if not curso_id:
            return JsonResponse({'error': 'Falta curso_id'}, status=400)
            
        servicio = ServicioReporteNotas()
        alumnos = servicio.obtener_lista_alumnos_curso(curso_id)
        
        return JsonResponse({'alumnos': alumnos})

class AdminNotasEstudiantesView(AdminRequiredMixin, TemplateView):
    template_name = 'administrador/notas_estudiantes/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        servicio = ServicioReporteNotas()
        
        context['stats'] = servicio.obtener_dashboard_admin()
        
        context['lista_cursos'] = CourseGroup.objects.select_related('course').order_by('course__name')

        curso_id = self.request.GET.get('curso_id')
        busqueda = self.request.GET.get('busqueda')
        
        resultados_busqueda = []
        if curso_id or busqueda:
            resultados_busqueda = servicio.buscar_notas_detalladas(curso_id, busqueda)
            
        context['resultados_busqueda'] = resultados_busqueda
        context['filtros_activos'] = {'curso_id': curso_id, 'busqueda': busqueda}
        
        return context