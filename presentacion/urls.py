from django.urls import path
from presentacion.controladores.matricula_controller import MatriculaAPIView
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("cargar", views.cargar, name="cargar"),

    path('matriculas/upload_excel/', MatriculaAPIView.as_view(), name='matriculas-upload'),  
    path('matriculas/', MatriculaAPIView.as_view(), name='matriculas-list'), 
]
