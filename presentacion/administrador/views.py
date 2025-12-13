from django.views.generic import TemplateView, ListView, FormView
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import get_template
from xhtml2pdf import pisa
from .mixins import AdminRequiredMixin, SecretariaOrAdminMixin
from servicios.servicioMetricas import ServicioMetricas
from servicios.servicioMonitoreo import ServicioMonitoreo
from repositorio.postgres_repository.models import UsuarioModel, LaboratorioModel
from datetime import datetime, timedelta
import logging
from repositorio.postgres_repository.models import UsuarioModel, LaboratorioModel, User


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Vista principal del dashboard administrativo"""
    template_name = 'administrador/dashboard.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servicio_metricas = ServicioMetricas()
        self.servicio_monitoreo = ServicioMonitoreo()
        self.logger = logging.getLogger('admin_panel.dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Registrar acceso al dashboard en auditoría
            self.servicio_monitoreo.registrar_accion_administrativa(
                usuario_id=str(self.request.user.id),
                usuario_nombre=f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.username,
                accion="consulta_realizada",
                descripcion="Acceso al dashboard administrativo",
                entidad_afectada="Dashboard",
                contexto_request={
                    'ip': self.request.META.get('REMOTE_ADDR', ''),
                    'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
                    'session_id': self.request.session.session_key or ''
                }
            )
            
            # Obtener métricas básicas del sistema
            metricas = self.servicio_metricas.obtener_metricas_sistema()
            metricas_dashboard = metricas.obtener_metricas_dashboard()
            
            # Obtener estado completo del sistema de monitoreo
            estado_sistema = self.servicio_monitoreo.obtener_estado_sistema()
            
            # Obtener alertas para el dashboard
            alertas_dashboard = self.servicio_monitoreo.obtener_alertas_dashboard(limite=5)
            
            # Obtener métricas de rendimiento
            metricas_rendimiento = self.servicio_monitoreo.obtener_metricas_rendimiento_dashboard()
            
            # Simular métricas de rendimiento para demo (remover en producción)
            self.servicio_monitoreo.simular_metricas_rendimiento()
            
            context.update({
                'page_title': 'Dashboard Administrativo',
                'metricas': metricas_dashboard,
                
                # Alertas del sistema
                'alertas_pendientes': alertas_dashboard,
                'tiene_alertas_criticas': estado_sistema.get('alertas', {}).get('criticas', 0) > 0,
                'total_alertas_activas': estado_sistema.get('alertas', {}).get('total_activas', 0),
                
                # Estado general del sistema
                'estado_general': estado_sistema.get('estado_general', 'desconocido'),
                'estado_sistema': estado_sistema,
                
                # Métricas de rendimiento
                'metricas_rendimiento': metricas_rendimiento.get('metricas', [])[:4],  # Top 4 métricas
                'estado_rendimiento': metricas_rendimiento.get('estado_general', 'optimo'),
                'porcentaje_saludable': metricas_rendimiento.get('porcentaje_saludable', 100),
                'alertas_rendimiento': metricas_rendimiento.get('alertas_rendimiento', []),
                
                # Inconsistencias detectadas
                'inconsistencias_activas': estado_sistema.get('inconsistencias', {}).get('total_activas', 0),
                'inconsistencias_por_severidad': estado_sistema.get('inconsistencias', {}).get('por_severidad', {}),
                'ultima_deteccion': estado_sistema.get('inconsistencias', {}).get('ultima_deteccion'),
                
                # Auditoría
                'auditoria_stats': estado_sistema.get('auditoria', {}),
                
                # Métricas adicionales
                'porcentaje_usuarios_activos': metricas.obtener_porcentaje_usuarios_activos(),
                'timestamp_actualizacion': estado_sistema.get('timestamp')
            })
            
        except Exception as e:
            # En caso de error, mostrar dashboard con datos por defecto
            self.logger.error(f'Error al cargar dashboard: {str(e)}')
            messages.error(self.request, f'Error al cargar métricas del sistema: {str(e)}')
            context.update({
                'page_title': 'Dashboard Administrativo',
                'metricas': {
                    'usuarios_activos': 0,
                    'cursos_activos': 0,
                    'promedio_asistencia': 0,
                    'promedio_notas': 0,
                    'alertas_pendientes': 0,
                    'alertas_criticas': 0,
                    'usuarios_por_rol': {},
                    'actividad_reciente': {}
                },
                'alertas_pendientes': [],
                'tiene_alertas_criticas': False,
                'porcentaje_usuarios_activos': 0,
                'estado_general': 'error',
                'metricas_rendimiento': [],
                'estado_rendimiento': 'critico',
                'porcentaje_saludable': 0,
                'alertas_rendimiento': [],
                'inconsistencias_activas': 0,
                'inconsistencias_por_severidad': {},
                'auditoria_stats': {}
            })
        
        return context


@method_decorator(cache_page(300), name='dispatch')  # Cache por 5 minutos
class AdminDashboardAPIView(AdminRequiredMixin, TemplateView):
    """API endpoint para obtener métricas del dashboard via AJAX"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servicio_metricas = ServicioMetricas()
    
    def get(self, request, *args, **kwargs):
        """Retorna métricas del dashboard en formato JSON"""
        try:
            metricas_json = self.servicio_metricas.obtener_metricas_dashboard_json()
            return JsonResponse({
                'success': True,
                'data': metricas_json,
                'timestamp': self.servicio_metricas._ultima_actualizacion.isoformat() if self.servicio_metricas._ultima_actualizacion else None
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class AdminUsuariosView(AdminRequiredMixin, ListView):
    """Vista para gestión de usuarios del sistema"""
    template_name = 'administrador/usuarios/lista.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtiene la lista de usuarios con filtros aplicados"""
        queryset = UsuarioModel.objects.all().order_by('last_name', 'first_name')
        
        # Filtro por rol
        rol_filter = self.request.GET.get('rol')
        if rol_filter and rol_filter != 'todos':
            queryset = queryset.filter(role=rol_filter)
        
        # Filtro por estado (activo/inactivo)
        estado_filter = self.request.GET.get('estado')
        if estado_filter == 'activo':
            queryset = queryset.filter(is_active=True)
        elif estado_filter == 'inactivo':
            queryset = queryset.filter(is_active=False)
        
        # Búsqueda por texto
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(institutional_email__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Gestión de Usuarios',
            'roles_choices': UsuarioModel.ROLE_CHOICES,
            'current_filters': {
                'rol': self.request.GET.get('rol', 'todos'),
                'estado': self.request.GET.get('estado', 'todos'),
                'search': self.request.GET.get('search', '')
            },
            'total_usuarios': UsuarioModel.objects.count(),
            'usuarios_activos': UsuarioModel.objects.filter(is_active=True).count(),
            'usuarios_inactivos': UsuarioModel.objects.filter(is_active=False).count(),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Maneja las acciones de activación/desactivación de usuarios"""
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if not action or not user_id:
            return JsonResponse({
                'success': False,
                'error': 'Acción o ID de usuario no especificado'
            }, status=400)
        
        try:
            usuario = UsuarioModel.objects.get(id=user_id)
            
            # Prevenir que el admin se desactive a sí mismo
            if usuario.id == request.user.id and action == 'desactivar':
                return JsonResponse({
                    'success': False,
                    'error': 'No puedes desactivar tu propia cuenta'
                }, status=400)
            
            if action == 'activar':
                usuario.is_active = True
                usuario.save()
                message = f'Usuario {usuario.institutional_email} activado correctamente'
            elif action == 'desactivar':
                usuario.is_active = False
                usuario.save()
                message = f'Usuario {usuario.institutional_email} desactivado correctamente'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Acción no válida'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'user_status': usuario.is_active
            })
            
        except UsuarioModel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar la acción: {str(e)}'
            }, status=500)


class AdminUsuariosAPIView(AdminRequiredMixin, TemplateView):
    """API endpoint para operaciones AJAX de usuarios"""
    
    def post(self, request, *args, **kwargs):
        """Maneja las acciones de activación/desactivación de usuarios via AJAX"""
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if not action or not user_id:
            return JsonResponse({
                'success': False,
                'error': 'Acción o ID de usuario no especificado'
            }, status=400)
        
        try:
            usuario = UsuarioModel.objects.get(id=user_id)
            
            # Prevenir que el admin se desactive a sí mismo
            if usuario.id == request.user.id and action == 'desactivar':
                return JsonResponse({
                    'success': False,
                    'error': 'No puedes desactivar tu propia cuenta'
                }, status=400)
            
            if action == 'activar':
                usuario.is_active = True
                usuario.save()
                message = f'Usuario {usuario.institutional_email} activado correctamente'
            elif action == 'desactivar':
                usuario.is_active = False
                usuario.save()
                message = f'Usuario {usuario.institutional_email} desactivado correctamente'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Acción no válida'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'user_status': usuario.is_active,
                'user_email': usuario.institutional_email
            })
            
        except UsuarioModel.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al procesar la acción: {str(e)}'
            }, status=500)


class AdminReportesView(AdminRequiredMixin, TemplateView):
    """Vista para generación de reportes globales"""
    template_name = 'administrador/reportes/index.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from servicios.servicioReportes import ServicioReportes
        self.servicio_reportes = ServicioReportes()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import ReporteAsistenciaForm, ReporteNotasForm, ReporteEstadisticasForm
        
        context.update({
            'page_title': 'Reportes Globales',
            'form_asistencia': ReporteAsistenciaForm(),
            'form_notas': ReporteNotasForm(),
            'form_estadisticas': ReporteEstadisticasForm(),
        })
        return context
    
    def _render_pdf(self, template_src, context_dict, filename='reporte.pdf'):
        """Función auxiliar para generar PDF"""
        template = get_template(template_src)
        html = template.render(context_dict)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Crear PDF
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse(f'Ocurrió un error generando el PDF: {pisa_status.err}')
            
        return response
    
    def post(self, request, *args, **kwargs):
        """Maneja la generación de reportes según el tipo solicitado"""
        from .forms import ReporteAsistenciaForm, ReporteNotasForm, ReporteEstadisticasForm
        from servicios.servicioReportes import ReporteGeneracionException
        
        categoria = request.POST.get('categoria_reporte')
        
        try:
            if categoria == 'asistencia':
                return self._generar_reporte_asistencia(request)
            elif categoria == 'notas':
                from .forms import ReporteNotasForm  # Importación local
                from servicios.servicioReporteNotas import ServicioReporteNotas
            
                form = ReporteNotasForm(request.POST)

                if form.is_valid():
                    filtros = form.cleaned_data
                    servicio = ServicioReporteNotas()
                
                    data_pdf = servicio.generar_data_reporte_oficial(filtros)
                
                    if not data_pdf or not data_pdf.get('tablas'):
                        messages.warning(request, "No se encontraron registros con los filtros seleccionados.")
                        return redirect('administrador:reportes')

                    return self._render_pdf('administrador/reportes/acta_notas.html', {
                    'reporte': data_pdf,
                    'headers': ['CUI', 'ALUMNO', 'NOTA FINAL', 'ESTADO']
                }, filename=f"Reporte_Notas_{filtros['tipo_reporte']}.pdf")
            
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                    return redirect('administrador:reportes')
            
            elif categoria == 'estadisticas':
                return self._generar_reporte_estadisticas(request)
            else:
                messages.error(request, 'Tipo de reporte no válido.')
                return redirect('admin:reportes')
                
        except ReporteGeneracionException as e:
            messages.error(request, f'Error generando reporte: {str(e)}')
            return redirect('admin:reportes')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
            return redirect('administrador:reportes')
    
    def _generar_reporte_asistencia(self, request):
        """Genera reporte de asistencia"""
        from .forms import ReporteAsistenciaForm
        
        form = ReporteAsistenciaForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            formato = form.cleaned_data['formato']
            incluir_detalle = form.cleaned_data['incluir_detalle']
            
            return self.servicio_reportes.generar_reporte_asistencia_global(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                formato=formato,
                incluir_detalle=incluir_detalle
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('admin:reportes')
    
    def _generar_reporte_notas(self, request):
        """Genera reporte de notas"""
        from .forms import ReporteNotasForm
        
        form = ReporteNotasForm(request.POST)
        if form.is_valid():
            ciclo = form.cleaned_data['ciclo']
            tipo_reporte = form.cleaned_data['tipo_reporte']
            curso_codigo = form.cleaned_data.get('curso_codigo')
            docente_email = form.cleaned_data.get('docente_email')
            formato = form.cleaned_data['formato']
            incluir_estadisticas = form.cleaned_data['incluir_estadisticas']
            
            return self.servicio_reportes.generar_reporte_notas_global(
                ciclo=ciclo,
                tipo_reporte=tipo_reporte,
                curso_codigo=curso_codigo,
                docente_email=docente_email,
                formato=formato,
                incluir_estadisticas=incluir_estadisticas
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('admin:reportes')
    
    def _generar_reporte_estadisticas(self, request):
        """Genera reporte de estadísticas"""
        from .forms import ReporteEstadisticasForm
        
        form = ReporteEstadisticasForm(request.POST)
        if form.is_valid():
            periodo = form.cleaned_data['periodo']
            fecha_inicio = form.cleaned_data.get('fecha_inicio')
            fecha_fin = form.cleaned_data.get('fecha_fin')
            formato = form.cleaned_data['formato']
            incluir_graficos = form.cleaned_data['incluir_graficos']
            
            return self.servicio_reportes.generar_reporte_estadisticas_global(
                periodo=periodo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                formato=formato,
                incluir_graficos=incluir_graficos
            )
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('admin:reportes')


class AdminRecursosView(AdminRequiredMixin, TemplateView):
    """Vista para consulta de laboratorios y recursos"""
    template_name = 'administrador/recursos/index.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from servicios.servicioReservas import ServicioReservaAmbientes
        self.servicio_reservas = ServicioReservaAmbientes()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener laboratorios activos con estadísticas
            laboratorios = self.servicio_reservas.obtener_laboratorios_activos()
            
            # Obtener reservas recientes
            reservas_recientes = self.servicio_reservas.obtener_reservas_recientes(dias=7)
            
            # Obtener conflictos activos
            conflictos = self.servicio_reservas.obtener_conflictos_activos()
            
            # Obtener estadísticas de uso
            estadisticas = self.servicio_reservas.obtener_estadisticas_uso()
            
            # Calcular métricas adicionales
            total_laboratorios = laboratorios.count()
            laboratorios_con_reservas = laboratorios.filter(total_reservas__gt=0).count()
            tasa_utilizacion = (laboratorios_con_reservas / total_laboratorios * 100) if total_laboratorios > 0 else 0
            
            context.update({
                'page_title': 'Recursos y Laboratorios',
                'laboratorios': laboratorios,
                'reservas_recientes': reservas_recientes[:10],  # Últimas 10 reservas
                'conflictos_activos': conflictos,
                'estadisticas': estadisticas,
                'metricas_resumen': {
                    'total_laboratorios': total_laboratorios,
                    'laboratorios_activos': laboratorios.filter(activo=True).count(),
                    'reservas_pendientes': sum(lab.reservas_pendientes for lab in laboratorios),
                    'reservas_aprobadas': sum(lab.reservas_aprobadas for lab in laboratorios),
                    'conflictos_detectados': len(conflictos),
                    'tasa_utilizacion': round(tasa_utilizacion, 1),
                    'tasa_aprobacion_automatica': round(estadisticas.get('tasa_aprobacion_automatica', 0), 1)
                },
                'tipos_laboratorio': dict(LaboratorioModel.TIPOS_LABORATORIO),
                'estados_reserva': dict(ReservaModel.ESTADOS_RESERVA),
                'tiene_conflictos': len(conflictos) > 0,
                'alertas_recursos': self._generar_alertas_recursos(laboratorios, conflictos, estadisticas)
            })
            
        except Exception as e:
            # En caso de error, mostrar vista con datos por defecto
            messages.error(self.request, f'Error al cargar información de recursos: {str(e)}')
            context.update({
                'page_title': 'Recursos y Laboratorios',
                'laboratorios': [],
                'reservas_recientes': [],
                'conflictos_activos': [],
                'estadisticas': {},
                'metricas_resumen': {
                    'total_laboratorios': 0,
                    'laboratorios_activos': 0,
                    'reservas_pendientes': 0,
                    'reservas_aprobadas': 0,
                    'conflictos_detectados': 0,
                    'tasa_utilizacion': 0,
                    'tasa_aprobacion_automatica': 0
                },
                'tipos_laboratorio': {},
                'estados_reserva': {},
                'tiene_conflictos': False,
                'alertas_recursos': []
            })
        
        return context
    
    def _generar_alertas_recursos(self, laboratorios, conflictos, estadisticas):
        """Genera alertas basadas en el estado de los recursos"""
        alertas = []
        
        # Alerta por conflictos activos
        if conflictos:
            alertas.append({
                'tipo': 'error',
                'titulo': 'Conflictos de Reservas Detectados',
                'descripcion': f'Se encontraron {len(conflictos)} conflictos en las reservas actuales.',
                'accion': 'Revisar y resolver conflictos',
                'prioridad': 'alta'
            })
        
        # Alerta por laboratorios sin uso
        laboratorios_sin_uso = laboratorios.filter(total_reservas=0)
        if laboratorios_sin_uso.exists():
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Laboratorios Sin Uso',
                'descripcion': f'{laboratorios_sin_uso.count()} laboratorios no tienen reservas registradas.',
                'accion': 'Verificar disponibilidad y promoción',
                'prioridad': 'media'
            })
        
        # Alerta por alta demanda
        laboratorios_alta_demanda = laboratorios.filter(reservas_pendientes__gte=5)
        if laboratorios_alta_demanda.exists():
            alertas.append({
                'tipo': 'info',
                'titulo': 'Alta Demanda de Laboratorios',
                'descripcion': f'{laboratorios_alta_demanda.count()} laboratorios tienen 5 o más reservas pendientes.',
                'accion': 'Considerar optimización de horarios',
                'prioridad': 'media'
            })
        
        # Alerta por baja tasa de aprobación automática
        tasa_aprobacion = estadisticas.get('tasa_aprobacion_automatica', 0)
        if tasa_aprobacion < 70:
            alertas.append({
                'tipo': 'warning',
                'titulo': 'Baja Tasa de Aprobación Automática',
                'descripcion': f'Solo el {tasa_aprobacion:.1f}% de las reservas se aprueban automáticamente.',
                'accion': 'Revisar políticas de reservas',
                'prioridad': 'media'
            })
        
        return alertas


class AdminConfiguracionView(AdminRequiredMixin, FormView):
    """Vista para configuración de parámetros del sistema"""
    template_name = 'administrador/configuracion/index.html'
    form_class = None  # Will be imported from forms
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Import here to avoid circular imports
        from .forms import ConfiguracionSistemaForm
        self.form_class = ConfiguracionSistemaForm
        from dominio.modelo.admin_sistema.configuracion_sistema import ConfiguracionSistema
        self.configuracion_sistema = ConfiguracionSistema()
        self.logger = logging.getLogger('admin_panel.configuracion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener configuración actual
            configuracion_actual = self.configuracion_sistema.obtener_configuracion_actual()
            
            context.update({
                'page_title': 'Configuración del Sistema',
                'configuracion_actual': configuracion_actual,
                'parametros_criticos': [
                    'capacidad_maxima_laboratorio',
                    'tiempo_sesion_minutos',
                    'backup_automatico'
                ],
                'ultima_modificacion': configuracion_actual.get('fecha_modificacion'),
                'usuario_modificacion': configuracion_actual.get('usuario_modificacion')
            })
            
        except Exception as e:
            self.logger.error(f'Error al cargar configuración: {str(e)}')
            messages.error(self.request, f'Error al cargar la configuración del sistema: {str(e)}')
            context.update({
                'page_title': 'Configuración del Sistema',
                'configuracion_actual': {},
                'parametros_criticos': [],
                'error_carga': True
            })
        
        return context
    
    def get_initial(self):
        """Obtiene los valores iniciales del formulario"""
        try:
            configuracion_actual = self.configuracion_sistema.obtener_configuracion_actual()
            return {
                'capacidad_maxima_laboratorio': configuracion_actual.get('capacidad_maxima_laboratorio', 30),
                'tiempo_sesion_minutos': configuracion_actual.get('tiempo_sesion_minutos', 120),
                'backup_automatico': configuracion_actual.get('backup_automatico', True),
                'frecuencia_backup_horas': configuracion_actual.get('frecuencia_backup_horas', 24),
                'alertas_activas': configuracion_actual.get('alertas_activas', True)
            }
        except Exception as e:
            self.logger.error(f'Error al obtener configuración inicial: {str(e)}')
            return {}
    
    def form_valid(self, form):
        """Procesa el formulario válido"""
        try:
            # Obtener datos del formulario
            parametros = form.cleaned_data
            
            # Validar parámetros
            errores = self.configuracion_sistema.validar_parametros(parametros)
            if errores:
                for error in errores:
                    form.add_error(None, error)
                return self.form_invalid(form)
            
            # Verificar si hay parámetros críticos que requieren confirmación
            parametros_criticos_modificados = []
            for param, valor in parametros.items():
                if self.configuracion_sistema.es_parametro_critico(param):
                    parametros_criticos_modificados.append(param)
            
            # Si hay parámetros críticos y no se ha confirmado, solicitar confirmación
            if parametros_criticos_modificados and not self.request.POST.get('confirmar_cambios'):
                messages.warning(
                    self.request,
                    f'Los siguientes parámetros son críticos: {", ".join(parametros_criticos_modificados)}. '
                    'Confirme los cambios para continuar.'
                )
                context = self.get_context_data(form=form)
                context['requiere_confirmacion'] = True
                context['parametros_criticos_modificados'] = parametros_criticos_modificados
                return self.render_to_response(context)
            
            # Actualizar configuración
            resultado = self.configuracion_sistema.actualizar_configuracion(
                parametros, 
                str(self.request.user.id)
            )
            
            if resultado:
                # Registrar acción en auditoría
                from servicios.servicioMonitoreo import ServicioMonitoreo
                servicio_monitoreo = ServicioMonitoreo()
                servicio_monitoreo.registrar_accion_administrativa(
                    usuario_id=str(self.request.user.id),
                    usuario_nombre=f"{self.request.user.first_name} {self.request.user.last_name}".strip() or self.request.user.institutional_email,
                    accion="configuracion_actualizada",
                    descripcion=f"Actualización de configuración del sistema: {', '.join(parametros.keys())}",
                    entidad_afectada="ConfiguracionSistema",
                    contexto_request={
                        'parametros_modificados': list(parametros.keys()),
                        'valores_anteriores': self.get_initial(),
                        'valores_nuevos': parametros,
                        'ip': self.request.META.get('REMOTE_ADDR', ''),
                        'user_agent': self.request.META.get('HTTP_USER_AGENT', '')
                    }
                )
                
                messages.success(
                    self.request,
                    'Configuración del sistema actualizada correctamente.'
                )
                
                # Log de la acción
                self.logger.info(
                    f'Configuración actualizada por usuario {self.request.user.institutional_email}: '
                    f'{", ".join(parametros.keys())}'
                )
                
            else:
                messages.error(
                    self.request,
                    'Error al actualizar la configuración del sistema.'
                )
            
            return super().form_valid(form)
            
        except Exception as e:
            self.logger.error(f'Error al procesar configuración: {str(e)}')
            messages.error(
                self.request,
                f'Error al procesar la configuración: {str(e)}'
            )
            return self.form_invalid(form)
    
    def get_success_url(self):
        """URL de redirección después del éxito"""
        return self.request.path


class AdminMonitoreoView(AdminRequiredMixin, TemplateView):
    """Vista para el sistema de monitoreo y supervisión"""
    template_name = 'administrador/monitoreo/index.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servicio_monitoreo = ServicioMonitoreo()
        self.logger = logging.getLogger('admin_panel.monitoreo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener estado completo del sistema
            estado_sistema = self.servicio_monitoreo.obtener_estado_sistema()
            
            # Obtener alertas activas
            alertas_activas = self.servicio_monitoreo.obtener_alertas_dashboard(limite=20)
            
            # Obtener métricas de rendimiento detalladas
            metricas_rendimiento = self.servicio_monitoreo.obtener_metricas_rendimiento_dashboard()
            
            # Obtener historial de auditoría reciente
            historial_auditoria = self.servicio_monitoreo.obtener_historial_auditoria(
                filtros={'fecha_inicio': datetime.now() - timedelta(days=7)},
                limite=50
            )
            
            context.update({
                'page_title': 'Sistema de Monitoreo',
                'estado_sistema': estado_sistema,
                'alertas_activas': alertas_activas,
                'metricas_rendimiento': metricas_rendimiento,
                'historial_auditoria': historial_auditoria,
                'puede_ejecutar_deteccion': not self.servicio_monitoreo.deteccion_en_progreso,
                'ultima_deteccion': estado_sistema.get('inconsistencias', {}).get('ultima_deteccion'),
                'configuracion_monitoreo': self.servicio_monitoreo.configuracion
            })
            
        except Exception as e:
            self.logger.error(f'Error cargando vista de monitoreo: {str(e)}')
            messages.error(self.request, f'Error al cargar sistema de monitoreo: {str(e)}')
            context.update({
                'page_title': 'Sistema de Monitoreo',
                'estado_sistema': {'estado_general': 'error'},
                'alertas_activas': [],
                'metricas_rendimiento': {'metricas': [], 'estado_general': 'critico'},
                'historial_auditoria': [],
                'puede_ejecutar_deteccion': False,
                'ultima_deteccion': None,
                'configuracion_monitoreo': {}
            })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Maneja acciones del sistema de monitoreo"""
        accion = request.POST.get('accion')
        
        try:
            if accion == 'ejecutar_deteccion':
                return self._ejecutar_deteccion_inconsistencias(request)
            elif accion == 'resolver_alerta':
                return self._resolver_alerta(request)
            elif accion == 'simular_metricas':
                return self._simular_metricas_rendimiento(request)
            else:
                messages.error(request, 'Acción no válida.')
                return redirect('admin:monitoreo')
                
        except Exception as e:
            self.logger.error(f'Error ejecutando acción de monitoreo: {str(e)}')
            messages.error(request, f'Error ejecutando acción: {str(e)}')
            return redirect('admin:monitoreo')
    
    def _ejecutar_deteccion_inconsistencias(self, request):
        """Ejecuta detección manual de inconsistencias"""
        resultado = self.servicio_monitoreo.ejecutar_deteccion_completa()
        
        if 'error' in resultado:
            messages.error(request, f'Error en detección: {resultado["error"]}')
        else:
            total = resultado.get('total_inconsistencias', 0)
            criticas = resultado.get('inconsistencias_criticas', 0)
            
            if total == 0:
                messages.success(request, 'Detección completada: No se encontraron inconsistencias.')
            else:
                messages.warning(request, 
                    f'Detección completada: {total} inconsistencias encontradas '
                    f'({criticas} críticas).')
        
        return redirect('admin:monitoreo')
    
    def _resolver_alerta(self, request):
        """Resuelve una alerta específica"""
        alerta_id = request.POST.get('alerta_id')
        accion_correctiva = request.POST.get('accion_correctiva', '')
        notas = request.POST.get('notas', '')
        
        if not alerta_id:
            messages.error(request, 'ID de alerta no especificado.')
            return redirect('admin:monitoreo')
        
        usuario_nombre = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        
        resultado = self.servicio_monitoreo.resolver_alerta(
            alerta_id=alerta_id,
            usuario=usuario_nombre,
            accion=accion_correctiva,
            notas=notas
        )
        
        if resultado:
            messages.success(request, f'Alerta {alerta_id} resuelta correctamente.')
        else:
            messages.error(request, f'No se pudo resolver la alerta {alerta_id}.')
        
        return redirect('admin:monitoreo')
    
    def _simular_metricas_rendimiento(self, request):
        """Simula métricas de rendimiento para testing"""
        self.servicio_monitoreo.simular_metricas_rendimiento()
        messages.info(request, 'Métricas de rendimiento simuladas correctamente.')
        return redirect('admin:monitoreo')


class AdminMonitoreoAPIView(AdminRequiredMixin, TemplateView):
    """API endpoints para el sistema de monitoreo"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servicio_monitoreo = ServicioMonitoreo()
        self.logger = logging.getLogger('admin_panel.monitoreo_api')
    
    def get(self, request, *args, **kwargs):
        """Obtiene datos del sistema de monitoreo via AJAX"""
        endpoint = kwargs.get('endpoint', 'estado')
        
        try:
            if endpoint == 'estado':
                data = self.servicio_monitoreo.obtener_estado_sistema()
            elif endpoint == 'alertas':
                data = self.servicio_monitoreo.obtener_alertas_dashboard(limite=10)
            elif endpoint == 'metricas':
                data = self.servicio_monitoreo.obtener_metricas_rendimiento_dashboard()
            elif endpoint == 'auditoria':
                filtros = {
                    'fecha_inicio': datetime.now() - timedelta(days=int(request.GET.get('dias', 7)))
                }
                data = self.servicio_monitoreo.obtener_historial_auditoria(
                    filtros=filtros,
                    limite=int(request.GET.get('limite', 20))
                )
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Endpoint no válido'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f'Error en API de monitoreo: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request, *args, **kwargs):
        """Ejecuta acciones del sistema de monitoreo via AJAX"""
        accion = request.POST.get('accion')
        
        try:
            if accion == 'ejecutar_deteccion':
                resultado = self.servicio_monitoreo.ejecutar_deteccion_completa()
                return JsonResponse({
                    'success': 'error' not in resultado,
                    'data': resultado
                })
            
            elif accion == 'resolver_alerta':
                alerta_id = request.POST.get('alerta_id')
                accion_correctiva = request.POST.get('accion_correctiva', '')
                notas = request.POST.get('notas', '')
                
                if not alerta_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'ID de alerta requerido'
                    }, status=400)
                
                usuario_nombre = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                
                resultado = self.servicio_monitoreo.resolver_alerta(
                    alerta_id=alerta_id,
                    usuario=usuario_nombre,
                    accion=accion_correctiva,
                    notas=notas
                )
                
                return JsonResponse({
                    'success': resultado,
                    'message': 'Alerta resuelta correctamente' if resultado else 'Error resolviendo alerta'
                })
            
            elif accion == 'simular_metricas':
                self.servicio_monitoreo.simular_metricas_rendimiento()
                return JsonResponse({
                    'success': True,
                    'message': 'Métricas simuladas correctamente'
                })
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Acción no válida'
                }, status=400)
                
        except Exception as e:
            self.logger.error(f'Error ejecutando acción de monitoreo: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)