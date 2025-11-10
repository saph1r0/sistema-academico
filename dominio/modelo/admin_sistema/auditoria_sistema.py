#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class TipoAccionAuditoria(Enum):
    """Tipos de acciones auditables en el sistema"""
    # Gestión de usuarios
    USUARIO_ACTIVADO = "usuario_activado"
    USUARIO_DESACTIVADO = "usuario_desactivado"
    USUARIO_MODIFICADO = "usuario_modificado"
    USUARIO_ELIMINADO = "usuario_eliminado"
    
    # Configuración del sistema
    CONFIGURACION_MODIFICADA = "configuracion_modificada"
    PARAMETRO_ACTUALIZADO = "parametro_actualizado"
    
    # Reportes y consultas
    REPORTE_GENERADO = "reporte_generado"
    REPORTE_DESCARGADO = "reporte_descargado"
    CONSULTA_REALIZADA = "consulta_realizada"
    
    # Gestión de alertas
    ALERTA_RESUELTA = "alerta_resuelta"
    ALERTA_IGNORADA = "alerta_ignorada"
    INCONSISTENCIA_CORREGIDA = "inconsistencia_corregida"
    
    # Acceso y autenticación
    LOGIN_ADMIN = "login_admin"
    LOGOUT_ADMIN = "logout_admin"
    ACCESO_DENEGADO = "acceso_denegado"
    
    # Operaciones del sistema
    BACKUP_EJECUTADO = "backup_ejecutado"
    MANTENIMIENTO_INICIADO = "mantenimiento_iniciado"
    MANTENIMIENTO_FINALIZADO = "mantenimiento_finalizado"
    
    # Monitoreo
    DETECCION_INCONSISTENCIAS = "deteccion_inconsistencias"
    REVISION_SISTEMA = "revision_sistema"


class NivelAuditoria(Enum):
    """Niveles de importancia para las acciones de auditoría"""
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"
    INFO = "info"


