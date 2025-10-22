#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, date, time, timedelta
from django.db.models import Q, Count, Avg
from django.utils import timezone
from repositorio.postgres_repository.models import LaboratorioModel, ReservaModel, UsuarioModel


class ServicioReservas:
    def __init__(self):
        self._reserva_repo = None
        self._ambiente_repo = None

    def consultar_disponibilidad(self, fecha, inicio, fin, tipo=None):
        """Consulta la disponibilidad de laboratorios para una fecha y horario específico"""
        laboratorios_query = LaboratorioModel.objects.filter(activo=True)
        
        if tipo:
            laboratorios_query = laboratorios_query.filter(tipo=tipo)
        
        disponibilidad = []
        
        for laboratorio in laboratorios_query:
            # Verificar si hay conflictos en el horario solicitado
            conflictos = ReservaModel.objects.filter(
                laboratorio=laboratorio,
                fecha_reserva=fecha,
                estado__in=['APROBADA', 'APROBADA_MANUAL'],
                hora_inicio__lt=fin,
                hora_fin__gt=inicio
            ).exists()
            
            disponibilidad.append({
                'laboratorio': laboratorio,
                'disponible': not conflictos,
                'reservas_dia': self._obtener_reservas_dia(laboratorio, fecha)
            })
        
        return disponibilidad

    def reservar_ambiente(self, docente_id, ambiente_id, fecha, inicio, fin, proposito):
        """Crea una nueva reserva de ambiente"""
        try:
            docente = UsuarioModel.objects.get(id=docente_id, rol='docente')
            laboratorio = LaboratorioModel.objects.get(id=ambiente_id, activo=True)
            
            # Crear la reserva
            reserva = ReservaModel(
                laboratorio=laboratorio,
                docente=docente,
                fecha_reserva=fecha,
                hora_inicio=inicio,
                hora_fin=fin,
                proposito=proposito
            )
            
            # Verificar conflictos
            if reserva.tiene_conflicto():
                reserva.estado = 'RECHAZADA'
                reserva.motivo_rechazo = 'Conflicto de horario con otra reserva'
            else:
                # Aprobar automáticamente si no hay conflictos
                reserva.estado = 'APROBADA'
                reserva.aprobada_automaticamente = True
            
            reserva.save()
            return reserva
            
        except (UsuarioModel.DoesNotExist, LaboratorioModel.DoesNotExist) as e:
            raise ValueError(f"Error en la reserva: {str(e)}")

    def verificar_conflicto(self, ambiente_id, fecha, inicio, fin, reserva_id=None):
        """Verifica si existe conflicto con otras reservas"""
        conflictos = ReservaModel.objects.filter(
            laboratorio_id=ambiente_id,
            fecha_reserva=fecha,
            estado__in=['APROBADA', 'APROBADA_MANUAL'],
            hora_inicio__lt=fin,
            hora_fin__gt=inicio
        )
        
        if reserva_id:
            conflictos = conflictos.exclude(id=reserva_id)
        
        return conflictos.exists()

    def obtener_laboratorios_activos(self):
        """Obtiene todos los laboratorios activos con sus estadísticas"""
        laboratorios = LaboratorioModel.objects.filter(activo=True).annotate(
            total_reservas=Count('reservas'),
            reservas_pendientes=Count('reservas', filter=Q(reservas__estado='PENDIENTE')),
            reservas_aprobadas=Count('reservas', filter=Q(reservas__estado__in=['APROBADA', 'APROBADA_MANUAL']))
        ).order_by('nombre')
        
        return laboratorios

    def obtener_reservas_recientes(self, dias=7):
        """Obtiene las reservas más recientes"""
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        return ReservaModel.objects.filter(
            fecha_solicitud__gte=fecha_limite
        ).select_related('laboratorio', 'docente').order_by('-fecha_solicitud')

    def obtener_conflictos_activos(self):
        """Obtiene reservas con conflictos activos"""
        conflictos = []
        reservas_activas = ReservaModel.objects.filter(
            estado__in=['PENDIENTE', 'APROBADA', 'APROBADA_MANUAL'],
            fecha_reserva__gte=date.today()
        ).select_related('laboratorio', 'docente')
        
        for reserva in reservas_activas:
            if reserva.tiene_conflicto():
                conflictos.append(reserva)
        
        return conflictos

    def obtener_estadisticas_uso(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene estadísticas de uso de laboratorios"""
        if not fecha_inicio:
            fecha_inicio = date.today() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = date.today()
        
        reservas = ReservaModel.objects.filter(
            fecha_reserva__range=[fecha_inicio, fecha_fin],
            estado__in=['APROBADA', 'APROBADA_MANUAL', 'COMPLETADA']
        )
        
        estadisticas = {
            'total_reservas': reservas.count(),
            'reservas_por_laboratorio': {},
            'reservas_por_tipo': {},
            'promedio_duracion': 0,
            'tasa_aprobacion_automatica': 0
        }
        
        # Estadísticas por laboratorio
        for laboratorio in LaboratorioModel.objects.filter(activo=True):
            reservas_lab = reservas.filter(laboratorio=laboratorio)
            estadisticas['reservas_por_laboratorio'][laboratorio.nombre] = {
                'total': reservas_lab.count(),
                'duracion_promedio': self._calcular_duracion_promedio(reservas_lab)
            }
        
        # Estadísticas por tipo
        for tipo, nombre_tipo in LaboratorioModel.TIPOS_LABORATORIO:
            reservas_tipo = reservas.filter(laboratorio__tipo=tipo)
            estadisticas['reservas_por_tipo'][nombre_tipo] = reservas_tipo.count()
        
        # Promedio de duración
        duraciones = [r.duracion_horas() for r in reservas if r.duracion_horas() > 0]
        if duraciones:
            estadisticas['promedio_duracion'] = sum(duraciones) / len(duraciones)
        
        # Tasa de aprobación automática
        total_reservas = reservas.count()
        if total_reservas > 0:
            automaticas = reservas.filter(aprobada_automaticamente=True).count()
            estadisticas['tasa_aprobacion_automatica'] = (automaticas / total_reservas) * 100
        
        return estadisticas

    def _obtener_reservas_dia(self, laboratorio, fecha):
        """Obtiene las reservas de un laboratorio para un día específico"""
        return ReservaModel.objects.filter(
            laboratorio=laboratorio,
            fecha_reserva=fecha,
            estado__in=['PENDIENTE', 'APROBADA', 'APROBADA_MANUAL']
        ).order_by('hora_inicio')

    def _calcular_duracion_promedio(self, reservas):
        """Calcula la duración promedio de un conjunto de reservas"""
        duraciones = [r.duracion_horas() for r in reservas if r.duracion_horas() > 0]
        return sum(duraciones) / len(duraciones) if duraciones else 0
