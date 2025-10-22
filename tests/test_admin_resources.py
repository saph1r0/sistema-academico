#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
from datetime import date, time, datetime, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock

from repositorio.postgres_repository.models import UsuarioModel, LaboratorioModel, ReservaModel
from servicios.servicioReservas import ServicioReservas
from presentacion.administrador.views import AdminRecursosView


class TestLaboratorioModel(TestCase):
    """Tests para el modelo LaboratorioModel"""
    
    def setUp(self):
        self.laboratorio_data = {
            'nombre': 'Laboratorio de Cómputo 1',
            'codigo': 'LAB-COMP-01',
            'tipo': 'COMPUTO',
            'capacidad': 30,
            'ubicacion': 'Edificio A - Piso 2',
            'equipamiento': '30 computadoras, proyector, aire acondicionado',
            'activo': True
        }
    
    def test_crear_laboratorio(self):
        """Test creación de laboratorio"""
        laboratorio = LaboratorioModel.objects.create(**self.laboratorio_data)
        
        self.assertEqual(laboratorio.nombre, 'Laboratorio de Cómputo 1')
        self.assertEqual(laboratorio.codigo, 'LAB-COMP-01')
        self.assertEqual(laboratorio.tipo, 'COMPUTO')
        self.assertEqual(laboratorio.capacidad, 30)
        self.assertTrue(laboratorio.activo)
    
    def test_str_representation(self):
        """Test representación string del laboratorio"""
        laboratorio = LaboratorioModel.objects.create(**self.laboratorio_data)
        expected = f"{laboratorio.codigo} - {laboratorio.nombre}"
        self.assertEqual(str(laboratorio), expected)
    
    def test_laboratorio_unique_constraints(self):
        """Test restricciones de unicidad"""
        LaboratorioModel.objects.create(**self.laboratorio_data)
        
        # Intentar crear otro laboratorio con el mismo código
        with self.assertRaises(Exception):
            LaboratorioModel.objects.create(**self.laboratorio_data)


class TestReservaModel(TestCase):
    """Tests para el modelo ReservaModel"""
    
    def setUp(self):
        # Crear usuario docente
        self.docente = UsuarioModel.objects.create_user(
            email='docente@test.com',
            password='testpass123',
            nombre='Juan',
            apellido='Pérez',
            rol='docente'
        )
        
        # Crear laboratorio
        self.laboratorio = LaboratorioModel.objects.create(
            nombre='Lab Test',
            codigo='LAB-TEST-01',
            tipo='COMPUTO',
            capacidad=25,
            ubicacion='Test Location',
            activo=True
        )
        
        self.reserva_data = {
            'laboratorio': self.laboratorio,
            'docente': self.docente,
            'fecha_reserva': date.today() + timedelta(days=1),
            'hora_inicio': time(9, 0),
            'hora_fin': time(11, 0),
            'proposito': 'Clase de programación',
            'estado': 'PENDIENTE'
        }
    
    def test_crear_reserva(self):
        """Test creación de reserva"""
        reserva = ReservaModel.objects.create(**self.reserva_data)
        
        self.assertEqual(reserva.laboratorio, self.laboratorio)
        self.assertEqual(reserva.docente, self.docente)
        self.assertEqual(reserva.estado, 'PENDIENTE')
        self.assertFalse(reserva.aprobada_automaticamente)
    
    def test_duracion_horas(self):
        """Test cálculo de duración en horas"""
        reserva = ReservaModel.objects.create(**self.reserva_data)
        duracion = reserva.duracion_horas()
        self.assertEqual(duracion, 2.0)  # 9:00 a 11:00 = 2 horas
    
    def test_tiene_conflicto_sin_conflicto(self):
        """Test detección de conflictos - sin conflicto"""
        reserva = ReservaModel.objects.create(**self.reserva_data)
        self.assertFalse(reserva.tiene_conflicto())
    
    def test_tiene_conflicto_con_conflicto(self):
        """Test detección de conflictos - con conflicto"""
        # Crear primera reserva aprobada
        reserva1_data = self.reserva_data.copy()
        reserva1_data['estado'] = 'APROBADA'
        reserva1 = ReservaModel.objects.create(**reserva1_data)
        
        # Crear segunda reserva que se solapa
        reserva2_data = self.reserva_data.copy()
        reserva2_data['hora_inicio'] = time(10, 0)  # Se solapa con la primera
        reserva2_data['hora_fin'] = time(12, 0)
        reserva2 = ReservaModel.objects.create(**reserva2_data)
        
        self.assertTrue(reserva2.tiene_conflicto())
    
    def test_str_representation(self):
        """Test representación string de la reserva"""
        reserva = ReservaModel.objects.create(**self.reserva_data)
        expected = f"{self.laboratorio.codigo} - {reserva.fecha_reserva} {reserva.hora_inicio}-{reserva.hora_fin}"
        self.assertEqual(str(reserva), expected)


