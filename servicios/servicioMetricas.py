#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List
from django.db.models import Count, Avg, Q
from django.utils import timezone

from dominio.modelo.admin_sistema.metricas_sistema import MetricasSistema, AlertaSistema
from repositorio.postgres_repository.models import UsuarioModel, EstudianteModel, MatriculaModel


class ServicioMetricas:
    """
    Servicio de dominio para calcular métricas del sistema
    """
    
    def __init__(self):
        self._cache_timeout = 300  # 5 minutos de cache
        self._ultima_actualizacion = None
        self._metricas_cache = None
    
    def obtener_metricas_sistema(self, forzar_recalculo: bool = False) -> MetricasSistema:
        """
        Obtiene las métricas del sistema, usando cache si está disponible
        """
        ahora = timezone.now()
        
        # Verificar si necesitamos recalcular
        if (not forzar_recalculo and 
            self._metricas_cache and 
            self._ultima_actualizacion and
            (ahora - self._ultima_actualizacion).seconds < self._cache_timeout):
            return self._metricas_cache
        
        # Calcular nuevas métricas
        metricas = self._calcular_metricas_completas()
        
        # Actualizar cache
        self._metricas_cache = metricas
        self._ultima_actualizacion = ahora
        
        return metricas
    
    def _calcular_metricas_completas(self) -> MetricasSistema:
        """
        Calcula todas las métricas del sistema
        """
        metricas = MetricasSistema()
        
        # Métricas de usuarios
        self._calcular_metricas_usuarios(metricas)
        
        # Métricas de cursos y matrículas
        self._calcular_metricas_academicas(metricas)
        
        # Métricas de asistencia y notas (simuladas por ahora)
        self._calcular_metricas_rendimiento(metricas)
        
        # Detectar alertas del sistema
        self._detectar_alertas_sistema(metricas)
        
        # Actualizar fecha de cálculo
        metricas.actualizar_fecha_calculo()
        
        return metricas
    
    def _calcular_metricas_usuarios(self, metricas: MetricasSistema):
        """
        Calcula métricas relacionadas con usuarios
        """
        # Contar usuarios por rol y estado
        usuarios_stats = UsuarioModel.objects.aggregate(
            total_activos=Count('id', filter=Q(activo=True, is_active=True)),
            total_inactivos=Count('id', filter=Q(activo=False) | Q(is_active=False)),
            total_estudiantes=Count('id', filter=Q(rol='estudiante')),
            total_docentes=Count('id', filter=Q(rol='docente')),
            total_secretarias=Count('id', filter=Q(rol='secretaria')),
            total_administradores=Count('id', filter=Q(rol='admin'))
        )
        
        metricas.total_usuarios_activos = usuarios_stats['total_activos'] or 0
        metricas.total_usuarios_inactivos = usuarios_stats['total_inactivos'] or 0
        metricas.total_estudiantes = usuarios_stats['total_estudiantes'] or 0
        metricas.total_docentes = usuarios_stats['total_docentes'] or 0
        metricas.total_secretarias = usuarios_stats['total_secretarias'] or 0
        metricas.total_administradores = usuarios_stats['total_administradores'] or 0
        
        # Usuarios activos en la última semana
        hace_una_semana = timezone.now() - timedelta(days=7)
        metricas.usuarios_activos_ultima_semana = UsuarioModel.objects.filter(
            ultimo_acceso__gte=hace_una_semana
        ).count()
    
    def _calcular_metricas_academicas(self, metricas: MetricasSistema):
        """
        Calcula métricas académicas (cursos, matrículas, laboratorios)
        """
        # Contar matrículas activas
        matriculas_stats = MatriculaModel.objects.aggregate(
            total_activas=Count('id', filter=Q(estado='MATRICULADO')),
            total_cursos=Count('curso_codigo', distinct=True)
        )
        
        metricas.total_matriculas_activas = matriculas_stats['total_activas'] or 0
        metricas.total_cursos_activos = matriculas_stats['total_cursos'] or 0
        
        # Nuevas matrículas del mes
        hace_un_mes = timezone.now() - timedelta(days=30)
        metricas.nuevas_matriculas_mes = MatriculaModel.objects.filter(
            fecha_matricula__gte=hace_un_mes
        ).count()
        
        # Laboratorios (simulado por ahora - se implementará con el modelo real)
        metricas.total_laboratorios = 5  # Valor simulado
        metricas.total_reservas_pendientes = 3  # Valor simulado
        metricas.total_reservas_aprobadas = 12  # Valor simulado
        metricas.reservas_automaticas_hoy = 2  # Valor simulado
    
    def _calcular_metricas_rendimiento(self, metricas: MetricasSistema):
        """
        Calcula métricas de rendimiento académico
        """
        # Por ahora usamos valores simulados
        # TODO: Implementar cuando estén disponibles los modelos de asistencia y notas
        
        # Simular promedio de asistencia basado en matrículas activas
        total_matriculas = metricas.total_matriculas_activas
        if total_matriculas > 0:
            # Simular un promedio de asistencia entre 75% y 85%
            metricas.promedio_asistencia_global = 78.5
            metricas.promedio_notas_global = 14.2
        else:
            metricas.promedio_asistencia_global = 0.0
            metricas.promedio_notas_global = 0.0
    
    def _detectar_alertas_sistema(self, metricas: MetricasSistema):
        """
        Detecta y crea alertas del sistema basadas en las métricas
        """
        alertas = []
        
        # Alerta por usuarios inactivos
        if metricas.total_usuarios_inactivos > metricas.total_usuarios_activos:
            alerta = AlertaSistema()
            alerta.tipo = 'warning'
            alerta.titulo = 'Alto número de usuarios inactivos'
            alerta.descripcion = f'Hay {metricas.total_usuarios_inactivos} usuarios inactivos vs {metricas.total_usuarios_activos} activos'
            alerta.prioridad = 'media'
            alerta.fecha_creacion = timezone.now()
            alertas.append(alerta)
        
        # Alerta por baja asistencia
        if metricas.promedio_asistencia_global < 70.0:
            alerta = AlertaSistema()
            alerta.tipo = 'error'
            alerta.titulo = 'Promedio de asistencia bajo'
            alerta.descripcion = f'El promedio de asistencia global es {metricas.promedio_asistencia_global}%, por debajo del 70%'
            alerta.prioridad = 'alta'
            alerta.fecha_creacion = timezone.now()
            alertas.append(alerta)
        
        # Alerta por falta de actividad reciente
        if metricas.usuarios_activos_ultima_semana == 0:
            alerta = AlertaSistema()
            alerta.tipo = 'warning'
            alerta.titulo = 'Sin actividad reciente'
            alerta.descripcion = 'No hay usuarios activos en la última semana'
            alerta.prioridad = 'media'
            alerta.fecha_creacion = timezone.now()
            alertas.append(alerta)
        
        # Alerta por inconsistencias en datos (simulada)
        if metricas.total_estudiantes > 0 and metricas.total_matriculas_activas == 0:
            alerta = AlertaSistema()
            alerta.tipo = 'error'
            alerta.titulo = 'Inconsistencia en datos'
            alerta.descripcion = 'Hay estudiantes registrados pero sin matrículas activas'
            alerta.prioridad = 'alta'
            alerta.fecha_creacion = timezone.now()
            alertas.append(alerta)
        
        metricas.alertas_pendientes = alertas
    
    def obtener_metricas_dashboard_json(self) -> dict:
        """
        Obtiene las métricas formateadas para el dashboard en formato JSON
        """
        metricas = self.obtener_metricas_sistema()
        return metricas.obtener_metricas_dashboard()
    
    def limpiar_cache(self):
        """
        Limpia el cache de métricas forzando un recálculo en la próxima consulta
        """
        self._metricas_cache = None
        self._ultima_actualizacion = None