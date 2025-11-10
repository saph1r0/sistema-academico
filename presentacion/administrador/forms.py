from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, date
from repositorio.postgres_repository.models import UsuarioModel


class ConfiguracionSistemaForm(forms.Form):
    """Formulario para configuración de parámetros del sistema"""
    
    capacidad_maxima_laboratorio = forms.IntegerField(
        label='Capacidad máxima por laboratorio',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '30'
        }),
        help_text='Número máximo de estudiantes por laboratorio (1-100)'
    )
    
    tiempo_sesion_minutos = forms.IntegerField(
        label='Tiempo de sesión (minutos)',
        validators=[MinValueValidator(30), MaxValueValidator(480)],
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '120'
        }),
        help_text='Duración de las sesiones en minutos (30-480)'
    )
    
    backup_automatico = forms.BooleanField(
        label='Backup automático',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Activar backups automáticos del sistema'
    )
    
    frecuencia_backup_horas = forms.IntegerField(
        label='Frecuencia de backup (horas)',
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '24'
        }),
        help_text='Intervalo entre backups automáticos en horas (1-168)'
    )
    
    alertas_activas = forms.BooleanField(
        label='Alertas del sistema',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Activar alertas automáticas del sistema'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        backup_automatico = cleaned_data.get('backup_automatico')
        frecuencia_backup = cleaned_data.get('frecuencia_backup_horas')
        
        if backup_automatico and not frecuencia_backup:
            raise forms.ValidationError(
                'Debe especificar la frecuencia de backup si está activado.'
            )
        
        return cleaned_data


class ReporteAsistenciaForm(forms.Form):
    """Formulario para generar reportes de asistencia"""
    
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    
    fecha_inicio = forms.DateField(
        label='Fecha de inicio',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Fecha de inicio del período a reportar'
    )
    
    fecha_fin = forms.DateField(
        label='Fecha de fin',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Fecha de fin del período a reportar'
    )
    
    formato = forms.ChoiceField(
        label='Formato de exportación',
        choices=FORMATO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    incluir_detalle = forms.BooleanField(
        label='Incluir detalle por estudiante',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Incluir información detallada de cada estudiante'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError(
                    'La fecha de inicio no puede ser posterior a la fecha de fin.'
                )
            
            if fecha_fin > date.today():
                raise forms.ValidationError(
                    'La fecha de fin no puede ser futura.'
                )
        
        return cleaned_data


class ReporteNotasForm(forms.Form):
    """Formulario para generar reportes de notas"""
    
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    
    TIPO_CHOICES = [
        ('global', 'Reporte Global'),
        ('por_curso', 'Por Curso'),
        ('por_docente', 'Por Docente'),
    ]
    
    tipo_reporte = forms.ChoiceField(
        label='Tipo de reporte',
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    ciclo = forms.CharField(
        label='Ciclo académico',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': '2024-1'
        }),
        help_text='Formato: YYYY-N (ej: 2024-1)'
    )
    
    curso_codigo = forms.CharField(
        label='Código del curso (opcional)',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Dejar vacío para todos los cursos'
        }),
        help_text='Solo para reportes por curso específico'
    )
    
    docente_email = forms.EmailField(
        label='Email del docente (opcional)',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Dejar vacío para todos los docentes'
        }),
        help_text='Solo para reportes por docente específico'
    )
    
    formato = forms.ChoiceField(
        label='Formato de exportación',
        choices=FORMATO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    incluir_estadisticas = forms.BooleanField(
        label='Incluir estadísticas',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Incluir promedios, desviación estándar, etc.'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_reporte = cleaned_data.get('tipo_reporte')
        curso_codigo = cleaned_data.get('curso_codigo')
        docente_email = cleaned_data.get('docente_email')
        
        if tipo_reporte == 'por_curso' and not curso_codigo:
            raise forms.ValidationError(
                'Debe especificar el código del curso para este tipo de reporte.'
            )
        
        if tipo_reporte == 'por_docente' and not docente_email:
            raise forms.ValidationError(
                'Debe especificar el email del docente para este tipo de reporte.'
            )
        
        return cleaned_data


class ReporteEstadisticasForm(forms.Form):
    """Formulario para generar reportes de estadísticas generales"""
    
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ]
    
    PERIODO_CHOICES = [
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('personalizado', 'Período personalizado'),
    ]
    
    periodo = forms.ChoiceField(
        label='Período del reporte',
        choices=PERIODO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    fecha_inicio = forms.DateField(
        label='Fecha de inicio (para período personalizado)',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    fecha_fin = forms.DateField(
        label='Fecha de fin (para período personalizado)',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    formato = forms.ChoiceField(
        label='Formato de exportación',
        choices=FORMATO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    incluir_graficos = forms.BooleanField(
        label='Incluir gráficos',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        help_text='Incluir gráficos estadísticos en el reporte'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if periodo == 'personalizado':
            if not fecha_inicio or not fecha_fin:
                raise forms.ValidationError(
                    'Debe especificar las fechas de inicio y fin para el período personalizado.'
                )
            
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError(
                    'La fecha de inicio no puede ser posterior a la fecha de fin.'
                )
        
        return cleaned_data