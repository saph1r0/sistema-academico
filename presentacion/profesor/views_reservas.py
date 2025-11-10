#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vistas para gestión de reservas de ambientes del profesor
Reserva automática de 9 ambientes (3 pisos)
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, time, datetime

from .mixins import ProfesorRequiredMixin
from servicios.servicioReservas import servicio_reservas
from servicios.servicioNotas import servicio_notas


class ProfesorReservasView(ProfesorRequiredMixin, TemplateView):
    """Vista principal para gestión de reservas"""
    template_name = 'profesor/reservas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = self.request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener cursos del profesor
            cursos = servicio_notas.obtener_cursos_profesor(teacher_id)
            
            # Obtener reservas del profesor (próximos 30 días)
            reservas_data = servicio_reservas.obtener_reservas_profesor(teacher_id)
            
            # Obtener ambientes disponibles para hoy
            fecha_hoy = timezone.now().date()
            hora_inicio = time(8, 0)  # 8:00 AM
            hora_fin = time(10, 0)    # 10:00 AM
            
            ambientes_disponibles = servicio_reservas.obtener_ambientes_disponibles(
                fecha_hoy, hora_inicio, hora_fin
            )
            
            context.update({
                'cursos': cursos,
                'reservas_data': reservas_data,
                'ambientes_disponibles': ambientes_disponibles,
                'fecha_hoy': fecha_hoy,
                'horarios_sugeridos': [
                    {'inicio': '07:00', 'fin': '08:40', 'label': '1ra Hora (07:00 - 08:40)'},
                    {'inicio': '08:50', 'fin': '10:30', 'label': '2da Hora (08:50 - 10:30)'},
                    {'inicio': '10:40', 'fin': '12:20', 'label': '3ra Hora (10:40 - 12:20)'},
                    {'inicio': '14:00', 'fin': '15:40', 'label': '4ta Hora (14:00 - 15:40)'},
                    {'inicio': '15:50', 'fin': '17:30', 'label': '5ta Hora (15:50 - 17:30)'},
                    {'inicio': '17:40', 'fin': '19:20', 'label': '6ta Hora (17:40 - 19:20)'}
                ],
                'tipos_ambiente': [
                    {'value': 'classroom', 'label': 'Aula (Clases teóricas)'},
                    {'value': 'laboratory', 'label': 'Laboratorio (Clases prácticas)'}
                ]
            })
            
        except AttributeError:
            messages.error(self.request, 'No se encontró perfil de profesor.')
            context.update({
                'cursos': [],
                'reservas_data': {},
                'ambientes_disponibles': {}
            })
        except Exception as e:
            messages.error(self.request, f'Error cargando datos: {str(e)}')
            context.update({
                'cursos': [],
                'reservas_data': {},
                'ambientes_disponibles': {}
            })
        
        return context

    def post(self, request, *args, **kwargs):
        """Procesar solicitud de reserva"""
        try:
            teacher = request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener datos del formulario
            accion = request.POST.get('accion')
            
            if accion == 'reservar_automatico':
                # Reserva automática
                curso_id = request.POST.get('curso_id')
                fecha_str = request.POST.get('fecha')
                hora_inicio_str = request.POST.get('hora_inicio')
                hora_fin_str = request.POST.get('hora_fin')
                proposito = request.POST.get('proposito', '')
                tipo_preferido = request.POST.get('tipo_ambiente')
                
                if not all([curso_id, fecha_str, hora_inicio_str, hora_fin_str]):
                    messages.error(request, 'Todos los campos son obligatorios.')
                    return redirect('profesor:reservas')
                
                try:
                    fecha = date.fromisoformat(fecha_str)
                    hora_inicio = time.fromisoformat(hora_inicio_str)
                    hora_fin = time.fromisoformat(hora_fin_str)
                except ValueError:
                    messages.error(request, 'Fecha u hora inválida.')
                    return redirect('profesor:reservas')
                
                # Realizar reserva automática
                resultado = servicio_reservas.reservar_ambiente_automatico(
                    teacher_id=teacher_id,
                    course_id=curso_id,
                    fecha=fecha,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    proposito=proposito,
                    tipo_preferido=tipo_preferido
                )
                
                if resultado['success']:
                    ambiente = resultado['ambiente_asignado']
                    messages.success(
                        request,
                        f'Reserva exitosa! Se asignó el ambiente {ambiente["code"]} - {ambiente["name"]} '
                        f'para el {fecha.strftime("%d/%m/%Y")} de {hora_inicio.strftime("%H:%M")} '
                        f'a {hora_fin.strftime("%H:%M")}.'
                    )
                else:
                    messages.error(request, f'Error en la reserva: {resultado["error"]}')
            
            elif accion == 'cancelar_reserva':
                # Cancelar reserva existente
                reservation_id = request.POST.get('reservation_id')
                
                if not reservation_id:
                    messages.error(request, 'ID de reserva requerido.')
                    return redirect('profesor:reservas')
                
                resultado = servicio_reservas.cancelar_reserva(reservation_id, teacher_id)
                
                if resultado['success']:
                    messages.success(request, resultado['message'])
                else:
                    messages.error(request, f'Error cancelando reserva: {resultado["error"]}')
            
        except AttributeError:
            messages.error(request, 'No se encontró perfil de profesor.')
        except Exception as e:
            messages.error(request, f'Error procesando reserva: {str(e)}')
        
        return redirect('profesor:reservas')


