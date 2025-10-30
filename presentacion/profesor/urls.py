"""
URLs para el módulo de profesores
"""
from django.urls import path
from . import views
from . import views_simple
from . import api_views

app_name = 'profesor'

urlpatterns = [
    # Vistas principales (usando vistas simplificadas temporalmente)
    path('dashboard/', views.ProfesorDashboardView.as_view(), name='dashboard'),
    path('notas/', views_simple.ProfesorNotasViewSimple.as_view(), name='notas'),
    path('asistencia/', views.ProfesorAsistenciaView.as_view(), name='asistencia'),
    path('reservas/', views.ProfesorReservasView.as_view(), name='reservas'),
    path('silabo/', views.ProfesorSilaboView.as_view(), name='silabo'),
    
    # APIs para gráficos
    path('api/grade-statistics/', api_views.GradeStatisticsAPI.as_view(), name='api_grade_statistics'),
    path('api/attendance-statistics/', api_views.AttendanceStatisticsAPI.as_view(), name='api_attendance_statistics'),
    
    # Utilidades de debug (usando vistas simplificadas)
    path('debug/check-data/', views_simple.DebugDataViewSimple.as_view(), name='debug_data'),
    path('debug/process-excel/', views_simple.DebugProcessExcelViewSimple.as_view(), name='debug_process_excel'),
]