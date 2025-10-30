#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class TipoInconsistencia(Enum):
    """Tipos de inconsistencias detectables en el sistema"""
    USUARIO_DUPLICADO = "usuario_duplicado"
    MATRICULA_INVALIDA = "matricula_invalida"
    RESERVA_CONFLICTO = "reserva_conflicto"
    DATOS_FALTANTES = "datos_faltantes"
    REFERENCIA_ROTA = "referencia_rota"
    CAPACIDAD_EXCEDIDA = "capacidad_excedida"
    FECHA_INVALIDA = "fecha_invalida"


class SeveridadInconsistencia(Enum):
    """Niveles de severidad para las inconsistencias"""
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class InconsistenciaSistema:
    """Representa una inconsistencia detectada en el sistema"""
    
    def __init__(self):
        self.id = None
        self.tipo: TipoInconsistencia = None
        self.severidad: SeveridadInconsistencia = SeveridadInconsistencia.MEDIA
        self.titulo = ""
        self.descripcion = ""
        self.entidad_afectada = ""  # tabla/modelo afectado
        self.registro_id = None  # ID del registro específico
        self.datos_adicionales: Dict[str, Any] = {}
        self.fecha_deteccion = None
        self.resuelto = False
        self.fecha_resolucion = None
        self.usuario_resolucion = None
        self.accion_correctiva = ""
    
    def marcar_como_resuelto(self, usuario: str, accion: str = ""):
        """Marca la inconsistencia como resuelta"""
        self.resuelto = True
        self.fecha_resolucion = datetime.now()
        self.usuario_resolucion = usuario
        self.accion_correctiva = accion
    
    def obtener_prioridad_numerica(self) -> int:
        """Obtiene la prioridad numérica para ordenamiento"""
        prioridades = {
            SeveridadInconsistencia.CRITICA: 4,
            SeveridadInconsistencia.ALTA: 3,
            SeveridadInconsistencia.MEDIA: 2,
            SeveridadInconsistencia.BAJA: 1
        }
        return prioridades.get(self.severidad, 1)