class ProfesorConsultarDisponibilidadView(ProfesorRequiredMixin, TemplateView):
    """Vista para consultar disponibilidad de ambientes"""
    template_name = 'profesor/reservas/disponibilidad.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de consulta
        fecha_str = self.request.GET.get('fecha', timezone.now().date().isoformat())
        hora_inicio_str = self.request.GET.get('hora_inicio', '08:00')
        hora_fin_str = self.request.GET.get('hora_fin', '10:00')
        tipo_ambiente = self.request.GET.get('tipo_ambiente', '')
        
        try:
            fecha = date.fromisoformat(fecha_str)
            hora_inicio = time.fromisoformat(hora_inicio_str)
            hora_fin = time.fromisoformat(hora_fin_str)
        except ValueError:
            fecha = timezone.now().date()
            hora_inicio = time(8, 0)
            hora_fin = time(10, 0)
        
        # Obtener disponibilidad
        disponibilidad = servicio_reservas.obtener_ambientes_disponibles(
            fecha, hora_inicio, hora_fin, tipo_ambiente if tipo_ambiente else None
        )
        
        context.update({
            'disponibilidad': disponibilidad,
            'fecha_consulta': fecha,
            'hora_inicio_consulta': hora_inicio,
            'hora_fin_consulta': hora_fin,
            'tipo_ambiente_consulta': tipo_ambiente,
            'tipos_ambiente': [
                {'value': '', 'label': 'Todos los tipos'},
                {'value': 'classroom', 'label': 'Solo Aulas'},
                {'value': 'laboratory', 'label': 'Solo Laboratorios'}
            ]
        })
        
        return context


class ProfesorAmbientesDisponiblesAPIView(ProfesorRequiredMixin, TemplateView):
    """API para consultar ambientes disponibles en tiempo real"""
    
    def get(self, request, *args, **kwargs):
        """Retornar ambientes disponibles en formato JSON"""
        try:
            # Obtener parámetros
            fecha_str = request.GET.get('fecha')
            hora_inicio_str = request.GET.get('hora_inicio')
            hora_fin_str = request.GET.get('hora_fin')
            tipo_ambiente = request.GET.get('tipo_ambiente')
            
            if not all([fecha_str, hora_inicio_str, hora_fin_str]):
                return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
            
            try:
                fecha = date.fromisoformat(fecha_str)
                hora_inicio = time.fromisoformat(hora_inicio_str)
                hora_fin = time.fromisoformat(hora_fin_str)
            except ValueError:
                return JsonResponse({'error': 'Fecha u hora inválida'}, status=400)
            
            # Obtener disponibilidad
            disponibilidad = servicio_reservas.obtener_ambientes_disponibles(
                fecha, hora_inicio, hora_fin, tipo_ambiente if tipo_ambiente else None
            )
            
            if disponibilidad['success']:
                return JsonResponse({
                    'success': True,
                    'ambientes_por_piso': disponibilidad['ambientes_por_piso'],
                    'estadisticas': disponibilidad['estadisticas'],
                    'fecha': fecha_str,
                    'horario': {
                        'inicio': hora_inicio_str,
                        'fin': hora_fin_str
                    }
                })
            else:
                return JsonResponse({'error': 'Error consultando disponibilidad'}, status=500)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ProfesorReservaRapidaAPIView(ProfesorRequiredMixin, TemplateView):
    """API para reserva rápida de ambientes"""
    
    def post(self, request, *args, **kwargs):
        """Realizar reserva rápida via AJAX"""
        try:
            teacher = request.user.teacher
            teacher_id = str(teacher.id)
            
            # Obtener datos JSON
            import json
            data = json.loads(request.body)
            
            curso_id = data.get('curso_id')
            fecha_str = data.get('fecha')
            hora_inicio_str = data.get('hora_inicio')
            hora_fin_str = data.get('hora_fin')
            proposito = data.get('proposito', 'Clase regular')
            tipo_preferido = data.get('tipo_preferido')
            
            if not all([curso_id, fecha_str, hora_inicio_str, hora_fin_str]):
                return JsonResponse({'error': 'Datos incompletos'}, status=400)
            
            try:
                fecha = date.fromisoformat(fecha_str)
                hora_inicio = time.fromisoformat(hora_inicio_str)
                hora_fin = time.fromisoformat(hora_fin_str)
            except ValueError:
                return JsonResponse({'error': 'Fecha u hora inválida'}, status=400)
            
            # Realizar reserva automática
            resultado = servicio_reservas.reservar_ambiente_automatico(
                teacher_id=teacher_id,
                course_id=curso_id,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                proposito=proposito,
                tipo_preferido=tipo_preferido
            )
            
            if resultado['success']:
                return JsonResponse({
                    'success': True,
                    'message': resultado['message'],
                    'ambiente_asignado': resultado['ambiente_asignado'],
                    'detalles_reserva': resultado['detalles_reserva']
                })
            else:
                return JsonResponse({'error': resultado['error']}, status=400)
            
        except AttributeError:
            return JsonResponse({'error': 'No se encontró perfil de profesor'}, status=403)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)