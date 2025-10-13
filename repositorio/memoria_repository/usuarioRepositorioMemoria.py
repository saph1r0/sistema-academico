#!/usr/bin/python
# -*- coding: utf-8 -*-

from dominio.modelo.usuario.iUsuarioRepository import IUsuarioRepository
from dominio.modelo.usuario.usuario import Usuario
from typing import List


class UsuarioRepositorioMemoria(IUsuarioRepository):
    def __init__(self):
        self.usuarios: List[Usuario] = []

    def agregar(self, usuario: Usuario):
        """Agrega un usuario a la lista en memoria"""
        self.usuarios.append(usuario)

    def obtener_por_id(self, id: str) -> Usuario | None:
        """Busca usuario por ID"""
        return next((u for u in self.usuarios if getattr(u, "id", None) == id), None)

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        """Busca usuario por correo"""
        return next((u for u in self.usuarios if getattr(u, "correo_institucional", None) == correo), None)

    def eliminar(self, id: str):
        """Elimina usuario por ID"""
        self.usuarios = [u for u in self.usuarios if getattr(u, "id", None) != id]

    def listar_activos(self) -> List[Usuario]:
        """Devuelve usuarios activos"""
        return [u for u in self.usuarios if getattr(u, "activo", False)]

    def listar_por_rol(self, rol: str) -> List[Usuario]:
        """Devuelve usuarios por rol"""
        return [u for u in self.usuarios if getattr(u, "rol", None) == rol]

    def buscar_por_id(self, id: str) -> Usuario | None:
        """Alias de obtener_por_id"""
        return self.obtener_por_id(id)
