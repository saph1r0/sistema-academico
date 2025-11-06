"""
Formularios para el módulo de profesores
"""
from django import forms
from django.core.validators import FileExtensionValidator


class SubirNotasForm(forms.Form):
    """Formulario para subir archivo de notas"""
    curso_id = forms.UUIDField(widget=forms.HiddenInput())
    archivo_notas = forms.FileField(
        label='Archivo de Notas',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text='Solo archivos Excel (.xlsx, .xls)'
    )

    def clean_archivo_notas(self):
        archivo = self.cleaned_data.get('archivo_notas')
        if archivo:
            if archivo.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo no puede ser mayor a 5MB.')
        return archivo


class SubirNotasFaseForm(forms.Form):
    """Formulario para subir archivo de notas por fases académicas"""
    PHASE_CHOICES = [
        ('primera', 'Primera Fase'),
        ('segunda', 'Segunda Fase'),
        ('tercera', 'Tercera Fase'),
    ]
    
    course_group_id = forms.UUIDField(widget=forms.HiddenInput())
    phase = forms.ChoiceField(
        choices=PHASE_CHOICES,
        label='Fase Académica',
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    archivo_excel = forms.FileField(
        label='Archivo Excel de Notas',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text='Plantilla "Excel notas P1" con columnas: código estudiante, nota parcial, nota continua',
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': '.xlsx,.xls'
        })
    )
    allow_duplicates = forms.BooleanField(
        required=False,
        initial=False,
        label='Permitir actualizar notas existentes',
        help_text='Marcar si desea actualizar notas ya registradas para esta fase',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )

    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get('archivo_excel')
        if archivo:
            # Validar tamaño (máximo 10MB para archivos Excel)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensión
            if not archivo.name.lower().endswith(('.xlsx', '.xls')):
                raise forms.ValidationError('Solo se permiten archivos Excel (.xlsx, .xls).')
        
        return archivo

    def clean_phase(self):
        phase = self.cleaned_data.get('phase')
        if phase not in ['primera', 'segunda', 'tercera']:
            raise forms.ValidationError('Fase académica inválida.')
        return phase


class RegistrarAsistenciaForm(forms.Form):
    """Formulario para registrar asistencia"""
    curso_id = forms.UUIDField(widget=forms.HiddenInput())
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha'
    )
    
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        from django.utils import timezone
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError('No se puede registrar asistencia para fechas futuras.')
        return fecha


class CrearReservaForm(forms.Form):
    """Formulario para crear reservas"""
    recurso_id = forms.UUIDField(widget=forms.HiddenInput())
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de Reserva'
    )
    hora_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label='Hora de Inicio'
    )
    hora_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label='Hora de Fin'
    )
    proposito = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Propósito de la Reserva',
        max_length=500
    )

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        if hora_inicio and hora_fin:
            if hora_inicio >= hora_fin:
                raise forms.ValidationError('La hora de inicio debe ser anterior a la hora de fin.')
        
        return cleaned_data


class SubirSilaboForm(forms.Form):
    """Formulario para subir sílabo"""
    curso_id = forms.UUIDField(widget=forms.HiddenInput())
    archivo_silabo = forms.FileField(
        label='Archivo del Sílabo',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc'])],
        help_text='Archivos PDF o Word'
    )
    objetivos = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Objetivos del Curso',
        required=False
    )
    competencias = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Competencias',
        required=False
    )