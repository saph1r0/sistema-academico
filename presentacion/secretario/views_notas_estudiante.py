from django.views.generic import TemplateView, View
from .mixins import SecretarioRequiredMixin 
from servicios.servicioReporteNotas import ServicioReporteNotas 
from repositorio.postgres_repository.models import CourseGroup
from django.http import JsonResponse, HttpResponse
import csv
from datetime import datetime

class SecretarioNotasAlumnosAPIView(SecretarioRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        curso_id = request.GET.get('curso_id')
        if not curso_id:
            return JsonResponse({'error': 'Falta curso_id'}, status=400)
            
        servicio = ServicioReporteNotas()
        alumnos = servicio.obtener_lista_alumnos_curso(curso_id)
        return JsonResponse({'alumnos': alumnos})

class SecretarioNotasEstudiantesView(SecretarioRequiredMixin, TemplateView):
    template_name = 'secretario/notas_estudiantes/dashboard.html'

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

class ExportarNotasCSVSecretarioView(SecretarioRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        servicio = ServicioReporteNotas()
        stats = servicio.obtener_dashboard_admin()
        response = HttpResponse(content_type='text/csv')
        nombre_archivo = f"Resumen_Notas_Sec_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        writer = csv.writer(response)
        writer.writerow(['REPORTE DE NOTAS - RESUMEN GENERAL (SECRETARÍA)'])
        writer.writerow(['Fecha:', datetime.now().strftime("%d/%m/%Y %H:%M")])
        writer.writerow([]) 
        writer.writerow(['METRICAS GENERALES DEL SEMESTRE'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Promedio Ponderado Global', stats['promedio_global']])
        writer.writerow(['Tasa de Aprobación Global', f"{stats['tasa_aprobacion']}%"])
        writer.writerow(['Total Estudiantes Evaluados ', stats['total_evaluados']])
        writer.writerow(['Cantidad Estudiantes en Riesgo', stats['cantidad_riesgo']])
        
        return response