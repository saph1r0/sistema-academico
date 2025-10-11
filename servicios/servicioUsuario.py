#!/usr/bin/python
# -*- coding: utf-8 -*-

class ServicioUsuario:
    def __init__(self):
        self._usuario_repo = None
        self._estudiante_repo = None
        self._docente_repo = None

    def login(self, correo, contraseña):
        pass

    def logout(self, token):
        pass

    def validar_sesion_activa(self, token):
        pass

    def bloquear_cuenta(self, correo):
        pass

    def desbloquear_cuenta(self, correo):
        pass

    def activar_usuario(self, usuario_id):
        pass

    def desactivar_usuario(self, usuario_id, motivo):
        pass

    def obtener_usuario_por_correo(self, correo):
        pass

    def obtener_usuario_por_id(self, usuario_id):
        pass
