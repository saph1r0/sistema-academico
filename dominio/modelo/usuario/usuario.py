#!/usr/bin/python
# -*- coding: utf-8 -*-

class Usuario:
    def __init__(self):
        self.id = None
        self.correo_institucional = None
        self.nombre = None
        self.apellido = None
        self.contrasena_hash = None
        self.activo = None
        self.ultimo_acceso = None

    def autenticar(self, credenciales):
        pass

    def activar(self, ):
        pass

    def desactivar(self, ):
        pass
