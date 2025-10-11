#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reservas.ISolicitudReservaRepository import ISolicitudReservaRepository


class SolicitudReservaRepositoryMySQL(ISolicitudReservaRepository):
    def __init__(self):
        pass

    def agregar(solicitud: SolicitudReserva): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def actualizar(solicitud: SolicitudReserva): void(self, ):
        pass

    def obtener_por_id(id: str): SolicitudReserva(self, ):
        pass

    def listar_por_usuario(usuario_id: str): List<SolicitudReserva>(self, ):
        pass

    def listar_por_estado(estado: EstadoSolicitud): List<SolicitudReserva>(self, ):
        pass

    def listar_pendientes(): List<SolicitudReserva>(self, ):
        pass

    def verificar_conflictos(recurso_id: str, fecha: date, horario: Horario): bool(self, ):
        pass

    def listar_todas(): List<SolicitudReserva>(self, ):
        pass
