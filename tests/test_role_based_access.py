"""
Tests para el sistema de control de acceso por roles
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from presentacion.permisos import (
    get_user_role, is_admin, is_teacher, is_student, is_secretary,
    user_has_role, get_user_dashboard_url
)

User = get_user_model()


class RoleBasedAccessTestCase(TestCase):
    """Tests base para control de acceso por roles"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuarios de prueba para cada rol
        self.admin_user = self.create_test_user('admin', 'admin@unsa.edu.pe')
        self.teacher_user = self.create_test_user('teacher', 'jperez@unsa.edu.pe')
        self.student_user = self.create_test_user('student', 'jgarcia@unsa.edu.pe')
        self.secretary_user = self.create_test_user('secretary', 'mlopez@unsa.edu.pe')
    
    def create_test_user(self, role, email):
        """Crea un usuario de prueba con el rol especificado"""
        user = User.objects.create_user(
            institutional_email=email,
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=role,
            is_active=True
        )
        return user


class PermissionFunctionsTest(RoleBasedAccessTestCase):
    """Tests para las funciones de permisos"""
    
    def test_get_user_role(self):
        """Test para la función get_user_role"""
        self.assertEqual(get_user_role(self.admin_user), 'admin')
        self.assertEqual(get_user_role(self.teacher_user), 'teacher')
        self.assertEqual(get_user_role(self.student_user), 'student')
        self.assertEqual(get_user_role(self.secretary_user), 'secretary')
    
    def test_role_verification_functions(self):
        """Test para las funciones de verificación de roles"""
        # Test admin
        self.assertTrue(is_admin(self.admin_user))
        self.assertFalse(is_admin(self.teacher_user))
        self.assertFalse(is_admin(self.student_user))
        self.assertFalse(is_admin(self.secretary_user))
        
        # Test teacher
        self.assertFalse(is_teacher(self.admin_user))
        self.assertTrue(is_teacher(self.teacher_user))
        self.assertFalse(is_teacher(self.student_user))
        self.assertFalse(is_teacher(self.secretary_user))
        
        # Test student
        self.assertFalse(is_student(self.admin_user))
        self.assertFalse(is_student(self.teacher_user))
        self.assertTrue(is_student(self.student_user))
        self.assertFalse(is_student(self.secretary_user))
        
        # Test secretary
        self.assertFalse(is_secretary(self.admin_user))
        self.assertFalse(is_secretary(self.teacher_user))
        self.assertFalse(is_secretary(self.student_user))
        self.assertTrue(is_secretary(self.secretary_user))
    
    def test_user_has_role(self):
        """Test para la función user_has_role"""
        self.assertTrue(user_has_role(self.admin_user, 'admin'))
        self.assertFalse(user_has_role(self.admin_user, 'teacher'))
        
        self.assertTrue(user_has_role(self.teacher_user, 'teacher'))
        self.assertFalse(user_has_role(self.teacher_user, 'student'))
    
    def test_get_user_dashboard_url(self):
        """Test para la función get_user_dashboard_url"""
        self.assertEqual(get_user_dashboard_url(self.admin_user), 'administrador:dashboard')
        self.assertEqual(get_user_dashboard_url(self.teacher_user), 'profesor:dashboard')
        self.assertEqual(get_user_dashboard_url(self.student_user), 'estudiante:dashboard')
        self.assertEqual(get_user_dashboard_url(self.secretary_user), 'secretario:dashboard')


class LoginAccessTest(RoleBasedAccessTestCase):
    """Tests para el sistema de login y autenticación"""
    
    def test_login_with_valid_credentials(self):
        """Test de login con credenciales válidas"""
        response = self.client.post(reverse('login:login'), {
            'username': 'admin@unsa.edu.pe',
            'password': 'testpass123'
        })
        
        # Debe redirigir después del login exitoso
        self.assertEqual(response.status_code, 302)
    
    def test_login_with_invalid_credentials(self):
        """Test de login con credenciales inválidas"""
        response = self.client.post(reverse('login:login'), {
            'username': 'admin@unsa.edu.pe',
            'password': 'wrongpassword'
        })
        
        # Debe mostrar el formulario con errores
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciales incorrectas')
    
    def test_login_with_invalid_email_format(self):
        """Test de login con formato de email inválido"""
        response = self.client.post(reverse('login:login'), {
            'username': 'invalid-email@gmail.com',
            'password': 'testpass123'
        })
        
        # Debe mostrar error de formato
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Formato de email institucional inválido')


