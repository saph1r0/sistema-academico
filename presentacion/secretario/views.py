"""
Vistas para el módulo de secretarios
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import HttpResponse

from .mixins import SecretarioRequiredMixin
from servicios.servicioMatricula import ServicioMatricula
from servicios.servicioReservas import ServicioReservas
from servicios.servicioReportes import ServicioReportes
from servicios.servicioMonitoreo import ServicioMonitoreo


class SecretarioDashboardView(SecretarioRequiredMixin, TemplateView):
    """Dashboard principal del secretario"""
    template_name = 'secretario/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'resumen_inscripciones': ServicioMatricula.obtener_resumen_inscripciones(),
            'laboratorios_ocupacion': ServicioReservas.obtener_ocupacion_laboratorios(),
            'alertas_sistema': ServicioMonitoreo.obtener_alertas_academicas(),
            'estadisticas_generales': ServicioReportes.obtener_estadisticas_generales()
        })
        return context


class SecretarioLaboratoriosView(SecretarioRequiredMixin, TemplateView):
    """Gestión de inscripciones de laboratorio"""
    template_name = 'secretario/laboratorios/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtros de búsqueda
        curso_filtro = self.request.GET.get('curso')
        laboratorio_filtro = self.request.GET.get('laboratorio')
        estado_filtro = self.request.GET.get('estado')
        
        context.update({
            'inscripciones_laboratorio': ServicioMatricula.obtener_inscripciones_laboratorio(
                curso=curso_filtro,
                laboratorio=laboratorio_filtro,
                estado=estado_filtro
            ),
            'cursos_disponibles': ServicioMatricula.obtener_cursos_con_laboratorio(),
            'laboratorios_disponibles': ServicioReservas.obtener_todos_laboratorios(),
            'estadisticas_ocupacion': ServicioReservas.obtener_estadisticas_ocupacion()
        })
        return context

    def post(self, request, *args, **kwargs):
        """Gestionar inscripciones de laboratorio"""
        accion = request.POST.get('accion')
        inscripcion_id = request.POST.get('inscripcion_id')
        
        try:
            if accion == 'aprobar':
                ServicioMatricula.aprobar_inscripcion_laboratorio(inscripcion_id)
                messages.success(request, 'Inscripción aprobada exitosamente.')
            elif accion == 'rechazar':
                motivo = request.POST.get('motivo', 'Sin motivo especificado')
                ServicioMatricula.rechazar_inscripcion_laboratorio(inscripcion_id, motivo)
                messages.success(request, 'Inscripción rechazada.')
            elif accion == 'redistribuir':
                nuevo_laboratorio_id = request.POST.get('nuevo_laboratorio_id')
                ServicioMatricula.redistribuir_estudiante_laboratorio(inscripcion_id, nuevo_laboratorio_id)
                messages.success(request, 'Estudiante redistribuido exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al procesar la solicitud: {str(e)}')
        
        return redirect('secretario:laboratorios')


class SecretarioReportesView(SecretarioRequiredMixin, TemplateView):
    """Generación de reportes académicos"""
    template_name = 'secretario/reportes/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'tipos_reporte': [
                ('asistencia_general', 'Reporte de Asistencia General'),
                ('notas_por_curso', 'Reporte de Notas por Curso'),
                ('estadisticas_periodo', 'Estadísticas por Período'),
                ('ocupacion_laboratorios', 'Ocupación de Laboratorios'),
                ('rendimiento_academico', 'Rendimiento Académico')
            ],
            'periodos_academicos': ServicioReportes.obtener_periodos_disponibles(),
            'cursos_disponibles': ServicioReportes.obtener_cursos_disponibles(),
            'reportes_generados': ServicioReportes.obtener_reportes_recientes()
        })
        return context

    def post(self, request, *args, **kwargs):
        """Generar reportes académicos"""
        tipo_reporte = request.POST.get('tipo_reporte')
        formato = request.POST.get('formato', 'pdf')
        periodo_id = request.POST.get('periodo_id')
        curso_id = request.POST.get('curso_id')
        
        try:
            if tipo_reporte == 'asistencia_general':
                response = ServicioReportes.generar_reporte_asistencia_general(
                    periodo_id=periodo_id,
                    formato=formato
                )
            elif tipo_reporte == 'notas_por_curso':
                response = ServicioReportes.generar_reporte_notas_curso(
                    curso_id=curso_id,
                    periodo_id=periodo_id,
                    formato=formato
                )
            elif tipo_reporte == 'estadisticas_periodo':
                response = ServicioReportes.generar_estadisticas_periodo(
                    periodo_id=periodo_id,
                    formato=formato
                )
            elif tipo_reporte == 'ocupacion_laboratorios':
                response = ServicioReportes.generar_reporte_ocupacion_laboratorios(
                    periodo_id=periodo_id,
                    formato=formato
                )
            elif tipo_reporte == 'rendimiento_academico':
                response = ServicioReportes.generar_reporte_rendimiento_academico(
                    periodo_id=periodo_id,
                    formato=formato
                )
            else:
                messages.error(request, 'Tipo de reporte no válido.')
                return redirect('secretario:reportes')
            
            return response
            
        except Exception as e:
            messages.error(request, f'Error al generar reporte: {str(e)}')
            return redirect('secretario:reportes')


class SecretarioEstadisticasView(SecretarioRequiredMixin, TemplateView):
    """Vista de estadísticas académicas"""
    template_name = 'secretario/estadisticas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'estadisticas_matricula': ServicioMatricula.obtener_estadisticas_matricula(),
            'estadisticas_asistencia': ServicioReportes.obtener_estadisticas_asistencia(),
            'estadisticas_notas': ServicioReportes.obtener_estadisticas_notas(),
            'tendencias_academicas': ServicioReportes.obtener_tendencias_academicas(),
            'alertas_academicas': ServicioMonitoreo.obtener_alertas_detalladas()
        })
        return context