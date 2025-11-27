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
from . import views_reservas
from . import views_asistencia_profesor
from . import views_reportes
from . import views_horario

from .views_silabo import (
    ProfesorSilaboView,
    SubirSilaboView,
    EditarSilaboView,
)

app_name = 'profesor'

from .views_exam_accreditation import (
    TeacherExamAccreditationView,
    ExamAccreditationUploadAjaxView,
    ExamAccreditationDownloadView,
)
urlpatterns = [
    # Vista principal simplificada
    path("", views_simple.ProfesorDashboardView.as_view(), name="home"),

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
    path('mi-asistencia/', views_asistencia_profesor.ProfesorAsistenciaPersonalView.as_view(), name='mi_asistencia'),
    path('asistencia/', views_asistencia.asistencia.as_view(), name='asistencia'),
    path('asistencia/historial/', views_asistencia.ProfesorAsistenciaHistorialView.as_view(), name='asistencia_historial'),
    path('asistencia/reporte/', views_asistencia.ProfesorReporteAsistenciaView.as_view(), name='asistencia_reporte'),
    path('asistencia/api/rapida/', views_asistencia.ProfesorAsistenciaRapidaAPIView.as_view(), name='asistencia_api_rapida'),
    
    # Otras funcionalidades del profesor
    path('reservas/', views_simple.ProfesorReservasView.as_view(), name='reservas'),    path('silabo/', views_silabo.ProfesorSilaboView.as_view(), name='silabo'),

     # API de reservas
    path('reservas/estado/', views_reservas.reservas_estado, name='reservas_estado'),
    path('reservas/api/', views_reservas.reservas_api, name='reservas_crear'),
    path('reservas/api/<uuid:pk>/', views_reservas.reserva_api_detail, name='reservas_eliminar'),
    path('reservas/mis/', views_reservas.reservas_mis, name='reservas_mis'),

    
    # Debug y herramientas
    path('debug/data/', views_simple.ProfesorDebugDataView.as_view(), name='debug_data'),
    path('debug/process-excel/', views_simple.ProfesorDebugProcessExcelView.as_view(), name='debug_process_excel'),
    
    # API endpoints (temporalmente comentadas)
    # path('api/cursos/', api_views.ProfesorCursosAPIView.as_view(), name='api_cursos'),
    # path('api/estadisticas/', api_views.ProfesorEstadisticasAPIView.as_view(), name='api_estadisticas'),

     path('silabo/', ProfesorSilaboView.as_view(), name='silabo'),
    path('silabo/subir/', SubirSilaboView.as_view(), name='subir_silabo'),
    path('silabo/editar/', EditarSilaboView.as_view(), name='editar_silabo'), 

    #acreditacion examenes
    path('exam-accreditation/',TeacherExamAccreditationView.as_view(),name='exam_accreditation' ),
    path('exam-accreditation/upload-ajax/',ExamAccreditationUploadAjaxView.as_view(),name='exam_accreditation_upload_ajax'),
    path( 'exam-accreditation/download/<uuid:accreditation_id>/<str:file_type>/', ExamAccreditationDownloadView.as_view(),name='exam_accreditation_download'),

    #REPORTESxDOCENTE
    path('reportes/', views_reportes.ReportesView.as_view(), name='reportes'),
    path('reportes/pdf/', views_reportes.GenerarPDFView.as_view(), name='reportes_pdf'),
    
    #HORARIOS
    path('horario/', views_horario.TeacherScheduleView.as_view(), name='horario'),
    path('horario/api/', views_horario.GetTeacherScheduleView.as_view(), name='horario_api'),
]