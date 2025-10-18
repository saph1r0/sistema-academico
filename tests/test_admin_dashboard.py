#!/usr/bin/python
# -*- coding: utf-8 -*-
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock

from presentacion.administrador.views import AdminDashboardView
from servicios.servicioMetricas import ServicioMetricas
from dominio.modelo.admin_sistema.metricas_sistema import MetricasSistema, AlertaSistema

User = get_user_model()


class TestAdminDashboardView(TestCase):
    """Tests para la vista del dashboard administrativo"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user.rol = 'admin'
        self.admin_user.activo = True
        self.admin_user.save()
        
        # Crear usuario no administrador
        self.regular_user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='testpass123'
        )
        self.regular_user.rol = 'estudiante'
        self.regular_user.activo = True
        self.regular_user.save()
        
        self.dashboard_url = reverse('administrador:dashboard')
    
    def test_dashboard_requires_admin_permission(self):
        """Test que verifica que solo administradores pueden acceder al dashboard"""
        # Sin autenticación
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Con usuario regular
        self.client.force_login(self.regular_user)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Con usuario administrador
        self.client.force_login(self.admin_user)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('presentacion.administrador.views.ServicioMetricas')
    def test_dashboard_loads_metrics_successfully(self, mock_servicio):
        """Test que verifica que el dashboard carga las métricas correctamente"""
        # Configurar mock
        mock_metricas = MetricasSistema()
        mock_metricas.total_usuarios_activos = 150
        mock_metricas.total_cursos_activos = 25
        mock_metricas.promedio_asistencia_global = 85.5
        mock_metricas.promedio_notas_global = 15.2
        
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_metricas_sistema.return_value = mock_metricas
        
        # Hacer request
        self.client.force_login(self.admin_user)
        response = self.client.get(self.dashboard_url)
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Administrativo')
        self.assertContains(response, '150')  # usuarios activos
        self.assertContains(response, '25')   # cursos activos
        
        # Verificar que se llamó al servicio
        mock_instance.obtener_metricas_sistema.assert_called_once()
    
    @patch('presentacion.administrador.views.ServicioMetricas')
    def test_dashboard_handles_service_error_gracefully(self, mock_servicio):
        """Test que verifica el manejo de errores del servicio de métricas"""
        # Configurar mock para lanzar excepción
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_metricas_sistema.side_effect = Exception("Error de conexión")
        
        # Hacer request
        self.client.force_login(self.admin_user)
        response = self.client.get(self.dashboard_url)
        
        # Verificar que la página se carga con valores por defecto
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Administrativo')
        self.assertContains(response, '0')  # valores por defecto
    
    @patch('presentacion.administrador.views.ServicioMetricas')
    def test_dashboard_displays_alerts(self, mock_servicio):
        """Test que verifica la visualización de alertas del sistema"""
        # Crear alertas de prueba
        alerta_critica = AlertaSistema()
        alerta_critica.tipo = 'error'
        alerta_critica.titulo = 'Error crítico'
        alerta_critica.descripcion = 'Descripción del error'
        alerta_critica.prioridad = 'alta'
        alerta_critica.fecha_creacion = timezone.now()
        
        alerta_warning = AlertaSistema()
        alerta_warning.tipo = 'warning'
        alerta_warning.titulo = 'Advertencia'
        alerta_warning.descripcion = 'Descripción de la advertencia'
        alerta_warning.prioridad = 'media'
        alerta_warning.fecha_creacion = timezone.now()
        
        # Configurar mock
        mock_metricas = MetricasSistema()
        mock_metricas.alertas_pendientes = [alerta_critica, alerta_warning]
        
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_metricas_sistema.return_value = mock_metricas
        
        # Hacer request
        self.client.force_login(self.admin_user)
        response = self.client.get(self.dashboard_url)
        
        # Verificar que las alertas se muestran
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Error crítico')
        self.assertContains(response, 'Advertencia')
        self.assertContains(response, 'Descripción del error')
        self.assertContains(response, 'Descripción de la advertencia')
    
    def test_dashboard_context_data(self):
        """Test que verifica los datos del contexto del dashboard"""
        view = AdminDashboardView()
        view.request = MagicMock()
        view.request.user = self.admin_user
        
        with patch.object(view, 'servicio_metricas') as mock_servicio:
            mock_metricas = MetricasSistema()
            mock_metricas.total_usuarios_activos = 100
            mock_servicio.obtener_metricas_sistema.return_value = mock_metricas
            
            context = view.get_context_data()
            
            self.assertIn('page_title', context)
            self.assertIn('metricas', context)
            self.assertIn('alertas_pendientes', context)
            self.assertEqual(context['page_title'], 'Dashboard Administrativo')


class TestAdminDashboardAPIView(TestCase):
    """Tests para la API del dashboard administrativo"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user.rol = 'admin'
        self.admin_user.activo = True
        self.admin_user.save()
        
        self.api_url = reverse('administrador:dashboard_api')
    
    @patch('presentacion.administrador.views.ServicioMetricas')
    def test_dashboard_api_returns_json_metrics(self, mock_servicio):
        """Test que verifica que la API retorna métricas en formato JSON"""
        # Configurar mock
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_metricas_dashboard_json.return_value = {
            'usuarios_activos': 150,
            'cursos_activos': 25,
            'promedio_asistencia': 85.5,
            'promedio_notas': 15.2
        }
        mock_instance._ultima_actualizacion = timezone.now()
        
        # Hacer request
        self.client.force_login(self.admin_user)
        response = self.client.get(self.api_url)
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['usuarios_activos'], 150)
    
    @patch('presentacion.administrador.views.ServicioMetricas')
    def test_dashboard_api_handles_error(self, mock_servicio):
        """Test que verifica el manejo de errores en la API"""
        # Configurar mock para lanzar excepción
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_metricas_dashboard_json.side_effect = Exception("Error de servicio")
        
        # Hacer request
        self.client.force_login(self.admin_user)
        response = self.client.get(self.api_url)
        
        # Verificar respuesta de error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_dashboard_api_requires_admin_permission(self):
        """Test que verifica que la API requiere permisos de administrador"""
        # Sin autenticación
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login


