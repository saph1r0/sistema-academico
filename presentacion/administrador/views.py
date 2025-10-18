from django.views.generic import TemplateView, ListView, FormView
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.paginator import Paginator
from .mixins import AdminRequiredMixin, SecretariaOrAdminMixin
from servicios.servicioMetricas import ServicioMetricas
from repositorio.postgres_repository.models import UsuarioModel


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Vista principal del dashboard administrativo"""
    template_name = 'administrador/dashboard.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servicio_metricas = ServicioMetricas()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener métricas del sistema
            metricas = self.servicio_metricas.obtener_metricas_sistema()
            metricas_dashboard = metricas.obtener_metricas_dashboard()
            
            context.update({
                'page_title': 'Dashboard Administrativo',
                'metricas': metricas_dashboard,
                'alertas_pendientes': [
                    {
                        'tipo': alerta.tipo,
                        'titulo': alerta.titulo,
                        'descripcion': alerta.descripcion,
                        'prioridad': alerta.prioridad,
                        'fecha': alerta.fecha_creacion
                    }
                    for alerta in metricas.alertas_pendientes if not alerta.resuelto
                ],
                'tiene_alertas_criticas': metricas.tiene_alertas_criticas(),
                'porcentaje_usuarios_activos': metricas.obtener_porcentaje_usuarios_activos()
            })
            
        except Exception as e:
            # En caso de error, mostrar dashboard con datos por defecto
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
                'porcentaje_usuarios_activos': 0
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
        queryset = UsuarioModel.objects.all().order_by('apellido', 'nombre')
        
        # Filtro por rol
        rol_filter = self.request.GET.get('rol')
        if rol_filter and rol_filter != 'todos':
            queryset = queryset.filter(rol=rol_filter)
        
        # Filtro por estado (activo/inactivo)
        estado_filter = self.request.GET.get('estado')
        if estado_filter == 'activo':
            queryset = queryset.filter(activo=True)
        elif estado_filter == 'inactivo':
            queryset = queryset.filter(activo=False)
        
        # Búsqueda por texto
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(apellido__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Gestión de Usuarios',
            'roles_choices': UsuarioModel.ROLES,
            'current_filters': {
                'rol': self.request.GET.get('rol', 'todos'),
                'estado': self.request.GET.get('estado', 'todos'),
                'search': self.request.GET.get('search', '')
            },
            'total_usuarios': UsuarioModel.objects.count(),
            'usuarios_activos': UsuarioModel.objects.filter(activo=True).count(),
            'usuarios_inactivos': UsuarioModel.objects.filter(activo=False).count(),
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
                usuario.activar_usuario()
                message = f'Usuario {usuario.email} activado correctamente'
            elif action == 'desactivar':
                usuario.desactivar_usuario()
                message = f'Usuario {usuario.email} desactivado correctamente'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Acción no válida'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'user_status': usuario.activo
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
                usuario.activar_usuario()
                message = f'Usuario {usuario.email} activado correctamente'
            elif action == 'desactivar':
                usuario.desactivar_usuario()
                message = f'Usuario {usuario.email} desactivado correctamente'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Acción no válida'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': message,
                'user_status': usuario.activo,
                'user_email': usuario.email
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reportes Globales'
        return context


class AdminRecursosView(AdminRequiredMixin, TemplateView):
    """Vista para consulta de laboratorios y recursos"""
    template_name = 'administrador/recursos/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Recursos y Laboratorios'
        return context


class AdminConfiguracionView(AdminRequiredMixin, FormView):
    """Vista para configuración de parámetros del sistema"""
    template_name = 'administrador/configuracion/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Configuración del Sistema'
        return context