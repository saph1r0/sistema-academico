from django.urls import path
from . import views
from . import views_reservas
from . import views_asistencia_estudiantes
from .views_asistencia_profesor_admin import AdminAsistenciaProfesorView

from . import views_notas_estudiantes
app_name = 'admin'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('dashboard/api/', views.AdminDashboardAPIView.as_view(), name='dashboard_api'),
    
    # Gestión de usuarios
    path('usuarios/', views.AdminUsuariosView.as_view(), name='usuarios'),
    path('usuarios/api/', views.AdminUsuariosAPIView.as_view(), name='usuarios_api'),
    
    # Reportes
    path('reportes/', views.AdminReportesView.as_view(), name='reportes'),

    #NotasWa
    path('notas-estudiantes/', views_notas_estudiantes.AdminNotasEstudiantesView.as_view(), name='notas_estudiantes'),
    path('api/notas-estudiantes/alumnos/', views_notas_estudiantes.AdminNotasAlumnosAPIView.as_view(), name='api_notas_alumnos'),
    
    # Recursos y laboratorios
    #path('recursos/', views.AdminRecursosView.as_view(), name='recursos'),

     # RESERVAS
    path('reservas/', views_reservas.dashboard_reservas, name='reservas_dashboard'),
    path('reservas/api/dia/', views_reservas.api_reservas_del_dia, name='api_reservas_dia'),
    path('reservas/api/validar/', views_reservas.api_validar_restricciones, name='api_validar_restricciones'),
    path('reservas/api/filtrar/', views_reservas.api_reservas_por_filtro, name='api_reservas_filtrar'),
    path('reservas/api/cancelar/<uuid:reserva_id>/', views_reservas.api_cancelar_reserva, name='api_cancelar_reserva'),

    path("asistencia-profesor/", AdminAsistenciaProfesorView.as_view(), name="asistencia_profesor"),
    #ASISTENCIA ESTUDIANTES
    path('asistencia/', views_asistencia_estudiantes.dashboard_asistencia, name='dashboard_asistencia'),
    path('asistencia/curso/<uuid:curso_id>/', views_asistencia_estudiantes.reporte_por_curso, name='reporte_curso'),
    path('asistencia/estudiante/<uuid:estudiante_id>/', views_asistencia_estudiantes.reporte_por_estudiante, name='reporte_estudiante'),
    path('asistencia/riesgo/', views_asistencia_estudiantes.estudiantes_en_riesgo, name='estudiantes_riesgo'),
    
    # Sistema de monitoreo y supervisión
    path('monitoreo/', views.AdminMonitoreoView.as_view(), name='monitoreo'),
    path('monitoreo/api/<str:endpoint>/', views.AdminMonitoreoAPIView.as_view(), name='monitoreo_api'),
    
    # Configuración del sistema
    path('configuracion/', views.AdminConfiguracionView.as_view(), name='configuracion'),
]