class TestServicioMetricas(TestCase):
    """Tests para el servicio de métricas"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.servicio = ServicioMetricas()
    
    def test_obtener_metricas_sistema_returns_metricas_object(self):
        """Test que verifica que el servicio retorna un objeto MetricasSistema"""
        metricas = self.servicio.obtener_metricas_sistema()
        
        self.assertIsInstance(metricas, MetricasSistema)
        self.assertIsNotNone(metricas.fecha_calculo)
    
    def test_cache_functionality(self):
        """Test que verifica el funcionamiento del cache de métricas"""
        # Primera llamada
        metricas1 = self.servicio.obtener_metricas_sistema()
        
        # Segunda llamada (debería usar cache)
        metricas2 = self.servicio.obtener_metricas_sistema()
        
        # Verificar que se usa el mismo objeto del cache
        self.assertEqual(metricas1.fecha_calculo, metricas2.fecha_calculo)
    
    def test_forzar_recalculo_bypasses_cache(self):
        """Test que verifica que forzar recálculo ignora el cache"""
        # Primera llamada
        metricas1 = self.servicio.obtener_metricas_sistema()
        
        # Segunda llamada forzando recálculo
        metricas2 = self.servicio.obtener_metricas_sistema(forzar_recalculo=True)
        
        # Las fechas deberían ser diferentes
        self.assertNotEqual(metricas1.fecha_calculo, metricas2.fecha_calculo)
    
    def test_limpiar_cache(self):
        """Test que verifica la limpieza del cache"""
        # Obtener métricas para llenar cache
        self.servicio.obtener_metricas_sistema()
        
        # Verificar que hay cache
        self.assertIsNotNone(self.servicio._metricas_cache)
        
        # Limpiar cache
        self.servicio.limpiar_cache()
        
        # Verificar que el cache se limpió
        self.assertIsNone(self.servicio._metricas_cache)
        self.assertIsNone(self.servicio._ultima_actualizacion)


class TestMetricasSistema(TestCase):
    """Tests para el modelo de dominio MetricasSistema"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.metricas = MetricasSistema()
    
    def test_calcular_total_usuarios(self):
        """Test que verifica el cálculo del total de usuarios"""
        self.metricas.total_estudiantes = 100
        self.metricas.total_docentes = 20
        self.metricas.total_secretarias = 5
        self.metricas.total_administradores = 2
        
        total = self.metricas.calcular_total_usuarios()
        self.assertEqual(total, 127)
    
    def test_obtener_porcentaje_usuarios_activos(self):
        """Test que verifica el cálculo del porcentaje de usuarios activos"""
        self.metricas.total_estudiantes = 80
        self.metricas.total_docentes = 20
        self.metricas.total_usuarios_activos = 75
        
        porcentaje = self.metricas.obtener_porcentaje_usuarios_activos()
        self.assertEqual(porcentaje, 75.0)  # 75 de 100 = 75%
    
    def test_obtener_porcentaje_usuarios_activos_sin_usuarios(self):
        """Test que verifica el manejo cuando no hay usuarios"""
        porcentaje = self.metricas.obtener_porcentaje_usuarios_activos()
        self.assertEqual(porcentaje, 0.0)
    
    def test_tiene_alertas_criticas(self):
        """Test que verifica la detección de alertas críticas"""
        # Sin alertas críticas
        self.assertFalse(self.metricas.tiene_alertas_criticas())
        
        # Con alerta crítica
        alerta = AlertaSistema()
        alerta.prioridad = 'alta'
        alerta.resuelto = False
        self.metricas.alertas_pendientes = [alerta]
        
        self.assertTrue(self.metricas.tiene_alertas_criticas())
    
    def test_obtener_metricas_dashboard(self):
        """Test que verifica el formato de métricas para dashboard"""
        self.metricas.total_usuarios_activos = 100
        self.metricas.total_cursos_activos = 25
        self.metricas.promedio_asistencia_global = 85.7
        self.metricas.promedio_notas_global = 15.3
        
        dashboard_data = self.metricas.obtener_metricas_dashboard()
        
        self.assertIn('usuarios_activos', dashboard_data)
        self.assertIn('cursos_activos', dashboard_data)
        self.assertIn('promedio_asistencia', dashboard_data)
        self.assertIn('promedio_notas', dashboard_data)
        
        self.assertEqual(dashboard_data['usuarios_activos'], 100)
        self.assertEqual(dashboard_data['cursos_activos'], 25)
        self.assertEqual(dashboard_data['promedio_asistencia'], 85.7)
        self.assertEqual(dashboard_data['promedio_notas'], 15.3)