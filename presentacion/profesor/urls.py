"""
URLs para el módulo de profesores
"""
from django.urls import path
from . import views
from . import views_simple
from . import views_silabo
from . import api_views
from . import views_grade_upload
from . import views_asistencia
from . import api_reservas

app_name = 'profesor'

urlpatterns = [
    # Vista principal simplificada
    path('dashboard/', views_simple.ProfesorDashboardView.as_view(), name='dashboard'),
    
    # Vista de detalle de curso
    path('curso/<uuid:course_group_id>/', views_simple.ProfesorCourseDetailView.as_view(), name='course_detail'),
    
    # Gestión de notas por fases
    path('notas/', views_grade_upload.TeacherGradeUploadView.as_view(), name='notas'),
    path('notas/subir/', views_grade_upload.TeacherGradeUploadView.as_view(), name='grade_upload'),
    path('notas/estadisticas/', views_grade_upload.TeacherStatisticsDashboardView.as_view(), name='grade_statistics'),
    path('notas/ajax/upload/', views_grade_upload.GradeUploadAjaxView.as_view(), name='grade_upload_ajax'),
    path('notas/ajax/statistics/', views_grade_upload.GradeStatisticsAjaxView.as_view(), name='grade_statistics_ajax'),
    path('notas/plantilla/descargar/', views_grade_upload.DownloadExcelTemplateView.as_view(), name='download_excel_template'),
    
    # Gestión de asistencia
    path('asistencia/', views_asistencia.asistencia.as_view(), name='asistencia'),
    path('asistencia/historial/', views_asistencia.ProfesorAsistenciaHistorialView.as_view(), name='asistencia_historial'),
    path('asistencia/reporte/', views_asistencia.ProfesorReporteAsistenciaView.as_view(), name='asistencia_reporte'),
    path('asistencia/api/rapida/', views_asistencia.ProfesorAsistenciaRapidaAPIView.as_view(), name='asistencia_api_rapida'),
    
    # Otras funcionalidades del profesor
    path('reservas/', views_simple.ProfesorReservasView.as_view(), name='reservas'),
    path('silabo/', views_silabo.ProfesorSilaboView.as_view(), name='silabo'),
    
    # API de reservas
    path('reservas/estado/', api_reservas.estado_ocupacion, name='reservas_estado'),
    path('reservas/api/', api_reservas.crear_reserva, name='reservas_crear'),
    path('reservas/api/<uuid:pk>/', api_reservas.eliminar_reserva, name='reservas_eliminar'),
    
    # Debug y herramientas
    path('debug/data/', views_simple.ProfesorDebugDataView.as_view(), name='debug_data'),
    path('debug/process-excel/', views_simple.ProfesorDebugProcessExcelView.as_view(), name='debug_process_excel'),
    
    # API endpoints (temporalmente comentadas)
    # path('api/cursos/', api_views.ProfesorCursosAPIView.as_view(), name='api_cursos'),
    # path('api/estadisticas/', api_views.ProfesorEstadisticasAPIView.as_view(), name='api_estadisticas'),
]