class TestServicioReservas(TestCase):
    """Tests para ServicioReservas"""
    
    def setUp(self):
        self.servicio = ServicioReservas()
        
        # Crear datos de prueba
        self.docente = UsuarioModel.objects.create_user(
            email='docente@test.com',
            password='testpass123',
            nombre='Juan',
            apellido='Pérez',
            rol='docente'
        )
        
        self.laboratorio1 = LaboratorioModel.objects.create(
            nombre='Lab 1',
            codigo='LAB-01',
            tipo='COMPUTO',
            capacidad=30,
            ubicacion='Edificio A',
            activo=True
        )
        
        self.laboratorio2 = LaboratorioModel.objects.create(
            nombre='Lab 2',
            codigo='LAB-02',
            tipo='FISICA',
            capacidad=25,
            ubicacion='Edificio B',
            activo=True
        )
    
    def test_consultar_disponibilidad_sin_reservas(self):
        """Test consulta de disponibilidad sin reservas existentes"""
        fecha = date.today() + timedelta(days=1)
        inicio = time(9, 0)
        fin = time(11, 0)
        
        disponibilidad = self.servicio.consultar_disponibilidad(fecha, inicio, fin)
        
        self.assertEqual(len(disponibilidad), 2)
        for item in disponibilidad:
            self.assertTrue(item['disponible'])
            self.assertEqual(len(item['reservas_dia']), 0)
    
    def test_consultar_disponibilidad_con_reservas(self):
        """Test consulta de disponibilidad con reservas existentes"""
        fecha = date.today() + timedelta(days=1)
        
        # Crear reserva aprobada
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=fecha,
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            proposito='Test',
            estado='APROBADA'
        )
        
        # Consultar disponibilidad en horario que se solapa
        disponibilidad = self.servicio.consultar_disponibilidad(
            fecha, time(10, 0), time(12, 0)
        )
        
        # Lab 1 no debe estar disponible, Lab 2 sí
        lab1_disponible = next(item for item in disponibilidad if item['laboratorio'] == self.laboratorio1)
        lab2_disponible = next(item for item in disponibilidad if item['laboratorio'] == self.laboratorio2)
        
        self.assertFalse(lab1_disponible['disponible'])
        self.assertTrue(lab2_disponible['disponible'])
    
    def test_reservar_ambiente_sin_conflicto(self):
        """Test reserva de ambiente sin conflicto"""
        fecha = date.today() + timedelta(days=1)
        
        reserva = self.servicio.reservar_ambiente(
            docente_id=self.docente.id,
            ambiente_id=self.laboratorio1.id,
            fecha=fecha,
            inicio=time(9, 0),
            fin=time(11, 0),
            proposito='Clase de programación'
        )
        
        self.assertEqual(reserva.estado, 'APROBADA')
        self.assertTrue(reserva.aprobada_automaticamente)
        self.assertEqual(reserva.laboratorio, self.laboratorio1)
        self.assertEqual(reserva.docente, self.docente)
    
    def test_reservar_ambiente_con_conflicto(self):
        """Test reserva de ambiente con conflicto"""
        fecha = date.today() + timedelta(days=1)
        
        # Crear reserva existente
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=fecha,
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            proposito='Reserva existente',
            estado='APROBADA'
        )
        
        # Intentar reservar en horario que se solapa
        reserva = self.servicio.reservar_ambiente(
            docente_id=self.docente.id,
            ambiente_id=self.laboratorio1.id,
            fecha=fecha,
            inicio=time(10, 0),
            fin=time(12, 0),
            proposito='Nueva reserva'
        )
        
        self.assertEqual(reserva.estado, 'RECHAZADA')
        self.assertFalse(reserva.aprobada_automaticamente)
        self.assertIn('Conflicto de horario', reserva.motivo_rechazo)
    
    def test_verificar_conflicto(self):
        """Test verificación de conflictos"""
        fecha = date.today() + timedelta(days=1)
        
        # Crear reserva aprobada
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=fecha,
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            proposito='Test',
            estado='APROBADA'
        )
        
        # Verificar conflicto en horario que se solapa
        tiene_conflicto = self.servicio.verificar_conflicto(
            ambiente_id=self.laboratorio1.id,
            fecha=fecha,
            inicio=time(10, 0),
            fin=time(12, 0)
        )
        
        self.assertTrue(tiene_conflicto)
        
        # Verificar sin conflicto en horario diferente
        sin_conflicto = self.servicio.verificar_conflicto(
            ambiente_id=self.laboratorio1.id,
            fecha=fecha,
            inicio=time(14, 0),
            fin=time(16, 0)
        )
        
        self.assertFalse(sin_conflicto)
    
    def test_obtener_laboratorios_activos(self):
        """Test obtención de laboratorios activos con estadísticas"""
        # Crear algunas reservas
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=date.today() + timedelta(days=1),
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            proposito='Test 1',
            estado='APROBADA'
        )
        
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=date.today() + timedelta(days=2),
            hora_inicio=time(14, 0),
            hora_fin=time(16, 0),
            proposito='Test 2',
            estado='PENDIENTE'
        )
        
        laboratorios = self.servicio.obtener_laboratorios_activos()
        
        self.assertEqual(laboratorios.count(), 2)
        
        lab1 = laboratorios.get(id=self.laboratorio1.id)
        self.assertEqual(lab1.total_reservas, 2)
        self.assertEqual(lab1.reservas_aprobadas, 1)
        self.assertEqual(lab1.reservas_pendientes, 1)
    
    def test_obtener_conflictos_activos(self):
        """Test obtención de conflictos activos"""
        fecha_futura = date.today() + timedelta(days=1)
        
        # Crear dos reservas que se solapan
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=fecha_futura,
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            proposito='Reserva 1',
            estado='APROBADA'
        )
        
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=fecha_futura,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
            proposito='Reserva 2',
            estado='PENDIENTE'
        )
        
        conflictos = self.servicio.obtener_conflictos_activos()
        
        self.assertEqual(len(conflictos), 1)
        self.assertEqual(conflictos[0].proposito, 'Reserva 2')
    
    def test_obtener_estadisticas_uso(self):
        """Test obtención de estadísticas de uso"""
        fecha_inicio = date.today() - timedelta(days=7)
        fecha_fin = date.today()
        
        # Crear reservas de prueba
        ReservaModel.objects.create(
            laboratorio=self.laboratorio1,
            docente=self.docente,
            fecha_reserva=fecha_inicio + timedelta(days=1),
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
            proposito='Test 1',
            estado='APROBADA',
            aprobada_automaticamente=True
        )
        
        ReservaModel.objects.create(
            laboratorio=self.laboratorio2,
            docente=self.docente,
            fecha_reserva=fecha_inicio + timedelta(days=2),
            hora_inicio=time(14, 0),
            hora_fin=time(17, 0),
            proposito='Test 2',
            estado='APROBADA_MANUAL',
            aprobada_automaticamente=False
        )
        
        estadisticas = self.servicio.obtener_estadisticas_uso(fecha_inicio, fecha_fin)
        
        self.assertEqual(estadisticas['total_reservas'], 2)
        self.assertEqual(estadisticas['tasa_aprobacion_automatica'], 50.0)
        self.assertIn('Lab 1', estadisticas['reservas_por_laboratorio'])
        self.assertIn('Lab 2', estadisticas['reservas_por_laboratorio'])


