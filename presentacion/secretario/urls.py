"""
URLs para el módulo de secretarios
"""
from django.urls import path
from . import views
from django.urls import path
from . import views_reservas
from .views_exam_accreditation import (
    SecretaryExamAccreditationView,
    ExamAccreditationDownloadView
)


app_name = 'secretario'

urlpatterns = [
    path('dashboard/', views.SecretarioDashboardView.as_view(), name='dashboard'),
    #path('profesores/', views.SecretarioProfesoresView.as_view(), name='profesores'),
    path('laboratorios/', views.SecretarioLaboratoriosView.as_view(), name='laboratorios'),
    path('reportes/', views.SecretarioReportesView.as_view(), name='reportes'),
    path('estadisticas/', views.SecretarioEstadisticasView.as_view(), name='estadisticas'),
    path('usuarios/', views.SecretarioUsuariosView.as_view(), name='usuarios'),
    path('recursos/', views.SecretarioRecursosView.as_view(), name='recursos'),
    path('monitoreo/', views.SecretarioMonitoreoView.as_view(), name='monitoreo'),
    path('cargar-documentos/', views.CargarDocumentosView.as_view(), name='cargar_documentos'),
    path('cargar-cursos-docentes/', views.cargar_cursos_docentes, name='cargar_cursos_docentes'),
    path('cargar-horarios/', views.cargar_horarios, name='cargar_horarios'),
        path('cargar-estudiantes/', views.cargar_estudiantes, name='cargar_estudiantes'),



    path('exam-accreditation/',SecretaryExamAccreditationView.as_view(),name='exam_accreditation'),
    path(
        'exam-accreditation/download/<uuid:accreditation_id>/<str:file_type>/',
        ExamAccreditationDownloadView.as_view(),
        name='exam_accreditation_download'
    ),

    #reservas
    path('reservas/', views_reservas.dashboard_reservas, name='reservas_dashboard'),
    path('reservas/api/dia/', views_reservas.api_reservas_del_dia, name='api_reservas_dia'),
    path('reservas/api/validar/', views_reservas.api_validar_restricciones, name='api_validar_restricciones'),
    path('reservas/api/filtrar/', views_reservas.api_reservas_por_filtro, name='api_reservas_filtrar'),
    path('reservas/api/cancelar/<uuid:reserva_id>/', views_reservas.api_cancelar_reserva, name='api_cancelar_reserva'),
]