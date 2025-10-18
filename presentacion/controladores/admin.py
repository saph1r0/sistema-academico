from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect


@csrf_protect
@never_cache
def login_view(request):
    """
    Vista de login principal del sistema
    Redirige al dashboard de admin después del login exitoso
    """
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('admin:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Actualizar último acceso si el modelo lo soporta
                    if hasattr(user, 'actualizar_ultimo_acceso'):
                        user.actualizar_ultimo_acceso()
                    
                    # Redirigir al dashboard de admin
                    next_url = request.GET.get('next', 'admin:dashboard')
                    return redirect(next_url)
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
    return redirect('admin:dashboard')


def usuarios_list(request):
    """Vista legacy - redirige a la nueva gestión de usuarios"""
    return redirect('admin:usuarios')


def cursos_list(request):
    """Vista legacy - redirige a recursos"""
    return redirect('admin:recursos')


def matriculas(request):
    """Vista legacy - redirige a reportes"""
    return redirect('admin:reportes')