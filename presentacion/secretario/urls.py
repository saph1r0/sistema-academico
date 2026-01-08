"""
URLs para el módulo de secretarios
"""
from django.urls import path

from . import views
from . import views_reservas
from . import views_lab
from django.views.generic import RedirectView
from . import views_asistencia_estudiantes  
from . import views_export_asistestudiante 
from . import views_export_asistestudiantespdffiltro

from .views_exam_accreditation import (
    SecretaryExamAccreditationView,
    ExamAccreditationDownloadView
)

app_name = 'secretario'

urlpatterns = [
   
    
    path('', RedirectView.as_view(pattern_name='secretario:dashboard'), name='index'),
    # Dashboard principal
    path('dashboard/', views.SecretarioDashboardView.as_view(), name='dashboard'),
    
    # Monitor de Notas (Lógica unificada en views.py)
    path('notas-estudiantes/', views.SecretarioNotasEstudiantesView.as_view(), name='notas_estudiantes'),
    path('api/notas-estudiantes/alumnos/', views.SecretarioNotasAlumnosAPIView.as_view(), name='api_notas_alumnos'),
    path('notas-estudiantes/exportar-csv/', views.ExportarNotasCSVSecretarioView.as_view(), name='exportar_notas_csv'),

    # Reportes y Estadísticas generales
    path('reportes/', views.SecretarioReportesView.as_view(), name='reportes'),
    path('estadisticas/', views.SecretarioEstadisticasView.as_view(), name='estadisticas'),
    
    # Gestión de Usuarios y Monitoreo
    path('usuarios/', views.SecretarioUsuariosView.as_view(), name='usuarios'),
    path('recursos/', views.SecretarioRecursosView.as_view(), name='recursos'),
    path('monitoreo/', views.SecretarioMonitoreoView.as_view(), name='monitoreo'),

  # ASISTENCIA (Correcto para funciones)
    path('asistencia/', views_asistencia_estudiantes.dashboard_asistencia, name='dashboard_asistencia'),
    path('asistencia/curso/<uuid:curso_id>/', views_asistencia_estudiantes.reporte_por_curso, name='reporte_curso'),
    path('asistencia/estudiante/<uuid:estudiante_id>/', views_asistencia_estudiantes.reporte_por_estudiante, name='reporte_estudiante'),
    path('asistencia/riesgo/', views_asistencia_estudiantes.estudiantes_en_riesgo, name='estudiantes_riesgo'),

    # EXPORTACIONES ASISTENCIA
    path('asistencia/exportar/dashboard/excel/', views_export_asistestudiante.exportar_dashboard_excel, name='exportar_dashboard_excel'),
    path('asistencia/exportar/curso/<uuid:curso_id>/excel/', views_export_asistestudiante.exportar_curso_excel, name='exportar_curso_excel'),
    path('asistencia/exportar/estudiante/<uuid:estudiante_id>/excel/', views_export_asistestudiante.exportar_estudiante_excel, name='exportar_estudiante_excel'),
    path('asistencia/exportar/dashboard/pdf/', views_export_asistestudiantespdffiltro.exportar_dashboard_pdf, name='exportar_dashboard_pdf'),
    path('asistencia/exportar/curso/<uuid:curso_id>/pdf/', views_export_asistestudiantespdffiltro.exportar_curso_pdf, name='exportar_curso_pdf'),
    path('asistencia/exportar/estudiante/<uuid:estudiante_id>/pdf/', views_export_asistestudiantespdffiltro.exportar_estudiante_pdf, name='exportar_estudiante_pdf'),

    # Gestión de Carga de Documentos (CSVs/PDFs de la facultad)
    path('cargar-documentos/', views.CargarDocumentosView.as_view(), name='cargar_documentos'),
    path('cargar-cursos-docentes/', views.cargar_cursos_docentes, name='cargar_cursos_docentes'),
    path('cargar-horarios/', views.cargar_horarios, name='cargar_horarios'),
    path('cargar-estudiantes/', views.cargar_estudiantes, name='cargar_estudiantes'),
    path('cargar-horarios-laboratorios/', views_lab.cargar_horarios_laboratorios, name='cargar_horarios_laboratorios'),

    # Laboratorios y Cupos
    path('laboratorios/', views_lab.SecretarioLaboratoriosView.as_view(), name='laboratorios'),
    path('laboratorios/configurar-cupo-global/', views_lab.configurar_cupo_global_laboratorio, name='configurar_cupo_global_laboratorio'),
    path('laboratorios/configurar-periodo-lab/', views_lab.configurar_periodo_matricula_laboratorio, name='configurar_periodo_matricula_laboratorio'),
    path('laboratorios/asignar-docente/', views_lab.asignar_docente_laboratorio, name='asignar_docente_laboratorio'),

    # Acreditación de Exámenes (PDFs de exámenes)
    path('exam-accreditation/', SecretaryExamAccreditationView.as_view(), name='exam_accreditation'),
    path('exam-accreditation/download/<uuid:accreditation_id>/<str:file_type>/', ExamAccreditationDownloadView.as_view(), name='exam_accreditation_download'),

    # Reservas de Ambientes
    path('reservas/', views_reservas.dashboard_reservas, name='reservas_dashboard'),
    path('reservas/api/dia/', views_reservas.api_reservas_del_dia, name='api_reservas_dia'),
    path('reservas/api/validar/', views_reservas.api_validar_restricciones, name='api_validar_restricciones'),
    path('reservas/api/filtrar/', views_reservas.api_reservas_por_filtro, name='api_reservas_filtrar'),
    path('reservas/api/cancelar/<uuid:reserva_id>/', views_reservas.api_cancelar_reserva, name='api_cancelar_reserva'),
]