class DetectorInconsistencias:
    """Sistema de detección automática de inconsistencias"""
    
    def __init__(self):
        self.inconsistencias_detectadas: List[InconsistenciaSistema] = []
        self.reglas_validacion = {
            TipoInconsistencia.USUARIO_DUPLICADO: self._detectar_usuarios_duplicados,
            TipoInconsistencia.MATRICULA_INVALIDA: self._detectar_matriculas_invalidas,
            TipoInconsistencia.RESERVA_CONFLICTO: self._detectar_conflictos_reservas,
            TipoInconsistencia.DATOS_FALTANTES: self._detectar_datos_faltantes,
            TipoInconsistencia.REFERENCIA_ROTA: self._detectar_referencias_rotas,
            TipoInconsistencia.CAPACIDAD_EXCEDIDA: self._detectar_capacidad_excedida,
            TipoInconsistencia.FECHA_INVALIDA: self._detectar_fechas_invalidas
        }
    
    def ejecutar_deteccion_completa(self, datos_sistema: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Ejecuta todas las reglas de detección de inconsistencias"""
        self.inconsistencias_detectadas.clear()
        
        for tipo_inconsistencia, regla_validacion in self.reglas_validacion.items():
            try:
                inconsistencias = regla_validacion(datos_sistema)
                self.inconsistencias_detectadas.extend(inconsistencias)
            except Exception as e:
                # Crear inconsistencia por error en la validación
                error_inconsistencia = InconsistenciaSistema()
                error_inconsistencia.tipo = TipoInconsistencia.DATOS_FALTANTES
                error_inconsistencia.severidad = SeveridadInconsistencia.ALTA
                error_inconsistencia.titulo = f"Error en validación {tipo_inconsistencia.value}"
                error_inconsistencia.descripcion = f"Error al ejecutar regla de validación: {str(e)}"
                error_inconsistencia.fecha_deteccion = datetime.now()
                self.inconsistencias_detectadas.append(error_inconsistencia)
        
        return self.inconsistencias_detectadas
    
    def _detectar_usuarios_duplicados(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta usuarios con correos duplicados"""
        inconsistencias = []
        usuarios = datos.get('usuarios', [])
        
        correos_vistos = {}
        for usuario in usuarios:
            correo = usuario.get('correo_institucional', '').lower()
            if correo in correos_vistos:
                inconsistencia = InconsistenciaSistema()
                inconsistencia.tipo = TipoInconsistencia.USUARIO_DUPLICADO
                inconsistencia.severidad = SeveridadInconsistencia.ALTA
                inconsistencia.titulo = "Usuario duplicado detectado"
                inconsistencia.descripcion = f"Correo duplicado: {correo}"
                inconsistencia.entidad_afectada = "Usuario"
                inconsistencia.registro_id = usuario.get('id')
                inconsistencia.datos_adicionales = {
                    'correo_duplicado': correo,
                    'usuarios_afectados': [correos_vistos[correo], usuario.get('id')]
                }
                inconsistencia.fecha_deteccion = datetime.now()
                inconsistencias.append(inconsistencia)
            else:
                correos_vistos[correo] = usuario.get('id')
        
        return inconsistencias
    
    def _detectar_matriculas_invalidas(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta matrículas con referencias inválidas"""
        inconsistencias = []
        matriculas = datos.get('matriculas', [])
        usuarios_ids = {u.get('id') for u in datos.get('usuarios', [])}
        cursos_ids = {c.get('id') for c in datos.get('cursos', [])}
        
        for matricula in matriculas:
            usuario_id = matricula.get('usuario_id')
            curso_id = matricula.get('curso_id')
            
            if usuario_id not in usuarios_ids:
                inconsistencia = InconsistenciaSistema()
                inconsistencia.tipo = TipoInconsistencia.REFERENCIA_ROTA
                inconsistencia.severidad = SeveridadInconsistencia.CRITICA
                inconsistencia.titulo = "Matrícula con usuario inexistente"
                inconsistencia.descripcion = f"Matrícula {matricula.get('id')} referencia usuario inexistente {usuario_id}"
                inconsistencia.entidad_afectada = "Matricula"
                inconsistencia.registro_id = matricula.get('id')
                inconsistencia.fecha_deteccion = datetime.now()
                inconsistencias.append(inconsistencia)
            
            if curso_id not in cursos_ids:
                inconsistencia = InconsistenciaSistema()
                inconsistencia.tipo = TipoInconsistencia.REFERENCIA_ROTA
                inconsistencia.severidad = SeveridadInconsistencia.CRITICA
                inconsistencia.titulo = "Matrícula con curso inexistente"
                inconsistencia.descripcion = f"Matrícula {matricula.get('id')} referencia curso inexistente {curso_id}"
                inconsistencia.entidad_afectada = "Matricula"
                inconsistencia.registro_id = matricula.get('id')
                inconsistencia.fecha_deteccion = datetime.now()
                inconsistencias.append(inconsistencia)
        
        return inconsistencias
    
    def _detectar_conflictos_reservas(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta conflictos en reservas de laboratorios"""
        inconsistencias = []
        reservas = datos.get('reservas', [])
        
        # Agrupar reservas por laboratorio y fecha
        reservas_por_lab_fecha = {}
        for reserva in reservas:
            if reserva.get('estado') != 'aprobada':
                continue
                
            lab_id = reserva.get('laboratorio_id')
            fecha = reserva.get('fecha')
            hora_inicio = reserva.get('hora_inicio')
            hora_fin = reserva.get('hora_fin')
            
            key = f"{lab_id}_{fecha}"
            if key not in reservas_por_lab_fecha:
                reservas_por_lab_fecha[key] = []
            reservas_por_lab_fecha[key].append(reserva)
        
        # Detectar solapamientos
        for key, reservas_grupo in reservas_por_lab_fecha.items():
            if len(reservas_grupo) > 1:
                for i, reserva1 in enumerate(reservas_grupo):
                    for reserva2 in reservas_grupo[i+1:]:
                        if self._hay_solapamiento_horario(reserva1, reserva2):
                            inconsistencia = InconsistenciaSistema()
                            inconsistencia.tipo = TipoInconsistencia.RESERVA_CONFLICTO
                            inconsistencia.severidad = SeveridadInconsistencia.ALTA
                            inconsistencia.titulo = "Conflicto de reservas detectado"
                            inconsistencia.descripcion = f"Solapamiento entre reservas {reserva1.get('id')} y {reserva2.get('id')}"
                            inconsistencia.entidad_afectada = "Reserva"
                            inconsistencia.registro_id = reserva1.get('id')
                            inconsistencia.datos_adicionales = {
                                'reserva_conflicto': reserva2.get('id'),
                                'laboratorio': reserva1.get('laboratorio_id'),
                                'fecha': reserva1.get('fecha')
                            }
                            inconsistencia.fecha_deteccion = datetime.now()
                            inconsistencias.append(inconsistencia)
        
        return inconsistencias
    
    def _detectar_datos_faltantes(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta registros con datos obligatorios faltantes"""
        inconsistencias = []
        
        # Validar usuarios
        usuarios = datos.get('usuarios', [])
        for usuario in usuarios:
            campos_requeridos = ['correo_institucional', 'nombre', 'apellido', 'rol']
            for campo in campos_requeridos:
                if not usuario.get(campo):
                    inconsistencia = InconsistenciaSistema()
                    inconsistencia.tipo = TipoInconsistencia.DATOS_FALTANTES
                    inconsistencia.severidad = SeveridadInconsistencia.MEDIA
                    inconsistencia.titulo = f"Campo requerido faltante: {campo}"
                    inconsistencia.descripcion = f"Usuario {usuario.get('id')} no tiene {campo}"
                    inconsistencia.entidad_afectada = "Usuario"
                    inconsistencia.registro_id = usuario.get('id')
                    inconsistencia.fecha_deteccion = datetime.now()
                    inconsistencias.append(inconsistencia)
        
        return inconsistencias
    
    def _detectar_referencias_rotas(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta referencias a entidades inexistentes"""
        # Ya implementado parcialmente en _detectar_matriculas_invalidas
        return []
    
    def _detectar_capacidad_excedida(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta cuando se excede la capacidad de laboratorios"""
        inconsistencias = []
        reservas = datos.get('reservas', [])
        laboratorios = {lab.get('id'): lab for lab in datos.get('laboratorios', [])}
        
        for reserva in reservas:
            if reserva.get('estado') != 'aprobada':
                continue
                
            lab_id = reserva.get('laboratorio_id')
            participantes = reserva.get('numero_participantes', 0)
            
            if lab_id in laboratorios:
                capacidad_max = laboratorios[lab_id].get('capacidad_maxima', 0)
                if participantes > capacidad_max:
                    inconsistencia = InconsistenciaSistema()
                    inconsistencia.tipo = TipoInconsistencia.CAPACIDAD_EXCEDIDA
                    inconsistencia.severidad = SeveridadInconsistencia.ALTA
                    inconsistencia.titulo = "Capacidad de laboratorio excedida"
                    inconsistencia.descripcion = f"Reserva {reserva.get('id')} excede capacidad ({participantes}/{capacidad_max})"
                    inconsistencia.entidad_afectada = "Reserva"
                    inconsistencia.registro_id = reserva.get('id')
                    inconsistencia.datos_adicionales = {
                        'participantes': participantes,
                        'capacidad_maxima': capacidad_max,
                        'laboratorio_id': lab_id
                    }
                    inconsistencia.fecha_deteccion = datetime.now()
                    inconsistencias.append(inconsistencia)
        
        return inconsistencias
    
    def _detectar_fechas_invalidas(self, datos: Dict[str, Any]) -> List[InconsistenciaSistema]:
        """Detecta fechas inválidas o inconsistentes"""
        inconsistencias = []
        reservas = datos.get('reservas', [])
        
        for reserva in reservas:
            fecha = reserva.get('fecha')
            hora_inicio = reserva.get('hora_inicio')
            hora_fin = reserva.get('hora_fin')
            
            # Validar que hora_fin > hora_inicio
            if hora_inicio and hora_fin and hora_inicio >= hora_fin:
                inconsistencia = InconsistenciaSistema()
                inconsistencia.tipo = TipoInconsistencia.FECHA_INVALIDA
                inconsistencia.severidad = SeveridadInconsistencia.MEDIA
                inconsistencia.titulo = "Horario inválido en reserva"
                inconsistencia.descripcion = f"Reserva {reserva.get('id')} tiene hora fin antes o igual a hora inicio"
                inconsistencia.entidad_afectada = "Reserva"
                inconsistencia.registro_id = reserva.get('id')
                inconsistencia.fecha_deteccion = datetime.now()
                inconsistencias.append(inconsistencia)
        
        return inconsistencias
    
    def _hay_solapamiento_horario(self, reserva1: Dict, reserva2: Dict) -> bool:
        """Verifica si dos reservas tienen solapamiento horario"""
        inicio1 = reserva1.get('hora_inicio')
        fin1 = reserva1.get('hora_fin')
        inicio2 = reserva2.get('hora_inicio')
        fin2 = reserva2.get('hora_fin')
        
        if not all([inicio1, fin1, inicio2, fin2]):
            return False
        
        # Hay solapamiento si el inicio de una está antes del fin de la otra
        return not (fin1 <= inicio2 or fin2 <= inicio1)
    
    def obtener_inconsistencias_por_severidad(self, severidad: SeveridadInconsistencia) -> List[InconsistenciaSistema]:
        """Obtiene inconsistencias filtradas por severidad"""
        return [inc for inc in self.inconsistencias_detectadas if inc.severidad == severidad]
    
    def obtener_resumen_inconsistencias(self) -> Dict[str, int]:
        """Obtiene un resumen de inconsistencias por tipo y severidad"""
        resumen = {
            'total': len(self.inconsistencias_detectadas),
            'por_severidad': {},
            'por_tipo': {}
        }
        
        for inconsistencia in self.inconsistencias_detectadas:
            # Contar por severidad
            sev = inconsistencia.severidad.value
            resumen['por_severidad'][sev] = resumen['por_severidad'].get(sev, 0) + 1
            
            # Contar por tipo
            tipo = inconsistencia.tipo.value
            resumen['por_tipo'][tipo] = resumen['por_tipo'].get(tipo, 0) + 1
        
        return resumen