class RoleBasedViewAccessTest(RoleBasedAccessTestCase):
    """Tests para acceso a vistas basado en roles"""
    
    def test_admin_dashboard_access(self):
        """Test de acceso al dashboard de administrador"""
        # Admin debe poder acceder
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('administrador:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Otros roles no deben poder acceder
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('administrador:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección
        
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('administrador:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección
    
    def test_teacher_dashboard_access(self):
        """Test de acceso al dashboard de profesor"""
        # Teacher debe poder acceder
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('profesor:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Otros roles no deben poder acceder
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('profesor:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección
        
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('profesor:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección
    
    def test_student_dashboard_access(self):
        """Test de acceso al dashboard de estudiante"""
        # Student debe poder acceder
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('estudiante:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Otros roles no deben poder acceder
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('estudiante:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección
    
    def test_secretary_dashboard_access(self):
        """Test de acceso al dashboard de secretario"""
        # Secretary debe poder acceder
        self.client.force_login(self.secretary_user)
        response = self.client.get(reverse('secretario:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Otros roles no deben poder acceder
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('secretario:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección
    
    def test_unauthenticated_access(self):
        """Test de acceso sin autenticación"""
        # Todas las vistas protegidas deben redirigir al login
        protected_urls = [
            'administrador:dashboard',
            'profesor:dashboard',
            'estudiante:dashboard',
            'secretario:dashboard'
        ]
        
        for url_name in protected_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)
            self.assertIn('login', response.url)


class SessionSecurityTest(RoleBasedAccessTestCase):
    """Tests para seguridad de sesiones"""
    
    def test_session_timeout_configuration(self):
        """Test de configuración de timeout de sesiones"""
        from django.conf import settings
        
        # Verificar que existen configuraciones de timeout por rol
        self.assertIn('ROLE_SESSION_TIMEOUTS', dir(settings))
        timeouts = settings.ROLE_SESSION_TIMEOUTS
        
        self.assertIn('admin', timeouts)
        self.assertIn('teacher', timeouts)
        self.assertIn('student', timeouts)
        self.assertIn('secretary', timeouts)
    
    def test_session_data_after_login(self):
        """Test de datos de sesión después del login"""
        self.client.force_login(self.admin_user)
        
        # Hacer una request para activar el middleware
        response = self.client.get(reverse('administrador:dashboard'))
        
        # Verificar que se guardó información del rol en la sesión
        session = self.client.session
        self.assertIn('user_role', session)
        self.assertEqual(session['user_role'], 'admin')
        self.assertIn('last_activity', session)


class MiddlewareTest(RoleBasedAccessTestCase):
    """Tests para los middlewares de seguridad"""
    
    def test_security_headers_middleware(self):
        """Test del middleware de headers de seguridad"""
        response = self.client.get(reverse('login:login'))
        
        # Verificar headers de seguridad
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        
        self.assertIn('X-Frame-Options', response)
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        
        self.assertIn('X-XSS-Protection', response)
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
    
    def test_role_access_control_middleware(self):
        """Test del middleware de control de acceso por roles"""
        # Login como estudiante
        self.client.force_login(self.student_user)
        
        # Intentar acceder a ruta de admin
        response = self.client.get('/admin/dashboard/')
        
        # Debe redirigir y mostrar mensaje de error
        self.assertEqual(response.status_code, 302)
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('No tienes permisos' in str(m) for m in messages))


class DataFilteringTest(RoleBasedAccessTestCase):
    """Tests para filtrado de datos por rol"""
    
    def test_admin_sees_all_data(self):
        """Test que los administradores ven todos los datos"""
        from presentacion.permisos import filter_data_by_role
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        all_users = User.objects.all()
        
        # Admin debe ver todos los usuarios
        filtered_data = filter_data_by_role(self.admin_user, all_users)
        self.assertEqual(filtered_data.count(), all_users.count())
    
    def test_student_sees_only_own_data(self):
        """Test que los estudiantes solo ven sus propios datos"""
        from presentacion.permisos import filter_data_by_role
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        all_users = User.objects.all()
        
        # Student debe ver datos limitados
        filtered_data = filter_data_by_role(self.student_user, all_users)
        # En este caso, como no hay relación específica, debe retornar queryset vacío
        self.assertEqual(filtered_data.count(), 0)


if __name__ == '__main__':
    pytest.main([__file__])