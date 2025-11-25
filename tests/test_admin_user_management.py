"""
Tests de integración para la funcionalidad de gestión de usuarios del panel administrativo
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from repositorio.postgres_repository.models import UsuarioModel


class AdminUserManagementTestCase(TestCase):
    """Tests para la gestión de usuarios en el panel administrativo"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = UsuarioModel.objects.create_user(
            email='admin@test.com',
            password='admin123',
            nombre='Admin',
            apellido='Test',
            rol='admin',
            activo=True
        )
        
        # Crear usuarios de prueba con diferentes roles
        self.estudiante = UsuarioModel.objects.create_user(
            email='estudiante@test.com',
            password='test123',
            nombre='Juan',
            apellido='Pérez',
            rol='estudiante',
            activo=True
        )
        
        self.docente = UsuarioModel.objects.create_user(
            email='docente@test.com',
            password='test123',
            nombre='María',
            apellido='García',
            rol='docente',
            activo=True
        )
        
        self.secretaria = UsuarioModel.objects.create_user(
            email='secretaria@test.com',
            password='test123',
            nombre='Ana',
            apellido='López',
            rol='secretaria',
            activo=False
        )
        
        self.inactive_user = UsuarioModel.objects.create_user(
            email='inactive@test.com',
            password='test123',
            nombre='Pedro',
            apellido='Martín',
            rol='estudiante',
            activo=False
        )
    
    def test_admin_usuarios_view_requires_authentication(self):
        """Test que la vista de usuarios requiere autenticación"""
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_admin_usuarios_view_requires_admin_role(self):
        """Test que la vista de usuarios requiere rol de administrador"""
        # Login con usuario no admin
        self.client.login(email='estudiante@test.com', password='test123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        
        # Debe denegar el acceso
        self.assertEqual(response.status_code, 302)
    
    def test_admin_usuarios_view_loads_successfully(self):
        """Test que la vista de usuarios carga correctamente para admin"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestión de Usuarios')
        self.assertContains(response, 'estudiante@test.com')
        self.assertContains(response, 'docente@test.com')
        self.assertContains(response, 'secretaria@test.com')
    
    def test_user_list_displays_all_users(self):
        """Test que la lista muestra todos los usuarios"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        
        # Verificar que todos los usuarios están en el contexto
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 5)  # 4 usuarios de prueba + admin
        
        # Verificar estadísticas
        self.assertEqual(response.context['total_usuarios'], 5)
        self.assertEqual(response.context['usuarios_activos'], 3)
        self.assertEqual(response.context['usuarios_inactivos'], 2)
    
    def test_filter_by_role(self):
        """Test del filtrado por rol"""
        self.client.login(email='admin@test.com', password='admin123')
        
        # Filtrar por estudiantes
        url = reverse('administrador:usuarios')
        response = self.client.get(url, {'rol': 'estudiante'})
        
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 2)  # estudiante activo e inactivo
        
        for usuario in usuarios:
            self.assertEqual(usuario.rol, 'estudiante')
    
    def test_filter_by_status(self):
        """Test del filtrado por estado"""
        self.client.login(email='admin@test.com', password='admin123')
        
        # Filtrar por usuarios activos
        url = reverse('administrador:usuarios')
        response = self.client.get(url, {'estado': 'activo'})
        
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 3)  # admin, estudiante, docente
        
        for usuario in usuarios:
            self.assertTrue(usuario.activo)
    
    def test_search_functionality(self):
        """Test de la funcionalidad de búsqueda"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        
        # Buscar por nombre
        response = self.client.get(url, {'search': 'Juan'})
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0].nombre, 'Juan')
        
        # Buscar por email
        response = self.client.get(url, {'search': 'docente@test.com'})
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0].email, 'docente@test.com')
        
        # Buscar por apellido
        response = self.client.get(url, {'search': 'García'})
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0].apellido, 'García')
    
    def test_combined_filters(self):
        """Test de filtros combinados"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url, {
            'rol': 'estudiante',
            'estado': 'activo',
            'search': 'Juan'
        })
        
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0].nombre, 'Juan')
        self.assertEqual(usuarios[0].rol, 'estudiante')
        self.assertTrue(usuarios[0].activo)
    
    def test_pagination(self):
        """Test de paginación"""
        # Crear más usuarios para probar paginación
        for i in range(25):
            UsuarioModel.objects.create_user(
                email=f'user{i}@test.com',
                password='test123',
                nombre=f'Usuario{i}',
                apellido='Test',
                rol='estudiante',
                activo=True
            )
        
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        
        # Verificar paginación
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['usuarios']), 20)  # paginate_by = 20
    
    def test_activate_user_success(self):
        """Test de activación exitosa de usuario"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios_api')
        response = self.client.post(url, {
            'action': 'activar',
            'user_id': self.inactive_user.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('activado correctamente', data['message'])
        self.assertTrue(data['user_status'])
        
        # Verificar que el usuario fue activado en la base de datos
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.activo)
        self.assertTrue(self.inactive_user.is_active)
    
    def test_deactivate_user_success(self):
        """Test de desactivación exitosa de usuario"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios_api')
        response = self.client.post(url, {
            'action': 'desactivar',
            'user_id': self.estudiante.id
        })
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('desactivado correctamente', data['message'])
        self.assertFalse(data['user_status'])
        
        # Verificar que el usuario fue desactivado en la base de datos
        self.estudiante.refresh_from_db()
        self.assertFalse(self.estudiante.activo)
        self.assertFalse(self.estudiante.is_active)
    
    def test_admin_cannot_deactivate_self(self):
        """Test que el admin no puede desactivarse a sí mismo"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios_api')
        response = self.client.post(url, {
            'action': 'desactivar',
            'user_id': self.admin_user.id
        })
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('No puedes desactivar tu propia cuenta', data['error'])
        
        # Verificar que el admin sigue activo
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.activo)
    
    def test_invalid_action(self):
        """Test de acción inválida"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios_api')
        response = self.client.post(url, {
            'action': 'invalid_action',
            'user_id': self.estudiante.id
        })
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Acción no válida', data['error'])
    
    def test_missing_parameters(self):
        """Test de parámetros faltantes"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios_api')
        
        # Sin action
        response = self.client.post(url, {'user_id': self.estudiante.id})
        self.assertEqual(response.status_code, 400)
        
        # Sin user_id
        response = self.client.post(url, {'action': 'activar'})
        self.assertEqual(response.status_code, 400)
    
    def test_nonexistent_user(self):
        """Test con usuario inexistente"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios_api')
        response = self.client.post(url, {
            'action': 'activar',
            'user_id': 99999  # ID que no existe
        })
        
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Usuario no encontrado', data['error'])
    
    def test_api_requires_admin_authentication(self):
        """Test que la API requiere autenticación de admin"""
        # Sin login
        url = reverse('administrador:usuarios_api')
        response = self.client.post(url, {
            'action': 'activar',
            'user_id': self.inactive_user.id
        })
        self.assertEqual(response.status_code, 302)
        
        # Con usuario no admin
        self.client.login(email='estudiante@test.com', password='test123')
        response = self.client.post(url, {
            'action': 'activar',
            'user_id': self.inactive_user.id
        })
        self.assertEqual(response.status_code, 302)
    
    def test_user_list_ordering(self):
        """Test del ordenamiento de usuarios"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        
        usuarios = response.context['usuarios']
        
        # Verificar que están ordenados por apellido, nombre
        for i in range(len(usuarios) - 1):
            current = usuarios[i]
            next_user = usuarios[i + 1]
            
            # Comparar apellidos
            if current.apellido == next_user.apellido:
                # Si apellidos iguales, comparar nombres
                self.assertLessEqual(current.nombre, next_user.nombre)
            else:
                self.assertLessEqual(current.apellido, next_user.apellido)
    
    def test_context_data_completeness(self):
        """Test que el contexto contiene todos los datos necesarios"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url, {
            'rol': 'docente',
            'estado': 'activo',
            'search': 'María'
        })
        
        context = response.context
        
        # Verificar datos básicos
        self.assertIn('page_title', context)
        self.assertEqual(context['page_title'], 'Gestión de Usuarios')
        
        # Verificar choices de roles
        self.assertIn('roles_choices', context)
        self.assertEqual(context['roles_choices'], UsuarioModel.ROLES)
        
        # Verificar filtros actuales
        self.assertIn('current_filters', context)
        filters = context['current_filters']
        self.assertEqual(filters['rol'], 'docente')
        self.assertEqual(filters['estado'], 'activo')
        self.assertEqual(filters['search'], 'María')
        
        # Verificar estadísticas
        self.assertIn('total_usuarios', context)
        self.assertIn('usuarios_activos', context)
        self.assertIn('usuarios_inactivos', context)
    
    def test_empty_search_results(self):
        """Test de búsqueda sin resultados"""
        self.client.login(email='admin@test.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        response = self.client.get(url, {'search': 'NoExiste'})
        
        usuarios = response.context['usuarios']
        self.assertEqual(len(usuarios), 0)
        
        # Verificar que la página se renderiza correctamente sin usuarios
        self.assertContains(response, 'No se encontraron usuarios')


class AdminUserManagementIntegrationTestCase(TestCase):
    """Tests de integración completos para flujos de usuario"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.admin_user = UsuarioModel.objects.create_user(
            email='admin@integration.com',
            password='admin123',
            nombre='Admin',
            apellido='Integration',
            rol='admin',
            activo=True
        )
        
        # Crear usuarios para diferentes escenarios
        self.test_users = []
        roles = ['estudiante', 'docente', 'secretaria']
        
        for i in range(15):
            user = UsuarioModel.objects.create_user(
                email=f'user{i}@integration.com',
                password='test123',
                nombre=f'Usuario{i}',
                apellido=f'Test{i}',
                rol=roles[i % 3],
                activo=i % 2 == 0  # Alternar activo/inactivo
            )
            self.test_users.append(user)
    
    def test_complete_user_management_workflow(self):
        """Test del flujo completo de gestión de usuarios"""
        self.client.login(email='admin@integration.com', password='admin123')
        
        # 1. Cargar lista inicial
        url = reverse('administrador:usuarios')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # 2. Filtrar por rol
        response = self.client.get(url, {'rol': 'estudiante'})
        usuarios_estudiantes = response.context['usuarios']
        self.assertTrue(len(usuarios_estudiantes) > 0)
        
        # 3. Buscar usuario específico
        response = self.client.get(url, {'search': 'Usuario1'})
        usuarios_encontrados = response.context['usuarios']
        self.assertEqual(len(usuarios_encontrados), 1)
        
        # 4. Activar usuario inactivo
        usuario_inactivo = next(u for u in self.test_users if not u.activo)
        api_url = reverse('administrador:usuarios_api')
        response = self.client.post(api_url, {
            'action': 'activar',
            'user_id': usuario_inactivo.id
        })
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # 5. Verificar cambio en la lista
        response = self.client.get(url)
        usuarios_activos_count = response.context['usuarios_activos']
        self.assertGreater(usuarios_activos_count, 0)
        
        # 6. Desactivar usuario activo
        usuario_activo = next(u for u in self.test_users if u.activo and u.id != usuario_inactivo.id)
        response = self.client.post(api_url, {
            'action': 'desactivar',
            'user_id': usuario_activo.id
        })
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_pagination_with_filters(self):
        """Test de paginación con filtros aplicados"""
        # Crear más usuarios para forzar paginación
        for i in range(25):
            UsuarioModel.objects.create_user(
                email=f'extra{i}@integration.com',
                password='test123',
                nombre=f'Extra{i}',
                apellido='User',
                rol='estudiante',
                activo=True
            )
        
        self.client.login(email='admin@integration.com', password='admin123')
        
        url = reverse('administrador:usuarios')
        
        # Primera página con filtro
        response = self.client.get(url, {'rol': 'estudiante'})
        self.assertTrue(response.context['is_paginated'])
        
        # Segunda página con el mismo filtro
        response = self.client.get(url, {'rol': 'estudiante', 'page': 2})
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el filtro se mantiene
        self.assertEqual(response.context['current_filters']['rol'], 'estudiante')
    
    def test_concurrent_user_operations(self):
        """Test de operaciones concurrentes sobre usuarios"""
        self.client.login(email='admin@integration.com', password='admin123')
        
        api_url = reverse('administrador:usuarios_api')
        
        # Simular operaciones concurrentes
        usuario1 = self.test_users[0]
        usuario2 = self.test_users[1]
        
        # Activar/desactivar múltiples usuarios
        responses = []
        
        response1 = self.client.post(api_url, {
            'action': 'desactivar' if usuario1.activo else 'activar',
            'user_id': usuario1.id
        })
        responses.append(response1)
        
        response2 = self.client.post(api_url, {
            'action': 'desactivar' if usuario2.activo else 'activar',
            'user_id': usuario2.id
        })
        responses.append(response2)
        
        # Verificar que ambas operaciones fueron exitosas
        for response in responses:
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])