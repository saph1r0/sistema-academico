from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from servicios.servicioAsistencia import servicio_asistencia

class EstudianteAsistenciaView(LoginRequiredMixin, TemplateView):
    template_name = 'estudiante/asistencia/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = self.request.user.student
            
            reporte = servicio_asistencia.obtener_reporte_asistencia_estudiante(student.id)
            
            context['reporte'] = reporte
            
        except AttributeError:
            context['error'] = "No tienes un perfil de estudiante asociado."
        except Exception as e:
            context['error'] = f"Error cargando asistencias: {str(e)}"
            
        return context