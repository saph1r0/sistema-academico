#!/usr/bin/python
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from typing import List
from dominio.modelo.usuario.usuario import Usuario
from dominio.modelo.usuario.rol import Rol   # o RolUsuario, según como lo tengas definido

class IUsuarioRepository(ABC):

    @abstractmethod
    def agregar(self, usuario: Usuario) -> None:
        pass

    @abstractmethod
    def obtener_por_id(self, id: str) -> Usuario | None:
        pass

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Usuario | None:
        pass

    @abstractmethod
    def eliminar(self, id: str) -> None:
        pass

    @abstractmethod
    def listar_activos(self) -> List[Usuario]:
        pass

    @abstractmethod
    def listar_por_rol(self, rol: Rol) -> List[Usuario]:
        pass

    @abstractmethod
    def buscar_por_id(self, id: str) -> Usuario | None:
        pass
