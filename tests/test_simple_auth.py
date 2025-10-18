"""
Simple test for authentication system
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleAuthTestCase(TestCase):
    """Simple tests for the authentication system"""
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            rol='admin'
        )
        
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.rol, 'admin')
        self.assertTrue(user.activo)
        self.assertTrue(user.is_active)
    
    def test_admin_permissions(self):
        """Test admin permission methods"""
        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            nombre='Admin',
            apellido='User',
            rol='admin'
        )
        
        regular_user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            nombre='Regular',
            apellido='User',
            rol='estudiante'
        )
        
        self.assertTrue(admin_user.is_admin())
        self.assertFalse(regular_user.is_admin())
    
    def test_user_activation(self):
        """Test user activation/deactivation"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            rol='admin'
        )
        
        # Test deactivation
        user.desactivar_usuario()
        self.assertFalse(user.activo)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_admin())  # Should be False when inactive
        
        # Test activation
        user.activar_usuario()
        self.assertTrue(user.activo)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_admin())  # Should be True when active again