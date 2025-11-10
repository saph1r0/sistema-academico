"""
URLs para el módulo de estudiantes
"""
from django.urls import path
from . import views

app_name = 'estudiante'

urlpatterns = [
    path('dashboard/', views.EstudianteDashboardView.as_view(), name='dashboard'),
    path('curso/<uuid:course_id>/', views.EstudianteCursoDetalleView.as_view(), name='curso_detalle'),
    path('laboratorios/', views.EstudianteLaboratoriosView.as_view(), name='laboratorios'),
    path('notas/', views.EstudianteNotasView.as_view(), name='notas'),
    path('horarios/', views.EstudianteHorarioView.as_view(), name='horarios'),
    path('cursos/', views.cursos, name='cursos'),
    
]