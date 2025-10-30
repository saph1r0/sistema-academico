"""
URLs para el módulo de secretarios
"""
from django.urls import path
from . import views

app_name = 'secretario'

urlpatterns = [
    path('dashboard/', views.SecretarioDashboardView.as_view(), name='dashboard'),
    path('profesores/', views.SecretarioProfesoresView.as_view(), name='profesores'),
    path('laboratorios/', views.SecretarioLaboratoriosView.as_view(), name='laboratorios'),
    path('reportes/', views.SecretarioReportesView.as_view(), name='reportes'),
    path('estadisticas/', views.SecretarioEstadisticasView.as_view(), name='estadisticas'),
]