class TestAdminRecursosView(TestCase):
    """Tests para AdminRecursosView"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = UsuarioModel.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='User',
            rol='admin'
        )
        
        # Crear usuario no administrador
        self.regular_user = UsuarioModel.objects.create_user(
            email='user@test.com',
            password='testpass123',
            nombre='Regular',
            apellido='User',
            rol='estudiante'
        )
        
        # Crear datos de prueba
        self.laboratorio = LaboratorioModel.objects.create(
            nombre='Test Lab',
            codigo='TEST-01',
            tipo='COMPUTO',
            capacidad=30,
            ubicacion='Test Location',
            activo=True
        )
        
        self.url = reverse('admin:recursos')
    
    def test_acceso_admin_autorizado(self):
        """Test que el administrador puede acceder a la vista"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recursos y Laboratorios')
    
    def test_acceso_no_admin_denegado(self):
        """Test que usuarios no admin no pueden acceder"""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.url)
        
        # Debe redirigir o devolver 403
        self.assertIn(response.status_code, [302, 403])
    
    def test_acceso_sin_autenticar_denegado(self):
        """Test que usuarios no autenticados no pueden acceder"""
        response = self.client.get(self.url)
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
    
    @patch('presentacion.administrador.views.ServicioReservas')
    def test_context_data_con_datos(self, mock_servicio):
        """Test que el contexto incluye todos los datos necesarios"""
        # Configurar mock
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_laboratorios_activos.return_value = [self.laboratorio]
        mock_instance.obtener_reservas_recientes.return_value = []
        mock_instance.obtener_conflictos_activos.return_value = []
        mock_instance.obtener_estadisticas_uso.return_value = {
            'total_reservas': 10,
            'tasa_aprobacion_automatica': 80.0
        }
        
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('laboratorios', response.context)
        self.assertIn('reservas_recientes', response.context)
        self.assertIn('conflictos_activos', response.context)
        self.assertIn('estadisticas', response.context)
        self.assertIn('metricas_resumen', response.context)
        self.assertIn('alertas_recursos', response.context)
    
    @patch('presentacion.administrador.views.ServicioReservas')
    def test_manejo_errores_servicio(self, mock_servicio):
        """Test manejo de errores del servicio"""
        # Configurar mock para lanzar excepción
        mock_instance = mock_servicio.return_value
        mock_instance.obtener_laboratorios_activos.side_effect = Exception("Error de prueba")
        
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Debe mostrar datos por defecto
        self.assertEqual(response.context['metricas_resumen']['total_laboratorios'], 0)
    
    def test_generacion_alertas_recursos(self):
        """Test generación de alertas basadas en el estado de recursos"""
        view = AdminRecursosView()
        
        # Simular laboratorios sin uso
        laboratorios_mock = MagicMock()
        laboratorios_mock.filter.return_value.exists.return_value = True
        laboratorios_mock.filter.return_value.count.return_value = 2
        
        # Simular conflictos
        conflictos = ['conflicto1', 'conflicto2']
        
        # Simular estadísticas con baja tasa de aprobación
        estadisticas = {'tasa_aprobacion_automatica': 60.0}
        
        alertas = view._generar_alertas_recursos(laboratorios_mock, conflictos, estadisticas)
        
        # Debe generar alertas por conflictos, laboratorios sin uso y baja tasa de aprobación
        self.assertGreater(len(alertas), 0)
        
        # Verificar que hay alerta por conflictos
        alerta_conflictos = next((a for a in alertas if 'Conflictos' in a['titulo']), None)
        self.assertIsNotNone(alerta_conflictos)
        self.assertEqual(alerta_conflictos['tipo'], 'error')


