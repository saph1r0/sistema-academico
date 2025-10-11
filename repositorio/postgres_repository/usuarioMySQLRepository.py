#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Usuario.IUsuarioRepository import IUsuarioRepository


class UsuarioMySQLRepository(IUsuarioRepository):
    def __init__(self):
        pass

    def agregar(usuario): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def obtener_por_id(id: str): Usuario(self, ):
        pass

    def obtener_por_correo(correo: str): Usuario(self, ):
        pass

    def listar_activos(): List<Usuario(self, ):
        pass

    def listar_inactivos(): List<Usuario>(self, ):
        pass

    def listar_por_rol(rol: Rol): List<Usuario>(self, ):
        pass

    def buscar_por_id(id: str): Usuario(self, ):
        pass

    def actualizar_estado(id: str, activo: bool): void(self, ):
        pass

    def actualizar_ultimo_acceso(id: str, acceso: datetime): void(self, ):
        pass
