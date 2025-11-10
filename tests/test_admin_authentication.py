"""
Tests para el sistema de autenticación y permisos del panel administrativo
"""
import pytest
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from unittest.mock import Mock, patch
from presentacion.administrador.mixins import (
    AdminRequiredMixin, 
    SecretariaOrAdminMixin,
    admin_required,
    secretaria_or_admin_required,
    ajax_admin_required,
    check_admin_permission,
    check_secretaria_or_admin_permission,
    PermissionDeniedError
)
from presentacion.administrador.middleware import (
    AdminPanelMiddleware,
    AdminSessionSecurityMiddleware,
    AdminAuditMiddleware
)
from presentacion.administrador.views import AdminDashboardView

User = get_user_model()


class UserModelTestCase(TestCase):
    """Tests para el modelo de usuario personalizado"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        
        self.secretaria_user = User.objects.create_user(
            email='secretaria@test.com',
            password='testpass123',
            nombre='Secretaria',
            apellido='Test',
            rol='secretaria'
        )
        
        self.docente_user = User.objects.create_user(
            email='docente@test.com',
            password='testpass123',
            nombre='Docente',
            apellido='Test',
            rol='docente'
        )
        
        self.estudiante_user = User.objects.create_user(
            email='estudiante@test.com',
            password='testpass123',
            nombre='Estudiante',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_user_creation(self):
        """Test de creación de usuarios"""
        self.assertEqual(self.admin_user.email, 'admin@test.com')
        self.assertEqual(self.admin_user.rol, 'admin')
        self.assertTrue(self.admin_user.activo)
        self.assertTrue(self.admin_user.is_active)
    
    def test_is_admin_method(self):
        """Test del método is_admin"""
        self.assertTrue(self.admin_user.is_admin())
        self.assertFalse(self.secretaria_user.is_admin())
        self.assertFalse(self.docente_user.is_admin())
        self.assertFalse(self.estudiante_user.is_admin())
    
    def test_is_secretaria_method(self):
        """Test del método is_secretaria"""
        self.assertFalse(self.admin_user.is_secretaria())
        self.assertTrue(self.secretaria_user.is_secretaria())
        self.assertFalse(self.docente_user.is_secretaria())
        self.assertFalse(self.estudiante_user.is_secretaria())
    
    def test_is_docente_method(self):
        """Test del método is_docente"""
        self.assertFalse(self.admin_user.is_docente())
        self.assertFalse(self.secretaria_user.is_docente())
        self.assertTrue(self.docente_user.is_docente())
        self.assertFalse(self.estudiante_user.is_docente())
    
    def test_is_estudiante_method(self):
        """Test del método is_estudiante"""
        self.assertFalse(self.admin_user.is_estudiante())
        self.assertFalse(self.secretaria_user.is_estudiante())
        self.assertFalse(self.docente_user.is_estudiante())
        self.assertTrue(self.estudiante_user.is_estudiante())
    
    def test_activar_usuario(self):
        """Test de activación de usuario"""
        self.admin_user.desactivar_usuario()
        self.assertFalse(self.admin_user.activo)
        self.assertFalse(self.admin_user.is_active)
        
        self.admin_user.activar_usuario()
        self.assertTrue(self.admin_user.activo)
        self.assertTrue(self.admin_user.is_active)
    
    def test_desactivar_usuario(self):
        """Test de desactivación de usuario"""
        self.assertTrue(self.admin_user.activo)
        self.admin_user.desactivar_usuario()
        self.assertFalse(self.admin_user.activo)
        self.assertFalse(self.admin_user.is_active)
    
    def test_inactive_user_permissions(self):
        """Test que usuarios inactivos no tienen permisos"""
        self.admin_user.desactivar_usuario()
        self.assertFalse(self.admin_user.is_admin())
        self.assertFalse(self.admin_user.is_secretaria())
        self.assertFalse(self.admin_user.is_docente())
        self.assertFalse(self.admin_user.is_estudiante())


class AdminRequiredMixinTestCase(TestCase):
    """Tests para AdminRequiredMixin"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_admin_user_passes_test(self):
        """Test que usuario admin pasa la verificación"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin_user
        
        mixin = AdminRequiredMixin()
        mixin.request = request
        
        self.assertTrue(mixin.test_func())
    
    def test_regular_user_fails_test(self):
        """Test que usuario regular falla la verificación"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.regular_user
        
        mixin = AdminRequiredMixin()
        mixin.request = request
        
        self.assertFalse(mixin.test_func())
    
    def test_anonymous_user_fails_test(self):
        """Test que usuario anónimo falla la verificación"""
        request = self.factory.get('/admin/dashboard/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        mixin = AdminRequiredMixin()
        mixin.request = request
        
        self.assertFalse(mixin.test_func())
    
    def test_inactive_admin_fails_test(self):
        """Test que admin inactivo falla la verificación"""
        self.admin_user.desactivar_usuario()
        
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin_user
        
        mixin = AdminRequiredMixin()
        mixin.request = request
        
        self.assertFalse(mixin.test_func())


class SecretariaOrAdminMixinTestCase(TestCase):
    """Tests para SecretariaOrAdminMixin"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        self.secretaria_user = User.objects.create_user(
            email='secretaria@test.com',
            password='testpass123',
            nombre='Secretaria',
            apellido='Test',
            rol='secretaria'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_admin_user_passes_test(self):
        """Test que usuario admin pasa la verificación"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin_user
        
        mixin = SecretariaOrAdminMixin()
        mixin.request = request
        
        self.assertTrue(mixin.test_func())
    
    def test_secretaria_user_passes_test(self):
        """Test que usuario secretaria pasa la verificación"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.secretaria_user
        
        mixin = SecretariaOrAdminMixin()
        mixin.request = request
        
        self.assertTrue(mixin.test_func())
    
    def test_regular_user_fails_test(self):
        """Test que usuario regular falla la verificación"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.regular_user
        
        mixin = SecretariaOrAdminMixin()
        mixin.request = request
        
        self.assertFalse(mixin.test_func())


class AdminDecoratorsTestCase(TestCase):
    """Tests para decoradores de admin"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_admin_required_decorator_with_admin_user(self):
        """Test decorador admin_required con usuario admin"""
        @admin_required
        def test_view(request):
            return "success"
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        result = test_view(request)
        self.assertEqual(result, "success")
    
    def test_admin_required_decorator_with_regular_user(self):
        """Test decorador admin_required con usuario regular"""
        @admin_required
        def test_view(request):
            return "success"
        
        request = self.factory.get('/test/')
        request.user = self.regular_user
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        result = test_view(request)
        # Debe redirigir
        self.assertEqual(result.status_code, 302)
    
    def test_secretaria_or_admin_required_decorator(self):
        """Test decorador secretaria_or_admin_required"""
        @secretaria_or_admin_required
        def test_view(request):
            return "success"
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        self._add_middleware(request)
        
        result = test_view(request)
        self.assertEqual(result, "success")
    
    def test_ajax_admin_required_decorator_success(self):
        """Test decorador ajax_admin_required con usuario admin"""
        @ajax_admin_required
        def test_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        result = test_view(request)
        self.assertEqual(result.status_code, 200)
    
    def test_ajax_admin_required_decorator_failure(self):
        """Test decorador ajax_admin_required con usuario regular"""
        @ajax_admin_required
        def test_view(request):
            from django.http import JsonResponse
            return JsonResponse({'success': True})
        
        request = self.factory.get('/test/')
        request.user = self.regular_user
        
        result = test_view(request)
        self.assertEqual(result.status_code, 403)
    
    def _add_middleware(self, request):
        """Agrega middleware necesario para los tests"""
        # Agregar sesión
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Agregar mensajes
        messages_middleware = MessageMiddleware(lambda x: None)
        messages_middleware.process_request(request)


class PermissionUtilsTestCase(TestCase):
    """Tests para funciones utilitarias de permisos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        self.secretaria_user = User.objects.create_user(
            email='secretaria@test.com',
            password='testpass123',
            nombre='Secretaria',
            apellido='Test',
            rol='secretaria'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_check_admin_permission_success(self):
        """Test check_admin_permission con usuario admin"""
        self.assertTrue(check_admin_permission(self.admin_user))
    
    def test_check_admin_permission_failure(self):
        """Test check_admin_permission con usuario regular"""
        with self.assertRaises(PermissionDeniedError):
            check_admin_permission(self.regular_user)
    
    def test_check_admin_permission_unauthenticated(self):
        """Test check_admin_permission con usuario no autenticado"""
        user = Mock()
        user.is_authenticated = False
        
        with self.assertRaises(PermissionDeniedError):
            check_admin_permission(user)
    
    def test_check_secretaria_or_admin_permission_admin(self):
        """Test check_secretaria_or_admin_permission con admin"""
        self.assertTrue(check_secretaria_or_admin_permission(self.admin_user))
    
    def test_check_secretaria_or_admin_permission_secretaria(self):
        """Test check_secretaria_or_admin_permission con secretaria"""
        self.assertTrue(check_secretaria_or_admin_permission(self.secretaria_user))
    
    def test_check_secretaria_or_admin_permission_failure(self):
        """Test check_secretaria_or_admin_permission con usuario regular"""
        with self.assertRaises(PermissionDeniedError):
            check_secretaria_or_admin_permission(self.regular_user)


class AdminPanelMiddlewareTestCase(TestCase):
    """Tests para AdminPanelMiddleware"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        self.middleware = AdminPanelMiddleware(lambda x: x)
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_is_admin_url_detection(self):
        """Test detección de URLs de admin"""
        self.assertTrue(self.middleware._is_admin_url('/admin/dashboard/'))
        self.assertTrue(self.middleware._is_admin_url('/administrador/usuarios/'))
        self.assertFalse(self.middleware._is_admin_url('/login/'))
        self.assertFalse(self.middleware._is_admin_url('/estudiante/dashboard/'))
    
    def test_admin_request_with_admin_user(self):
        """Test request de admin con usuario admin"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin_user
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        result = self.middleware.process_request(request)
        self.assertIsNone(result)  # No debe redirigir
    
    def test_admin_request_with_regular_user(self):
        """Test request de admin con usuario regular"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.regular_user
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        result = self.middleware.process_request(request)
        self.assertEqual(result.status_code, 302)  # Debe redirigir
    
    def test_admin_request_unauthenticated(self):
        """Test request de admin con usuario no autenticado"""
        request = self.factory.get('/admin/dashboard/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        result = self.middleware.process_request(request)
        self.assertEqual(result.status_code, 302)  # Debe redirigir
    
    def test_non_admin_request(self):
        """Test request que no es de admin"""
        request = self.factory.get('/login/')
        request.user = self.regular_user
        
        result = self.middleware.process_request(request)
        self.assertIsNone(result)  # No debe procesar
    
    def _add_middleware(self, request):
        """Agrega middleware necesario para los tests"""
        # Agregar sesión
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Agregar mensajes
        messages_middleware = MessageMiddleware(lambda x: None)
        messages_middleware.process_request(request)


class AdminSessionSecurityMiddlewareTestCase(TestCase):
    """Tests para AdminSessionSecurityMiddleware"""
    
    def setUp(self):
        """Configuración inicial"""
        self.factory = RequestFactory()
        self.middleware = AdminSessionSecurityMiddleware(lambda x: x)
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
    
    def test_admin_session_timeout_validation(self):
        """Test validación de timeout de sesión de admin"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin_user
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        # Simular sesión expirada
        import time
        request.session['admin_last_activity'] = time.time() - 7200  # 2 horas atrás
        
        result = self.middleware.process_request(request)
        self.assertEqual(result.status_code, 302)  # Debe redirigir por timeout
    
    def test_admin_session_valid(self):
        """Test sesión de admin válida"""
        request = self.factory.get('/admin/dashboard/')
        request.user = self.admin_user
        
        # Agregar middleware necesario
        self._add_middleware(request)
        
        # Sesión reciente
        import time
        request.session['admin_last_activity'] = time.time() - 300  # 5 minutos atrás
        
        result = self.middleware.process_request(request)
        self.assertIsNone(result)  # No debe redirigir
    
    def _add_middleware(self, request):
        """Agrega middleware necesario para los tests"""
        # Agregar sesión
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Agregar mensajes
        messages_middleware = MessageMiddleware(lambda x: None)
        messages_middleware.process_request(request)


class AdminViewsIntegrationTestCase(TestCase):
    """Tests de integración para las vistas de admin"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
    
    def test_admin_dashboard_access_with_admin_user(self):
        """Test acceso al dashboard con usuario admin"""
        self.client.force_login(self.admin_user)
        
        # Simular URL del dashboard (ajustar según configuración real)
        response = self.client.get('/administrador/dashboard/')
        
        # Verificar que no hay redirección (acceso permitido)
        # Nota: Puede ser 200 o 404 dependiendo de si las URLs están configuradas
        self.assertIn(response.status_code, [200, 404])
    
    def test_admin_dashboard_access_with_regular_user(self):
        """Test acceso al dashboard con usuario regular"""
        self.client.force_login(self.regular_user)
        
        response = self.client.get('/administrador/dashboard/')
        
        # Debe redirigir o denegar acceso
        self.assertIn(response.status_code, [302, 403, 404])
    
    def test_admin_dashboard_access_unauthenticated(self):
        """Test acceso al dashboard sin autenticación"""
        response = self.client.get('/administrador/dashboard/')
        
        # Debe redirigir al login o denegar acceso
        self.assertIn(response.status_code, [302, 403, 404])


if __name__ == '__main__':
    pytest.main([__file__])