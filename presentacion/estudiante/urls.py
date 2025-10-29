"""
URLs para el módulo de estudiantes
"""
from django.urls import path
from . import views

app_name = 'estudiante'

urlpatterns = [
    path('dashboard/', views.EstudianteDashboardView.as_view(), name='dashboard'),
    path('laboratorios/', views.EstudianteLaboratoriosView.as_view(), name='laboratorios'),
    path('notas/', views.EstudianteNotasView.as_view(), name='notas'),
    path('horarios/', views.EstudianteHorarioView.as_view(), name='horarios'),
]