class RegistroAuditoria:
    """Representa un registro individual de auditoría"""
    
    def __init__(self):
        self.id = None
        self.timestamp = None
        self.usuario_id = None
        self.usuario_nombre = ""
        self.usuario_rol = ""
        self.accion: TipoAccionAuditoria = None
        self.nivel: NivelAuditoria = NivelAuditoria.INFO
        
        # Detalles de la acción
        self.descripcion = ""
        self.entidad_afectada = ""  # Tipo de entidad (Usuario, Configuracion, etc.)
        self.entidad_id = None  # ID específico de la entidad
        self.modulo_origen = ""  # Módulo que ejecutó la acción
        
        # Contexto técnico
        self.ip_address = ""
        self.user_agent = ""
        self.session_id = ""
        
        # Datos de la acción
        self.datos_anteriores: Dict[str, Any] = {}  # Estado antes del cambio
        self.datos_nuevos: Dict[str, Any] = {}  # Estado después del cambio
        self.parametros_accion: Dict[str, Any] = {}  # Parámetros usados en la acción
        
        # Resultado
        self.exitoso = True
        self.mensaje_error = ""
        self.codigo_error = None
        
        # Metadatos adicionales
        self.duracion_ms = None  # Duración de la operación en milisegundos
        self.impacto_estimado = "bajo"  # bajo, medio, alto
        self.requiere_revision = False
        self.tags: List[str] = []  # Etiquetas para categorización
    
    def marcar_como_critico(self, razon: str = ""):
        """Marca el registro como crítico y requiere revisión"""
        self.nivel = NivelAuditoria.CRITICO
        self.requiere_revision = True
        if razon:
            self.tags.append(f"critico:{razon}")
    
    def agregar_tag(self, tag: str):
        """Agrega una etiqueta al registro"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def obtener_resumen(self) -> str:
        """Obtiene un resumen legible del registro"""
        return f"{self.usuario_nombre} ({self.usuario_rol}) - {self.accion.value}: {self.descripcion}"
    
    def obtener_cambios_realizados(self) -> Dict[str, Any]:
        """Obtiene un resumen de los cambios realizados"""
        cambios = {}
        
        for campo, valor_nuevo in self.datos_nuevos.items():
            valor_anterior = self.datos_anteriores.get(campo)
            if valor_anterior != valor_nuevo:
                cambios[campo] = {
                    'anterior': valor_anterior,
                    'nuevo': valor_nuevo
                }
        
        return cambios
    
    def serializar_para_log(self) -> str:
        """Serializa el registro para logging estructurado"""
        log_data = {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'usuario': {
                'id': self.usuario_id,
                'nombre': self.usuario_nombre,
                'rol': self.usuario_rol
            },
            'accion': self.accion.value if self.accion else None,
            'nivel': self.nivel.value if self.nivel else None,
            'descripcion': self.descripcion,
            'entidad': {
                'tipo': self.entidad_afectada,
                'id': self.entidad_id
            },
            'contexto': {
                'ip': self.ip_address,
                'modulo': self.modulo_origen,
                'session': self.session_id
            },
            'resultado': {
                'exitoso': self.exitoso,
                'error': self.mensaje_error,
                'duracion_ms': self.duracion_ms
            },
            'cambios': self.obtener_cambios_realizados(),
            'tags': self.tags
        }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class SistemaAuditoria:
    """Sistema de auditoría para el panel administrativo"""
    
    def __init__(self):
        self.registros: List[RegistroAuditoria] = []
        self.configuracion = {
            'max_registros_memoria': 1000,
            'dias_retencion': 90,
            'log_file_path': 'logs/admin_panel.log',
            'niveles_log_archivo': [NivelAuditoria.CRITICO, NivelAuditoria.ALTO, NivelAuditoria.MEDIO],
            'auto_backup_registros': True,
            'alertar_acciones_criticas': True
        }
        self.estadisticas = {
            'total_registros': 0,
            'acciones_por_usuario': {},
            'acciones_por_tipo': {},
            'errores_detectados': 0
        }
    
    def registrar_accion(self, 
                        usuario_id: str,
                        usuario_nombre: str,
                        usuario_rol: str,
                        accion: TipoAccionAuditoria,
                        descripcion: str,
                        entidad_afectada: str = "",
                        entidad_id: str = None,
                        modulo_origen: str = "",
                        datos_anteriores: Dict[str, Any] = None,
                        datos_nuevos: Dict[str, Any] = None,
                        parametros: Dict[str, Any] = None,
                        contexto_request: Dict[str, str] = None) -> RegistroAuditoria:
        """Registra una nueva acción de auditoría"""
        
        registro = RegistroAuditoria()
        registro.timestamp = datetime.now()
        registro.usuario_id = usuario_id
        registro.usuario_nombre = usuario_nombre
        registro.usuario_rol = usuario_rol
        registro.accion = accion
        registro.descripcion = descripcion
        registro.entidad_afectada = entidad_afectada
        registro.entidad_id = entidad_id
        registro.modulo_origen = modulo_origen
        
        # Datos de la acción
        registro.datos_anteriores = datos_anteriores or {}
        registro.datos_nuevos = datos_nuevos or {}
        registro.parametros_accion = parametros or {}
        
        # Contexto de la request
        if contexto_request:
            registro.ip_address = contexto_request.get('ip', '')
            registro.user_agent = contexto_request.get('user_agent', '')
            registro.session_id = contexto_request.get('session_id', '')
        
        # Determinar nivel de importancia
        registro.nivel = self._determinar_nivel_accion(accion, entidad_afectada)
        
        # Determinar impacto
        registro.impacto_estimado = self._calcular_impacto(accion, datos_anteriores, datos_nuevos)
        
        # Agregar tags automáticos
        self._agregar_tags_automaticos(registro)
        
        # Agregar a la colección
        self.registros.append(registro)
        self._actualizar_estadisticas(registro)
        
        # Log a archivo si es necesario
        if registro.nivel in self.configuracion['niveles_log_archivo']:
            self._escribir_a_log_file(registro)
        
        # Limpiar registros antiguos si es necesario
        if len(self.registros) > self.configuracion['max_registros_memoria']:
            self._limpiar_registros_antiguos()
        
        return registro
    
    def registrar_login_admin(self, usuario_id: str, usuario_nombre: str, ip: str, exitoso: bool = True, error: str = "") -> RegistroAuditoria:
        """Registra un intento de login administrativo"""
        accion = TipoAccionAuditoria.LOGIN_ADMIN if exitoso else TipoAccionAuditoria.ACCESO_DENEGADO
        descripcion = f"Login administrativo {'exitoso' if exitoso else 'fallido'}"
        
        registro = self.registrar_accion(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            usuario_rol="admin",
            accion=accion,
            descripcion=descripcion,
            modulo_origen="AuthenticationSystem",
            contexto_request={'ip': ip}
        )
        
        if not exitoso:
            registro.exitoso = False
            registro.mensaje_error = error
            registro.nivel = NivelAuditoria.ALTO
            registro.agregar_tag("seguridad")
        
        return registro
    
    def registrar_cambio_usuario(self, admin_id: str, admin_nombre: str, usuario_afectado_id: str, 
                                accion: TipoAccionAuditoria, datos_anteriores: Dict = None, 
                                datos_nuevos: Dict = None) -> RegistroAuditoria:
        """Registra cambios en usuarios del sistema"""
        descripcion_map = {
            TipoAccionAuditoria.USUARIO_ACTIVADO: "Usuario activado",
            TipoAccionAuditoria.USUARIO_DESACTIVADO: "Usuario desactivado",
            TipoAccionAuditoria.USUARIO_MODIFICADO: "Usuario modificado"
        }
        
        return self.registrar_accion(
            usuario_id=admin_id,
            usuario_nombre=admin_nombre,
            usuario_rol="admin",
            accion=accion,
            descripcion=descripcion_map.get(accion, "Acción en usuario"),
            entidad_afectada="Usuario",
            entidad_id=usuario_afectado_id,
            modulo_origen="UserManagement",
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos
        )
    
    def registrar_generacion_reporte(self, admin_id: str, admin_nombre: str, tipo_reporte: str, 
                                   parametros: Dict[str, Any], exitoso: bool = True, error: str = "") -> RegistroAuditoria:
        """Registra la generación de reportes"""
        registro = self.registrar_accion(
            usuario_id=admin_id,
            usuario_nombre=admin_nombre,
            usuario_rol="admin",
            accion=TipoAccionAuditoria.REPORTE_GENERADO,
            descripcion=f"Reporte generado: {tipo_reporte}",
            entidad_afectada="Reporte",
            modulo_origen="ReportGeneration",
            parametros=parametros
        )
        
        if not exitoso:
            registro.exitoso = False
            registro.mensaje_error = error
            registro.nivel = NivelAuditoria.MEDIO
        
        return registro
    
    def registrar_cambio_configuracion(self, admin_id: str, admin_nombre: str, parametro: str,
                                     valor_anterior: Any, valor_nuevo: Any) -> RegistroAuditoria:
        """Registra cambios en la configuración del sistema"""
        return self.registrar_accion(
            usuario_id=admin_id,
            usuario_nombre=admin_nombre,
            usuario_rol="admin",
            accion=TipoAccionAuditoria.CONFIGURACION_MODIFICADA,
            descripcion=f"Configuración modificada: {parametro}",
            entidad_afectada="Configuracion",
            entidad_id=parametro,
            modulo_origen="SystemConfiguration",
            datos_anteriores={parametro: valor_anterior},
            datos_nuevos={parametro: valor_nuevo}
        )
    
    def obtener_registros_usuario(self, usuario_id: str, limite: int = 50) -> List[RegistroAuditoria]:
        """Obtiene los registros de auditoría de un usuario específico"""
        registros_usuario = [r for r in self.registros if r.usuario_id == usuario_id]
        registros_usuario.sort(key=lambda x: x.timestamp, reverse=True)
        return registros_usuario[:limite]
    
    def obtener_registros_por_entidad(self, entidad_tipo: str, entidad_id: str = None) -> List[RegistroAuditoria]:
        """Obtiene registros filtrados por entidad afectada"""
        registros = [r for r in self.registros if r.entidad_afectada == entidad_tipo]
        
        if entidad_id:
            registros = [r for r in registros if r.entidad_id == entidad_id]
        
        registros.sort(key=lambda x: x.timestamp, reverse=True)
        return registros
    
    def obtener_registros_criticos(self, limite: int = 20) -> List[RegistroAuditoria]:
        """Obtiene los registros críticos que requieren revisión"""
        registros_criticos = [r for r in self.registros 
                            if r.nivel == NivelAuditoria.CRITICO or r.requiere_revision]
        registros_criticos.sort(key=lambda x: x.timestamp, reverse=True)
        return registros_criticos[:limite]
    
    def obtener_estadisticas_auditoria(self, dias: int = 30) -> Dict[str, Any]:
        """Obtiene estadísticas de auditoría para un período"""
        fecha_limite = datetime.now() - timedelta(days=dias)
        registros_periodo = [r for r in self.registros if r.timestamp >= fecha_limite]
        
        estadisticas = {
            'total_acciones': len(registros_periodo),
            'acciones_por_dia': {},
            'usuarios_mas_activos': {},
            'acciones_por_tipo': {},
            'acciones_por_nivel': {},
            'errores_detectados': len([r for r in registros_periodo if not r.exitoso]),
            'acciones_criticas': len([r for r in registros_periodo if r.nivel == NivelAuditoria.CRITICO])
        }
        
        # Agrupar por día
        for registro in registros_periodo:
            fecha_str = registro.timestamp.strftime('%Y-%m-%d')
            estadisticas['acciones_por_dia'][fecha_str] = estadisticas['acciones_por_dia'].get(fecha_str, 0) + 1
        
        # Usuarios más activos
        for registro in registros_periodo:
            usuario = registro.usuario_nombre
            estadisticas['usuarios_mas_activos'][usuario] = estadisticas['usuarios_mas_activos'].get(usuario, 0) + 1
        
        # Acciones por tipo
        for registro in registros_periodo:
            tipo = registro.accion.value
            estadisticas['acciones_por_tipo'][tipo] = estadisticas['acciones_por_tipo'].get(tipo, 0) + 1
        
        # Acciones por nivel
        for registro in registros_periodo:
            nivel = registro.nivel.value
            estadisticas['acciones_por_nivel'][nivel] = estadisticas['acciones_por_nivel'].get(nivel, 0) + 1
        
        return estadisticas
    
    def buscar_registros(self, filtros: Dict[str, Any], limite: int = 100) -> List[RegistroAuditoria]:
        """Busca registros con filtros específicos"""
        registros_filtrados = self.registros.copy()
        
        # Filtrar por usuario
        if 'usuario_id' in filtros:
            registros_filtrados = [r for r in registros_filtrados if r.usuario_id == filtros['usuario_id']]
        
        # Filtrar por acción
        if 'accion' in filtros:
            registros_filtrados = [r for r in registros_filtrados if r.accion.value == filtros['accion']]
        
        # Filtrar por nivel
        if 'nivel' in filtros:
            registros_filtrados = [r for r in registros_filtrados if r.nivel.value == filtros['nivel']]
        
        # Filtrar por entidad
        if 'entidad_afectada' in filtros:
            registros_filtrados = [r for r in registros_filtrados if r.entidad_afectada == filtros['entidad_afectada']]
        
        # Filtrar por rango de fechas
        if 'fecha_inicio' in filtros:
            registros_filtrados = [r for r in registros_filtrados if r.timestamp >= filtros['fecha_inicio']]
        
        if 'fecha_fin' in filtros:
            registros_filtrados = [r for r in registros_filtrados if r.timestamp <= filtros['fecha_fin']]
        
        # Filtrar por texto en descripción
        if 'texto' in filtros:
            texto = filtros['texto'].lower()
            registros_filtrados = [r for r in registros_filtrados 
                                 if texto in r.descripcion.lower() or texto in r.usuario_nombre.lower()]
        
        registros_filtrados.sort(key=lambda x: x.timestamp, reverse=True)
        return registros_filtrados[:limite]
    
    def _determinar_nivel_accion(self, accion: TipoAccionAuditoria, entidad: str) -> NivelAuditoria:
        """Determina el nivel de importancia de una acción"""
        acciones_criticas = [
            TipoAccionAuditoria.USUARIO_ELIMINADO,
            TipoAccionAuditoria.CONFIGURACION_MODIFICADA,
            TipoAccionAuditoria.ACCESO_DENEGADO
        ]
        
        acciones_altas = [
            TipoAccionAuditoria.USUARIO_DESACTIVADO,
            TipoAccionAuditoria.PARAMETRO_ACTUALIZADO,
            TipoAccionAuditoria.INCONSISTENCIA_CORREGIDA
        ]
        
        if accion in acciones_criticas:
            return NivelAuditoria.CRITICO
        elif accion in acciones_altas:
            return NivelAuditoria.ALTO
        elif accion in [TipoAccionAuditoria.USUARIO_ACTIVADO, TipoAccionAuditoria.REPORTE_GENERADO]:
            return NivelAuditoria.MEDIO
        else:
            return NivelAuditoria.BAJO
    
    def _calcular_impacto(self, accion: TipoAccionAuditoria, datos_anteriores: Dict, datos_nuevos: Dict) -> str:
        """Calcula el impacto estimado de una acción"""
        acciones_alto_impacto = [
            TipoAccionAuditoria.CONFIGURACION_MODIFICADA,
            TipoAccionAuditoria.USUARIO_ELIMINADO
        ]
        
        if accion in acciones_alto_impacto:
            return "alto"
        
        # Calcular impacto basado en cantidad de cambios
        if datos_anteriores and datos_nuevos:
            cambios = len([k for k in datos_nuevos.keys() if datos_anteriores.get(k) != datos_nuevos[k]])
            if cambios > 3:
                return "medio"
        
        return "bajo"
    
    def _agregar_tags_automaticos(self, registro: RegistroAuditoria):
        """Agrega tags automáticos basados en la acción"""
        # Tags por tipo de acción
        if registro.accion in [TipoAccionAuditoria.LOGIN_ADMIN, TipoAccionAuditoria.ACCESO_DENEGADO]:
            registro.agregar_tag("autenticacion")
        
        if "usuario" in registro.accion.value:
            registro.agregar_tag("gestion_usuarios")
        
        if "configuracion" in registro.accion.value:
            registro.agregar_tag("configuracion_sistema")
        
        if "reporte" in registro.accion.value:
            registro.agregar_tag("reportes")
        
        # Tags por nivel
        if registro.nivel == NivelAuditoria.CRITICO:
            registro.agregar_tag("critico")
            registro.requiere_revision = True
    
    def _actualizar_estadisticas(self, registro: RegistroAuditoria):
        """Actualiza las estadísticas del sistema"""
        self.estadisticas['total_registros'] += 1
        
        # Estadísticas por usuario
        usuario = registro.usuario_nombre
        if usuario not in self.estadisticas['acciones_por_usuario']:
            self.estadisticas['acciones_por_usuario'][usuario] = 0
        self.estadisticas['acciones_por_usuario'][usuario] += 1
        
        # Estadísticas por tipo
        tipo = registro.accion.value
        if tipo not in self.estadisticas['acciones_por_tipo']:
            self.estadisticas['acciones_por_tipo'][tipo] = 0
        self.estadisticas['acciones_por_tipo'][tipo] += 1
        
        # Contar errores
        if not registro.exitoso:
            self.estadisticas['errores_detectados'] += 1
    
    def _escribir_a_log_file(self, registro: RegistroAuditoria):
        """Escribe el registro a un archivo de log"""
        try:
            import os
            log_dir = os.path.dirname(self.configuracion['log_file_path'])
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            with open(self.configuracion['log_file_path'], 'a', encoding='utf-8') as f:
                f.write(registro.serializar_para_log() + '\n')
        except Exception as e:
            # En caso de error, no fallar la operación principal
            pass
    
    def _limpiar_registros_antiguos(self):
        """Limpia registros antiguos de la memoria"""
        fecha_limite = datetime.now() - timedelta(days=self.configuracion['dias_retencion'])
        self.registros = [r for r in self.registros if r.timestamp >= fecha_limite]