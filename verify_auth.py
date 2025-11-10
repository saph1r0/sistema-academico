#!/usr/bin/env python
"""
Script to verify the authentication system implementation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from presentacion.administrador.mixins import (
    AdminRequiredMixin, 
    check_admin_permission,
    PermissionDeniedError
)

def test_user_model():
    """Test the custom User model"""
    print("Testing User Model...")
    
    User = get_user_model()
    
    # Test user creation
    try:
        admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='Test',
            rol='admin'
        )
        print("✓ Admin user created successfully")
        
        regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='User',
            apellido='Test',
            rol='estudiante'
        )
        print("✓ Regular user created successfully")
        
        # Test admin methods
        assert admin_user.is_admin() == True, "Admin user should have admin permissions"
        assert regular_user.is_admin() == False, "Regular user should not have admin permissions"
        print("✓ Admin permission methods work correctly")
        
        # Test activation/deactivation
        admin_user.desactivar_usuario()
        assert admin_user.is_admin() == False, "Inactive admin should not have permissions"
        
        admin_user.activar_usuario()
        assert admin_user.is_admin() == True, "Reactivated admin should have permissions"
        print("✓ User activation/deactivation works correctly")
        
        # Test other role methods
        secretaria_user = User.objects.create_user(
            email='secretaria@test.com',
            password='testpass123',
            nombre='Secretaria',
            apellido='Test',
            rol='secretaria'
        )
        
        assert secretaria_user.is_secretaria() == True, "Secretaria user should have secretaria permissions"
        assert secretaria_user.is_admin() == False, "Secretaria user should not have admin permissions"
        print("✓ Role-specific methods work correctly")
        
        print("✓ All User model tests passed!")
        
    except Exception as e:
        print(f"✗ User model test failed: {e}")
        return False
    
    return True

def test_permission_functions():
    """Test permission utility functions"""
    print("\nTesting Permission Functions...")
    
    User = get_user_model()
    
    try:
        admin_user = User.objects.get(email='admin@test.com')
        regular_user = User.objects.get(email='user@test.com')
        
        # Test check_admin_permission
        try:
            check_admin_permission(admin_user)
            print("✓ Admin user passes permission check")
        except PermissionDeniedError:
            print("✗ Admin user failed permission check")
            return False
        
        try:
            check_admin_permission(regular_user)
            print("✗ Regular user should not pass admin permission check")
            return False
        except PermissionDeniedError:
            print("✓ Regular user correctly denied admin permissions")
        
        print("✓ All permission function tests passed!")
        
    except Exception as e:
        print(f"✗ Permission function test failed: {e}")
        return False
    
    return True

def test_mixin_functionality():
    """Test AdminRequiredMixin functionality"""
    print("\nTesting AdminRequiredMixin...")
    
    from django.test import RequestFactory
    
    User = get_user_model()
    factory = RequestFactory()
    
    try:
        admin_user = User.objects.get(email='admin@test.com')
        regular_user = User.objects.get(email='user@test.com')
        
        # Test with admin user
        request = factory.get('/admin/dashboard/')
        request.user = admin_user
        
        mixin = AdminRequiredMixin()
        mixin.request = request
        
        assert mixin.test_func() == True, "Admin user should pass mixin test"
        print("✓ AdminRequiredMixin works with admin user")
        
        # Test with regular user
        request.user = regular_user
        mixin.request = request
        
        assert mixin.test_func() == False, "Regular user should fail mixin test"
        print("✓ AdminRequiredMixin correctly rejects regular user")
        
        print("✓ All AdminRequiredMixin tests passed!")
        
    except Exception as e:
        print(f"✗ AdminRequiredMixin test failed: {e}")
        return False
    
    return True

def cleanup():
    """Clean up test data"""
    print("\nCleaning up test data...")
    
    User = get_user_model()
    
    try:
        User.objects.filter(email__in=[
            'admin@test.com',
            'user@test.com',
            'secretaria@test.com'
        ]).delete()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")

def main():
    """Main test function"""
    print("=== Authentication System Verification ===\n")
    
    all_passed = True
    
    # Run tests
    if not test_user_model():
        all_passed = False
    
    if not test_permission_functions():
        all_passed = False
    
    if not test_mixin_functionality():
        all_passed = False
    
    # Cleanup
    cleanup()
    
    # Summary
    print("\n=== Test Summary ===")
    if all_passed:
        print("✓ All authentication system tests passed!")
        print("\nThe authentication and permission system has been successfully implemented with:")
        print("- Custom User model with role-based permissions")
        print("- AdminRequiredMixin for view-level access control")
        print("- Permission utility functions")
        print("- User activation/deactivation functionality")
        print("- Role-specific permission methods")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())