"""
URLs para el módulo de estudiantes
"""
from django.urls import path
from . import views
from .views_horario import (
    StudentScheduleView,
    GetStudentScheduleView,
    GetEnrolledLaboratoriesView,
    CheckScheduleConflictView,
)

app_name = 'estudiante'

urlpatterns = [
    path('dashboard/', views.EstudianteDashboardView.as_view(), name='dashboard'),
    path('curso/<uuid:course_id>/', views.EstudianteCursoDetalleView.as_view(), name='curso_detalle'),
    path('laboratorios/', views.EstudianteLaboratoriosView.as_view(), name='laboratorios'),
    path('notas/', views.EstudianteNotasView.as_view(), name='notas'),
    #path('horarios/', views.EstudianteHorarioView.as_view(), name='horarios'),
    path("horarios/", StudentScheduleView.as_view(), name="horarios"),
    path("api/horario/", GetStudentScheduleView.as_view(), name="api_horario"),
    path("api/laboratorios/", GetEnrolledLaboratoriesView.as_view(), name="api_labs"),
    path("api/conflictos/", CheckScheduleConflictView.as_view(), name="api_conflictos"),
    path('cursos/', views.cursos, name='cursos'),
    
]