class TestIntegracionRecursos(TestCase):
    """Tests de integración para el módulo de recursos"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = UsuarioModel.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin',
            apellido='User',
            rol='admin'
        )
        
        # Crear docente
        self.docente = UsuarioModel.objects.create_user(
            email='docente@test.com',
            password='testpass123',
            nombre='Juan',
            apellido='Pérez',
            rol='docente'
        )
        
        # Crear laboratorios
        self.lab1 = LaboratorioModel.objects.create(
            nombre='Laboratorio de Cómputo 1',
            codigo='LAB-COMP-01',
            tipo='COMPUTO',
            capacidad=30,
            ubicacion='Edificio A - Piso 2',
            activo=True
        )
        
        self.lab2 = LaboratorioModel.objects.create(
            nombre='Laboratorio de Física',
            codigo='LAB-FIS-01',
            tipo='FISICA',
            capacidad=25,
            ubicacion='Edificio B - Piso 1',
            activo=True
        )
    
    def test_flujo_completo_reservas_y_monitoreo(self):
        """Test del flujo completo de reservas y monitoreo"""
        servicio = ServicioReservas()
        fecha_reserva = date.today() + timedelta(days=1)
        
        # 1. Crear reserva sin conflicto
        reserva1 = servicio.reservar_ambiente(
            docente_id=self.docente.id,
            ambiente_id=self.lab1.id,
            fecha=fecha_reserva,
            inicio=time(9, 0),
            fin=time(11, 0),
            proposito='Clase de programación'
        )
        
        self.assertEqual(reserva1.estado, 'APROBADA')
        self.assertTrue(reserva1.aprobada_automaticamente)
        
        # 2. Crear reserva con conflicto
        reserva2 = servicio.reservar_ambiente(
            docente_id=self.docente.id,
            ambiente_id=self.lab1.id,
            fecha=fecha_reserva,
            inicio=time(10, 0),
            fin=time(12, 0),
            proposito='Otra clase'
        )
        
        self.assertEqual(reserva2.estado, 'RECHAZADA')
        self.assertFalse(reserva2.aprobada_automaticamente)
        
        # 3. Verificar que aparece en conflictos activos
        conflictos = servicio.obtener_conflictos_activos()
        self.assertEqual(len(conflictos), 1)
        
        # 4. Verificar vista de administrador
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin:recursos'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laboratorio de Cómputo 1')
        self.assertContains(response, 'Conflictos Detectados')
        
        # 5. Verificar estadísticas
        estadisticas = servicio.obtener_estadisticas_uso()
        self.assertEqual(estadisticas['total_reservas'], 2)
        self.assertEqual(estadisticas['tasa_aprobacion_automatica'], 50.0)
    
    def test_disponibilidad_multiple_laboratorios(self):
        """Test consulta de disponibilidad en múltiples laboratorios"""
        servicio = ServicioReservas()
        fecha = date.today() + timedelta(days=1)
        
        # Reservar lab1
        servicio.reservar_ambiente(
            docente_id=self.docente.id,
            ambiente_id=self.lab1.id,
            fecha=fecha,
            inicio=time(9, 0),
            fin=time(11, 0),
            proposito='Clase'
        )
        
        # Consultar disponibilidad
        disponibilidad = servicio.consultar_disponibilidad(
            fecha=fecha,
            inicio=time(10, 0),
            fin=time(12, 0)
        )
        
        # Lab1 no disponible, Lab2 disponible
        lab1_disp = next(item for item in disponibilidad if item['laboratorio'].id == self.lab1.id)
        lab2_disp = next(item for item in disponibilidad if item['laboratorio'].id == self.lab2.id)
        
        self.assertFalse(lab1_disp['disponible'])
        self.assertTrue(lab2_disp['disponible'])


if __name__ == '__main__':
    pytest.main([__file__])