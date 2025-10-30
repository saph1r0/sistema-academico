"""
Vistas para el módulo de profesores
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse

from .mixins import ProfesorRequiredMixin
from servicios.servicioUsuario import ServicioUsuario
from servicios.servicioNotas import ServicioNotas
from servicios.servicioAsistencia import ServicioAsistencia
from servicios.servicioReservas import ServicioReservas


class ProfesorDashboardView(ProfesorRequiredMixin, TemplateView):
    """Dashboard principal del profesor"""
    template_name = 'profesor/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el profesor asociado al usuario
        try:
            profesor = self.request.user.teacher
            profesor_id = profesor.id
        except AttributeError:
            profesor_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora
        context.update({
            'cursos_asignados': [],  # ServicioUsuario.obtener_cursos_profesor(profesor_id),
            'horarios': [],  # ServicioUsuario.obtener_horario_profesor(profesor_id),
            'asistencia_propia': {'porcentaje': 0.0},  # ServicioAsistencia.obtener_asistencia_profesor(profesor_id),
            'estadisticas_cursos': {},  # ServicioUsuario.obtener_estadisticas_profesor(profesor_id)
            'total_estudiantes': 0,
            'total_horas_semanales': 0,
            'horario_hoy': [],
            'proximas_evaluaciones': []
        })
        return context


class ProfesorNotasView(ProfesorRequiredMixin, TemplateView):
    """Gestión de notas mediante plantillas Excel"""
    template_name = 'profesor/notas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el profesor asociado al usuario
        try:
            profesor = self.request.user.teacher
            profesor_id = profesor.id
        except AttributeError:
            profesor_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora
        context.update({
            'cursos_asignados': [],  # ServicioUsuario.obtener_cursos_profesor(profesor_id),
            'estudiantes_por_curso': []  # ServicioNotas.obtener_estudiantes_profesor(profesor_id)
        })
        return context

    def post(self, request, *args, **kwargs):
        """Procesar descarga de plantilla o subida de notas"""
        # Obtener el profesor asociado al usuario
        try:
            profesor = request.user.teacher
            profesor_id = profesor.id
        except AttributeError:
            profesor_id = request.user.id
            
        if 'descargar_plantilla' in request.POST:
            curso_id = request.POST.get('curso_id')
            try:
                # response = ServicioNotas.generar_plantilla_excel(curso_id, profesor_id)
                messages.success(request, 'Plantilla generada exitosamente.')
                # return response
            except Exception as e:
                messages.error(request, f'Error al generar plantilla: {str(e)}')
        
        elif 'subir_notas' in request.POST:
            archivo = request.FILES.get('archivo_notas')
            curso_id = request.POST.get('curso_id')
            try:
                # resultado = ServicioNotas.procesar_archivo_notas(archivo, curso_id, profesor_id)
                messages.success(request, 'Notas procesadas exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al procesar archivo: {str(e)}')
        
        return redirect('profesor:notas')


class ProfesorAsistenciaView(ProfesorRequiredMixin, TemplateView):
    """Registro y gestión de asistencia estudiantil"""
    template_name = 'profesor/asistencia/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el profesor asociado al usuario
        try:
            profesor = self.request.user.teacher
            profesor_id = profesor.id
        except AttributeError:
            profesor_id = self.request.user.id
            
        fecha = self.request.GET.get('fecha', timezone.now().date())
        
        # Usar datos de ejemplo por ahora
        context.update({
            'cursos_asignados': [],  # ServicioUsuario.obtener_cursos_profesor(profesor_id),
            'estudiantes_del_dia': [],  # ServicioAsistencia.obtener_estudiantes_fecha(profesor_id, fecha),
            'fecha_actual': fecha,
            'reportes_asistencia': []  # ServicioAsistencia.obtener_reportes_profesor(profesor_id)
        })
        return context

    def post(self, request, *args, **kwargs):
        """Registrar asistencia masiva"""
        try:
            # Obtener el profesor asociado al usuario
            try:
                profesor = request.user.teacher
                profesor_id = profesor.id
            except AttributeError:
                profesor_id = request.user.id
                
            asistencias = request.POST.getlist('asistencia')
            fecha = request.POST.get('fecha')
            curso_id = request.POST.get('curso_id')
            
            # resultado = ServicioAsistencia.registrar_asistencia_masiva(asistencias, fecha, curso_id, profesor_id)
            messages.success(request, 'Asistencia registrada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al registrar asistencia: {str(e)}')
        
        return redirect('profesor:asistencia')


class ProfesorReservasView(ProfesorRequiredMixin, TemplateView):
    """Gestión de reservas de ambientes"""
    template_name = 'profesor/reservas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener el profesor asociado al usuario
        try:
            profesor = self.request.user.teacher
            profesor_id = profesor.id
        except AttributeError:
            profesor_id = self.request.user.id
        
        # Usar datos de ejemplo por ahora
        context.update({
            'recursos_disponibles': [],  # ServicioReservas.obtener_recursos_disponibles(),
            'reservas_profesor': [],  # ServicioReservas.obtener_reservas_profesor(profesor_id),
            'conflictos_horarios': []  # ServicioReservas.detectar_conflictos_profesor(profesor_id)
        })
        return context

    def post(self, request, *args, **kwargs):
        """Crear nueva reserva"""
        try:
            # Obtener el profesor asociado al usuario
            try:
                profesor = request.user.teacher
                profesor_id = profesor.id
            except AttributeError:
                profesor_id = request.user.id
                
            recurso_id = request.POST.get('recurso_id')
            fecha = request.POST.get('fecha')
            hora_inicio = request.POST.get('hora_inicio')
            hora_fin = request.POST.get('hora_fin')
            proposito = request.POST.get('proposito')
            
            # resultado = ServicioReservas.crear_reserva(recurso_id, profesor_id, fecha, hora_inicio, hora_fin, proposito)
            messages.success(request, 'Reserva creada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al crear reserva: {str(e)}')
        
        return redirect('profesor:reservas')


class ProfesorSilaboView(ProfesorRequiredMixin, TemplateView):
    """Gestión de sílabos y avance de cursos"""
    template_name = 'profesor/silabo/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profesor = self.request.user.profesor
        
        context.update({
            'cursos_asignados': ServicioUsuario.obtener_cursos_profesor(profesor.id),
            'silabos_profesor': ServicioSilabo.obtener_silabos_profesor(profesor.id),
            'avance_cursos': ServicioAvance.obtener_avance_profesor(profesor.id)
        })
        return context

    def post(self, request, *args, **kwargs):
        """Subir sílabo o registrar avance"""
        if 'subir_silabo' in request.POST:
            try:
                curso_id = request.POST.get('curso_id')
                archivo_silabo = request.FILES.get('archivo_silabo')
                unidades = request.POST.getlist('unidades')
                
                resultado = ServicioSilabo.procesar_silabo(
                    curso_id, archivo_silabo, unidades, request.user.profesor.id
                )
                messages.success(request, 'Sílabo subido exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al subir sílabo: {str(e)}')
        
        elif 'registrar_avance' in request.POST:
            try:
                tema_id = request.POST.get('tema_id')
                porcentaje = request.POST.get('porcentaje')
                notas = request.POST.get('notas')
                
                ServicioAvance.registrar_avance_tema(
                    tema_id, porcentaje, notas, request.user.profesor.id
                )
                messages.success(request, 'Avance registrado exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al registrar avance: {str(e)}')
        
        return redirect('profesor:silabo')