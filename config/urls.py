"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin as django_admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from presentacion.controladores.admin import login_view
from presentacion.controladores.matricula_controller import MatriculaAPIView

urlpatterns = [
    # Página de login principal
    path('', login_view, name='login'),
    
    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Role-based modules with namespaces
    path('administrador/', include('presentacion.administrador.urls', namespace='administrador')),
    path('profesor/', include('presentacion.profesor.urls', namespace='profesor')),
    path('secretario/', include('presentacion.secretario.urls', namespace='secretario')),
    path('estudiante/', include('presentacion.estudiante.urls', namespace='estudiante')),
    path('login/', include('presentacion.login.urls', namespace='login')),
    
    # Django admin (renombrado para evitar conflictos)
    path('djadmin/', django_admin.site.urls),
    
    # APIs
    path('api/matriculas/upload_excel/', MatriculaAPIView.as_view(), name='matriculas-upload'),
    path('api/matriculas/', MatriculaAPIView.as_view(), name='matriculas-list'),
]