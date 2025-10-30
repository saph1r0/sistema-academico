"""
Vistas para el sistema de autenticación
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from presentacion.permisos import obtener_dashboard_por_rol
import logging

logger = logging.getLogger('admin_panel.auth')


@csrf_protect
@never_cache
def login_view(request):
    """Vista de login principal"""
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir a su dashboard
        dashboard_url = obtener_dashboard_por_rol(request.user.role)
        return redirect(dashboard_url)
    
    if request.method == 'POST':
        email = request.POST.get('username')  # El campo se llama username en el template
        password = request.POST.get('password')
        
        if email and password:
            # Autenticar usuario usando nuestro backend personalizado
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Log del login exitoso
                    logger.info(f'Login exitoso: {email} - Rol: {user.role}')
                    
                    # Redirigir según el rol
                    dashboard_url = obtener_dashboard_por_rol(user.role)
                    messages.success(request, f'Bienvenido, {user.get_full_name()}')
                    return redirect(dashboard_url)
                else:
                    messages.error(request, 'Tu cuenta está desactivada.')
                    logger.warning(f'Intento de login con cuenta desactivada: {email}')
            else:
                messages.error(request, 'Email o contraseña incorrectos.')
                logger.warning(f'Intento de login fallido: {email}')
        else:
            messages.error(request, 'Por favor ingresa email y contraseña.')
    
    return render(request, 'auth/login.html')


@never_cache
def logout_view(request):
    """Vista de logout"""
    if request.user.is_authenticated:
        logger.info(f'Logout: {request.user.institutional_email}')
        logout(request)
        messages.success(request, 'Has cerrado sesión exitosamente.')
    
    return redirect('login:login')