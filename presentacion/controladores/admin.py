from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from presentacion.permisos import get_user_dashboard_url

@csrf_protect
@never_cache
def login_view(request):
    """
    Vista de login principal del sistema
    Redirige al dashboard de admin después del login exitoso
    """
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect(get_user_dashboard_url(request.user))
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Actualizar último acceso si el modelo lo soporta
                    if hasattr(user, 'ultimo_acceso'):
                        from django.utils import timezone
                        user.ultimo_acceso = timezone.now()
                        user.save(update_fields=['ultimo_acceso'])
                    
                    # Redirigir al dashboard de admin
                    #next_url = request.GET.get('next', 'admin:dashboard')
                    #return redirect(next_url)
                    return redirect(get_user_dashboard_url(user))
                else:
                    messages.error(request, "Tu cuenta está desactivada. Contacta al administrador.")
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Por favor, completa todos los campos.")
    
    return render(request, 'auth/login.html')


# Vistas legacy para compatibilidad (redirigen a las nuevas vistas)
def dashboard_view(request):
    """Vista legacy - redirige al nuevo dashboard"""
    #return redirect('admin:dashboard')
    return redirect(get_user_dashboard_url(request.user))


def usuarios_list(request):
    """Vista legacy - redirige a la nueva gestión de usuarios"""
    return redirect('admin:usuarios')


def cursos_list(request):
    """Vista legacy - redirige a recursos"""
    return redirect('admin:recursos')


def matriculas(request):
    """Vista legacy - redirige a reportes"""
    return redirect('admin:reportes')