#!/usr/bin/python
# -*- coding: utf-8 -*-

from Dominio.Modelo.reporte.IReporteRepository import IReporteRepository


class ReporteRepositoryMySQL(IReporteRepository):
    def __init__(self):
        pass

    def agregar_reporte(reporte: Reporte): void(self, ):
        pass

    def obtener_por_id(id: str): Reporte(self, ):
        pass

    def actualizar_reporte(reporte: Reporte): void(self, ):
        pass

    def eliminar(id: str): void(self, ):
        pass

    def listar_por_tipo(tipo: TipoReporte): List<Reporte>(self, ):
        pass

    def listar_por_usuario(usuario_id: str): List<Reporte>(self, ):
        pass

    def listar_por_fecha(fecha_inicio: date, fecha_fin: date): List<Reporte>(self, ):
        pass

    def listar_todos(): List<Reporte>(self, ):
        pass

    def exportar_pdf(id: str): ArchivoPDF(self, ):
        pass

    def xportar_excel(id: str): ArchivoExcel(self, ):
        pass
