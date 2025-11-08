"""
URLs para el módulo de profesores
"""
from django.urls import path
from . import views

app_name = 'profesor'

urlpatterns = [
    path('dashboard/', views.ProfesorDashboardView.as_view(), name='dashboard'),
    path('notas/', views.ProfesorNotasView.as_view(), name='notas'),
    path('asistencia/', views.ProfesorAsistenciaView.as_view(), name='asistencia'),
    path('reservas/', views.ProfesorReservasView.as_view(), name='reservas'),
    path('silabo/', views.ProfesorSilaboView.as_view(), name='silabo'),
]
