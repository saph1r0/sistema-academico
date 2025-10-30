#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.Usuario.Usuario import Usuario


class Admin(Usuario):
    def __init__(self):
        self.nivel_ acceso = None

    def activa_usuario(self, user):
        pass

    def desactiva_usuario(self, user):
        pass
