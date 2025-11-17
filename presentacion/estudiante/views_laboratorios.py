#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vistas para gestión de laboratorios del estudiante
VERSIÓN CON DEBUG para encontrar problemas
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
import logging

from servicios.servicioMatriculaLaboratorio import servicio_matricula_laboratorio
from servicios.servicioHorario import servicio_horario
from presentacion.estudiante.mixins import EstudianteRequiredMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class EstudianteLaboratoriosView(EstudianteRequiredMixin, TemplateView):
    """Vista principal de laboratorios del estudiante"""
    template_name = 'estudiante/laboratorios/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            student = self.request.user.student
            student_id = student.id
            
            logger.info(f"[DEBUG] Obteniendo laboratorios para estudiante ID: {student_id}")
            logger.info(f"[DEBUG] Estudiante: {student.user.get_full_name()} - {student.student_code}")
            
            # Obtener laboratorios disponibles con todas las validaciones
            data = servicio_matricula_laboratorio.obtener_laboratorios_disponibles(student_id)
            
            logger.info(f"[DEBUG] Respuesta del servicio - Success: {data.get('success')}")
            logger.info(f"[DEBUG] Total laboratorios: {data.get('total_disponibles', 0)}")
            logger.info(f"[DEBUG] En período matrícula: {data.get('en_periodo_matricula')}")
            
            if not data['success']:
                error_msg = data.get('error', 'Error al cargar laboratorios')
                logger.error(f"[DEBUG] Error en servicio: {error_msg}")
                messages.error(self.request, error_msg)
                context.update({
                    'laboratorios_disponibles': [],
                    'matriculas_actuales': [],
                    'en_periodo_matricula': False,
                    'total_disponibles': 0,
                    'total_matriculados': 0
                })
                return context
            
            # DEBUG: Imprimir todos los laboratorios
            logger.info(f"[DEBUG] Laboratorios encontrados: {len(data.get('laboratorios', []))}")
            for i, lab in enumerate(data.get('laboratorios', [])):
                logger.info(f"[DEBUG] Lab {i+1}: {lab.get('codigo')} - {lab.get('curso_nombre')}")
                logger.info(f"  - Ya matriculado: {lab.get('ya_matriculado')}")
                logger.info(f"  - Tiene cupos: {lab.get('tiene_cupos')}")
                logger.info(f"  - Conflicto: {lab.get('tiene_conflicto')}")
            
            # Separar laboratorios: matriculados vs disponibles
            laboratorios_disponibles = []
            matriculas_actuales = []
            
            for lab in data['laboratorios']:
                if lab['ya_matriculado']:
                    matriculas_actuales.append(lab)
                    logger.info(f"[DEBUG] Agregado a matriculas_actuales: {lab['codigo']}")
                else:
                    laboratorios_disponibles.append(lab)
                    logger.info(f"[DEBUG] Agregado a disponibles: {lab['codigo']}")
            
            logger.info(f"[DEBUG] Total disponibles: {len(laboratorios_disponibles)}")
            logger.info(f"[DEBUG] Total matriculados: {len(matriculas_actuales)}")
            
            # Obtener resumen del horario actual
            try:
                horario_data = servicio_horario.obtener_resumen_horario(student_id)
                logger.info(f"[DEBUG] Resumen horario obtenido: {horario_data.get('success')}")
            except Exception as e:
                logger.error(f"[DEBUG] Error obteniendo resumen horario: {e}")
                horario_data = {'success': False}
            
            context.update({
                'student': student,
                'laboratorios_disponibles': laboratorios_disponibles,
                'matriculas_actuales': matriculas_actuales,
                'en_periodo_matricula': data['en_periodo_matricula'],
                'total_disponibles': len(laboratorios_disponibles),
                'total_matriculados': len(matriculas_actuales),
                'resumen_horario': horario_data if horario_data.get('success') else None,
                'debug_mode': True  # Para mostrar info en el template
            })
            
            logger.info(f"[DEBUG] Context final - Disponibles: {len(laboratorios_disponibles)}, Matriculados: {len(matriculas_actuales)}")
            
        except Exception as e:
            logger.exception(f"[DEBUG] ERROR CRÍTICO en get_context_data: {e}")
            messages.error(self.request, f'Error al cargar la página: {str(e)}')
            context.update({
                'laboratorios_disponibles': [],
                'matriculas_actuales': [],
                'en_periodo_matricula': False,
                'total_disponibles': 0,
                'total_matriculados': 0
            })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Maneja matrícula y desmatrícula de laboratorios"""
        try:
            student = request.user.student
            accion = request.POST.get('accion')
            laboratorio_id = request.POST.get('laboratorio_id')
            
            logger.info(f"[DEBUG POST] Acción: {accion}, Lab ID: {laboratorio_id}")
            
            if not laboratorio_id:
                messages.error(request, 'ID de laboratorio no proporcionado')
                return redirect('estudiante:laboratorios')
            
            if accion == 'matricular':
                logger.info(f"[DEBUG POST] Intentando matricular en lab: {laboratorio_id}")
                exito, mensaje = servicio_matricula_laboratorio.matricular_laboratorio(
                    student.id, 
                    laboratorio_id
                )
                logger.info(f"[DEBUG POST] Resultado matrícula - Éxito: {exito}, Mensaje: {mensaje}")
                
                if exito:
                    messages.success(request, mensaje)
                else:
                    messages.error(request, mensaje)
            
            elif accion == 'desmatricular':
                logger.info(f"[DEBUG POST] Intentando desmatricular de lab: {laboratorio_id}")
                exito, mensaje = servicio_matricula_laboratorio.desmatricular_laboratorio(
                    student.id,
                    laboratorio_id
                )
                logger.info(f"[DEBUG POST] Resultado desmatrícula - Éxito: {exito}, Mensaje: {mensaje}")
                
                if exito:
                    messages.success(request, mensaje)
                else:
                    messages.error(request, mensaje)
            
            else:
                logger.warning(f"[DEBUG POST] Acción no válida: {accion}")
                messages.error(request, 'Acción no válida')
        
        except Exception as e:
            logger.exception(f"[DEBUG POST] ERROR en POST: {e}")
            messages.error(request, f'Error: {str(e)}')
        
        return redirect('estudiante:laboratorios')


class LaboratoriosDisponiblesAPIView(View):
    """API para obtener laboratorios disponibles en formato JSON"""
    
    def get(self, request, *args, **kwargs):
        try:
            student = request.user.student
            logger.info(f"[DEBUG API] Obteniendo labs para estudiante: {student.id}")
            
            data = servicio_matricula_laboratorio.obtener_laboratorios_disponibles(student.id)
            
            logger.info(f"[DEBUG API] Respuesta: Success={data.get('success')}, Total={data.get('total_disponibles')}")
            
            return JsonResponse(data)
        except Exception as e:
            logger.exception(f"[DEBUG API] Error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class VerificarConflictoAPIView(View):
    """API para verificar conflictos antes de matricular"""
    
    def post(self, request, *args, **kwargs):
        try:
            student = request.user.student
            laboratory_id = request.POST.get('laboratory_id')
            
            logger.info(f"[DEBUG CONFLICT] Verificando conflicto para lab: {laboratory_id}")
            
            if not laboratory_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID de laboratorio requerido'
                })
            
            # Verificar conflictos usando el servicio de horarios
            from repositorio.postgres_repository.models import Laboratory, Horario
            
            laboratory = Laboratory.objects.get(id=laboratory_id)
            horario_lab = Horario.objects.filter(laboratory=laboratory).first()
            
            if not horario_lab:
                logger.info(f"[DEBUG CONFLICT] Lab sin horario asignado")
                return JsonResponse({
                    'success': True,
                    'tiene_conflicto': False,
                    'mensaje': 'Sin horario asignado'
                })
            
            # Usar el servicio para verificar conflictos
            servicio = servicio_matricula_laboratorio
            tiene_conflicto, mensaje = servicio._verificar_conflicto_horario(
                student, 
                horario_lab
            )
            
            logger.info(f"[DEBUG CONFLICT] Conflicto: {tiene_conflicto}, Mensaje: {mensaje}")
            
            return JsonResponse({
                'success': True,
                'tiene_conflicto': tiene_conflicto,
                'mensaje': mensaje or 'Sin conflictos'
            })
            
        except Exception as e:
            logger.exception(f"[DEBUG CONFLICT] Error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@login_required
def laboratorio_detalle(request, laboratorio_id):
    """Vista de detalle de un laboratorio específico"""
    from repositorio.postgres_repository.models import Laboratory, Horario, LaboratoryEnrollment
    
    try:
        logger.info(f"[DEBUG DETALLE] Mostrando detalle de lab: {laboratorio_id}")
        
        student = request.user.student
        laboratory = Laboratory.objects.select_related(
            'course_group__course',
            'teacher__user'
        ).get(id=laboratorio_id)
        
        # Obtener horarios
        horarios = Horario.objects.filter(
            laboratory=laboratory
        ).select_related('aula')
        
        logger.info(f"[DEBUG DETALLE] Horarios encontrados: {horarios.count()}")
        
        # Obtener estudiantes matriculados
        matriculados = LaboratoryEnrollment.objects.filter(
            laboratory=laboratory,
            status='active'
        ).select_related('student__user').order_by('enrollment_date')
        
        logger.info(f"[DEBUG DETALLE] Estudiantes matriculados: {matriculados.count()}")
        
        # Verificar si el estudiante actual está matriculado
        mi_matricula = matriculados.filter(student=student).first()
        
        # Calcular cupos
        servicio = servicio_matricula_laboratorio
        cupos = servicio._calcular_cupos(laboratory)
        
        # Verificar conflictos
        horario_principal = horarios.first() if horarios else None
        tiene_conflicto, mensaje_conflicto = servicio._verificar_conflicto_horario(
            student, 
            horario_principal
        )
        
        logger.info(f"[DEBUG DETALLE] Conflicto: {tiene_conflicto}")
        
        context = {
            'laboratory': laboratory,
            'horarios': horarios,
            'matriculados': matriculados,
            'mi_matricula': mi_matricula,
            'cupos': cupos,
            'tiene_conflicto': tiene_conflicto,
            'mensaje_conflicto': mensaje_conflicto,
            'puede_matricularse': (
                not mi_matricula and 
                cupos['tiene_cupos'] and 
                not tiene_conflicto and
                servicio._verificar_periodo_matricula()
            ),
            'puede_desmatricularse': (
                mi_matricula and 
                servicio._puede_desmatricularse(mi_matricula)
            ) if mi_matricula else False
        }
        
        return render(request, 'estudiante/laboratorios/detalle.html', context)
        
    except Laboratory.DoesNotExist:
        logger.error(f"[DEBUG DETALLE] Laboratorio no encontrado: {laboratorio_id}")
        messages.error(request, 'Laboratorio no encontrado')
        return redirect('estudiante:laboratorios')
    except Exception as e:
        logger.exception(f"[DEBUG DETALLE] Error: {e}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('estudiante:laboratorios')