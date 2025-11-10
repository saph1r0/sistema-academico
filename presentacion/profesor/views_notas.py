#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para gestión de notas del profesor
Incluye subida de Excel, estadísticas y gráficos
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import json
import io
import xlsxwriter

from .mixins import ProfesorRequiredMixin
from servicios.servicioNotas import servicio_notas


class ProfesorNotasView(ProfesorRequiredMixin, TemplateView):
    """Vista principal para gestión de notas"""
    template_name = 'profesor/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener el profesor
            teacher = self.request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener cursos del profesor
            cursos = servicio_notas.obtener_cursos_profesor(teacher_id)
            
            # Si hay cursos, obtener estadísticas del primer curso por defecto
            curso_seleccionado = None
            estadisticas = {}
            
            if cursos:
                curso_id = self.request.GET.get('curso_id', cursos[0]['course_id'])
                curso_seleccionado = next((c for c in cursos if c['course_id'] == curso_id), cursos[0])
                
                # Obtener estadísticas por fase
                estadisticas = {
                    'primera': servicio_notas.obtener_estadisticas_curso(curso_id, 'primera'),
                    'segunda': servicio_notas.obtener_estadisticas_curso(curso_id, 'segunda'),
                    'tercera': servicio_notas.obtener_estadisticas_curso(curso_id, 'tercera'),
                    'general': servicio_notas.obtener_estadisticas_curso(curso_id)
                }
            
            # Verificar si las fechas están habilitadas para subir notas
            fechas_habilitadas = self._verificar_fechas_habilitadas()
            
            context.update({
                'cursos': cursos,
                'curso_seleccionado': curso_seleccionado,
                'estadisticas': estadisticas,
                'fechas_habilitadas': fechas_habilitadas,
                'fases_disponibles': ['primera', 'segunda', 'tercera']
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'estadisticas': {},
                'fechas_habilitadas': False
            })
        except Exception as e:
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'cursos': [],
                'curso_seleccionado': None,
                'estadisticas': {},
                'fechas_habilitadas': False
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Procesar subida de notas via Excel"""
        try:
            teacher = request.user.teacher
            teacher_id = str(teacher.id)
            
            # Verificar que las fechas estén habilitadas
            if not self._verificar_fechas_habilitadas():
                messages.error(request, 'Las fechas para subir notas no están habilitadas.')
                return redirect('profesor:notas')
            
            # Obtener datos del formulario
            curso_id = request.POST.get('curso_id')
            fase = request.POST.get('fase')
            archivo_excel = request.FILES.get('archivo_notas')
            
            if not all([curso_id, fase, archivo_excel]):
                messages.error(request, 'Todos los campos son obligatorios.')
                return redirect('profesor:notas')
            
            # Procesar archivo Excel
            excel_data = self._procesar_excel_notas(archivo_excel)
            
            if not excel_data['success']:
                messages.error(request, f'Error procesando Excel: {excel_data["error"]}')
                return redirect('profesor:notas')
            
            # Registrar notas en el sistema
            resultado = servicio_notas.registrar_notas_excel(
                teacher_id=teacher_id,
                course_id=curso_id,
                excel_data=excel_data['data'],
                fase=fase
            )
            
            if resultado['success']:
                messages.success(
                    request, 
                    f'Notas de {fase} fase registradas exitosamente. '
                    f'Registros exitosos: {resultado["registros_exitosos"]}'
                )
                
                if resultado['total_errores'] > 0:
                    messages.warning(
                        request,
                        f'Se encontraron {resultado["total_errores"]} errores. '
                        'Revisa los datos y vuelve a intentar.'
                    )
            else:
                messages.error(request, f'Error registrando notas: {resultado["error"]}')
            
        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
        except Exception as e:
            messages.error(request, f'Error procesando solicitud: {str(e)}')
        
        return redirect('profesor:notas')

    def _verificar_fechas_habilitadas(self):
        """Verificar si las fechas están habilitadas para subir notas"""
        # TODO: Implementar verificación real con modelo de configuración
        # Por ahora retorna True para permitir pruebas
        return True

    def _procesar_excel_notas(self, archivo_excel):
        """Procesar archivo Excel de notas"""
        try:
            import pandas as pd
            
            # Leer Excel
            df = pd.read_excel(archivo_excel)
            
            # Verificar columnas requeridas
            columnas_requeridas = ['codigo_estudiante', 'nota_parcial', 'nota_continua']
            
            if not all(col in df.columns for col in columnas_requeridas):
                return {
                    'success': False,
                    'error': f'El Excel debe contener las columnas: {", ".join(columnas_requeridas)}'
                }
            
            # Convertir a lista de diccionarios
            data = []
            for _, row in df.iterrows():
                data.append({
                    'codigo_estudiante': str(row['codigo_estudiante']).strip(),
                    'nota_parcial': row['nota_parcial'] if pd.notna(row['nota_parcial']) else None,
                    'nota_continua': row['nota_continua'] if pd.notna(row['nota_continua']) else None
                })
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error leyendo archivo Excel: {str(e)}'
            }


class ProfesorEstadisticasNotasView(ProfesorRequiredMixin, TemplateView):
    """Vista para estadísticas y gráficos de notas"""
    template_name = 'profesor/notas/estadisticas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = self.request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener cursos del profesor
            cursos = servicio_notas.obtener_cursos_profesor(teacher_id)
            
            # Obtener curso seleccionado
            curso_id = self.request.GET.get('curso_id')
            if curso_id and cursos:
                curso_seleccionado = next((c for c in cursos if c['course_id'] == curso_id), None)
                
                if curso_seleccionado:
                    # Obtener estadísticas detalladas
                    estadisticas = {
                        'primera': servicio_notas.obtener_estadisticas_curso(curso_id, 'primera'),
                        'segunda': servicio_notas.obtener_estadisticas_curso(curso_id, 'segunda'),
                        'tercera': servicio_notas.obtener_estadisticas_curso(curso_id, 'tercera'),
                        'general': servicio_notas.obtener_estadisticas_curso(curso_id)
                    }
                    
                    context.update({
                        'curso_seleccionado': curso_seleccionado,
                        'estadisticas': estadisticas,
                        'tiene_datos': any(est.get('success', False) for est in estadisticas.values())
                    })
            
            context.update({
                'cursos': cursos
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({'cursos': [], 'estadisticas': {}})
        except Exception as e:
            messages.error(self.request, f'Error cargando estadísticas: {str(e)}')
            context.update({'cursos': [], 'estadisticas': {}})
        
        return context


class ProfesorGraficosNotasAPIView(ProfesorRequiredMixin, TemplateView):
    """API para datos de gráficos de notas"""
    
    def get(self, request, *args, **kwargs):
        """Retornar datos para gráficos en formato JSON"""
        try:
            teacher = request.user.teacher
            curso_id = request.GET.get('curso_id')
            fase = request.GET.get('fase', 'general')
            
            if not curso_id:
                return JsonResponse({'error': 'curso_id requerido'}, status=400)
            
            # Obtener estadísticas
            estadisticas = servicio_notas.obtener_estadisticas_curso(curso_id, fase if fase != 'general' else None)
            
            if not estadisticas.get('success'):
                return JsonResponse({'error': 'No se pudieron obtener estadísticas'}, status=404)
            
            # Preparar datos para gráficos
            stats = estadisticas['estadisticas']
            distribucion = estadisticas['distribucion']
            notas_detalle = estadisticas['notas_detalle']
            
            # Datos para gráfico de barras (distribución)
            grafico_distribucion = {
                'labels': list(distribucion.keys()),
                'data': list(distribucion.values()),
                'backgroundColor': ['#ff6384', '#ff9f40', '#ffcd56', '#4bc0c0']
            }
            
            # Datos para gráfico de líneas (evolución por estudiante)
            estudiantes_nombres = [nota['student_name'] for nota in notas_detalle[:10]]  # Primeros 10
            estudiantes_notas = [nota['grade'] for nota in notas_detalle[:10]]
            
            grafico_estudiantes = {
                'labels': estudiantes_nombres,
                'data': estudiantes_notas,
                'borderColor': '#36a2eb',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)'
            }
            
            # Estadísticas resumidas
            estadisticas_resumen = {
                'promedio': stats['promedio'],
                'nota_maxima': stats['nota_maxima'],
                'nota_minima': stats['nota_minima'],
                'total_notas': stats['total_notas']
            }
            
            return JsonResponse({
                'success': True,
                'grafico_distribucion': grafico_distribucion,
                'grafico_estudiantes': grafico_estudiantes,
                'estadisticas': estadisticas_resumen,
                'fase': fase
            })
            
        except AttributeError:
            return JsonResponse({'error': 'No se encontró perfil de profesor'}, status=403)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ProfesorDescargarPlantillaView(ProfesorRequiredMixin, TemplateView):
    """Vista para descargar plantilla Excel de notas"""
    
    def get(self, request, *args, **kwargs):
        """Generar y descargar plantilla Excel"""
        try:
            teacher = request.user.teacher
            teacher_id = str(teacher.id)
            curso_id = request.GET.get('curso_id')
            
            if not curso_id:
                messages.error(request, 'Debe seleccionar un curso.')
                return redirect('profesor:notas')
            
            # Obtener estudiantes del curso
            # TODO: Implementar método para obtener estudiantes matriculados
            estudiantes_ejemplo = [
                {'codigo': '20190001', 'nombre': 'Juan Pérez'},
                {'codigo': '20190002', 'nombre': 'María García'},
                {'codigo': '20190003', 'nombre': 'Carlos López'},
            ]
            
            # Crear archivo Excel
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Notas')
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            cell_format = workbook.add_format({'border': 1})
            
            # Encabezados
            headers = ['codigo_estudiante', 'nombre_estudiante', 'nota_parcial', 'nota_continua']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Datos de estudiantes
            for row, estudiante in enumerate(estudiantes_ejemplo, 1):
                worksheet.write(row, 0, estudiante['codigo'], cell_format)
                worksheet.write(row, 1, estudiante['nombre'], cell_format)
                worksheet.write(row, 2, '', cell_format)  # nota_parcial vacía
                worksheet.write(row, 3, '', cell_format)  # nota_continua vacía
            
            # Ajustar ancho de columnas
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:D', 12)
            
            workbook.close()
            output.seek(0)
            
            # Preparar respuesta
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="plantilla_notas_{curso_id}.xlsx"'
            
            return response
            
        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
            return redirect('profesor:notas')
        except Exception as e:
            messages.error(request, f'Error generando plantilla: {str(e)}')
            return redirect('profesor:notas')