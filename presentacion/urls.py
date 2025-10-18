from django.urls import path, include
from presentacion.controladores.matricula_controller import MatriculaAPIView
from . import views
from presentacion.controladores import admin

urlpatterns = [
    path("", views.index, name="index"),
    path("cargar", views.cargar, name="cargar"),

    path('matriculas/upload_excel/', MatriculaAPIView.as_view(), name='matriculas-upload'),  
    path('matriculas/', MatriculaAPIView.as_view(), name='matriculas-list'),
    
    # Admin panel routes
    path('admin/', include('presentacion.administrador.urls')),
]
