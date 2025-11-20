"""
URLs para el módulo de estudiantes
VERSIÓN CORREGIDA - Sin duplicados
"""
from django.urls import path
from . import views
from . import views, views_asistencia
from .views_horario import (
    StudentScheduleView,
    GetStudentScheduleView,
    GetEnrolledLaboratoriesView,
    CheckScheduleConflictView,
)
from .views_laboratorios import (
    EstudianteLaboratoriosView,
    LaboratoriosDisponiblesAPIView,
    VerificarConflictoAPIView,
    laboratorio_detalle,
)

app_name = 'estudiante'

urlpatterns = [
    # Dashboard y vistas principales
    path('dashboard/', views.EstudianteDashboardView.as_view(), name='dashboard'),
    path('curso/<uuid:course_id>/', views.EstudianteCursoDetalleView.as_view(), name='curso_detalle'),
    path('notas/', views.EstudianteNotasView.as_view(), name='notas'),
    path('cursos/', views.cursos, name='cursos'),
    
    # Laboratorios - Vista principal con POST para matrícula/desmatrícula
    path('laboratorios/', EstudianteLaboratoriosView.as_view(), name='laboratorios'),
    path('laboratorios/<uuid:laboratorio_id>/detalle/', laboratorio_detalle, name='laboratorio_detalle'),
    
    # APIs de laboratorios
    path('api/laboratorios/disponibles/', LaboratoriosDisponiblesAPIView.as_view(), name='api_labs_disponibles'),
    path('api/laboratorios/verificar-conflicto/', VerificarConflictoAPIView.as_view(), name='api_verificar_conflicto'),
    
    # Horarios - Vista principal y calendario
    path('horarios/', StudentScheduleView.as_view(), name='horarios'),
    
    # APIs de horarios
    path('api/horario/', GetStudentScheduleView.as_view(), name='api_horario'),
    path('api/horario/laboratorios/', GetEnrolledLaboratoriesView.as_view(), name='api_labs'),
    path('api/horario/conflictos/', CheckScheduleConflictView.as_view(), name='api_conflictos'),

    #asistenciaXwa
    path('asistencia/', views_asistencia.EstudianteAsistenciaView.as_view(), name='mis_asistencias'),
]
'''
"""
URLs para el módulo de estudiantes
Incluye todas las rutas para gestión de laboratorios y horarios
"""
from django.urls import path
from . import views
from .views_horario import (
    StudentScheduleView,
    GetStudentScheduleView,
    GetEnrolledLaboratoriesView,
    CheckScheduleConflictView,
)
from .views_laboratorios import (
    EstudianteLaboratoriosView,
    LaboratoriosDisponiblesAPIView,
    VerificarConflictoAPIView,
    laboratorio_detalle,
)

app_name = 'estudiante'

urlpatterns = [
    # Dashboard y vistas principales
    path('dashboard/', views.EstudianteDashboardView.as_view(), name='dashboard'),
    path('curso/<uuid:course_id>/', views.EstudianteCursoDetalleView.as_view(), name='curso_detalle'),
    path('notas/', views.EstudianteNotasView.as_view(), name='notas'),
    path('cursos/', views.cursos, name='cursos'),
    
    # Laboratorios - Vista principal y acciones
    path('laboratorios/', EstudianteLaboratoriosView.as_view(), name='laboratorios'),
    path('laboratorios/<uuid:laboratorio_id>/', laboratorio_detalle, name='laboratorio_detalle'),
    
    # APIs de laboratorios
    path('api/laboratorios/disponibles/', LaboratoriosDisponiblesAPIView.as_view(), name='api_labs_disponibles'),
    path('api/laboratorios/verificar-conflicto/', VerificarConflictoAPIView.as_view(), name='api_verificar_conflicto'),
    
    # Horarios - Vista principal y calendario
    path('horarios/', StudentScheduleView.as_view(), name='horarios'),
    
    # APIs de horarios
    path('api/horario/', GetStudentScheduleView.as_view(), name='api_horario'),
    path('api/horario/laboratorios/', GetEnrolledLaboratoriesView.as_view(), name='api_labs'),
    path('api/horario/conflictos/', CheckScheduleConflictView.as_view(), name='api_conflictos'),
]
'''