from django.urls import path
from . import views

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
    
    # Recursos y laboratorios
    path('recursos/', views.AdminRecursosView.as_view(), name='recursos'),
    
    # Configuración del sistema
    path('configuracion/', views.AdminConfiguracionView.as_view(), name='configuracion'),
]