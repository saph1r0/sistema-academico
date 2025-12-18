from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, date
from repositorio.postgres_repository.models import UsuarioModel, AcademicPeriod


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
    TIPOS = [
        ('global', 'Global '),
        ('por_curso', 'Por Curso Específico'),
        ('por_estudiante', 'Por Estudiante '),
    ]
    
    tipo_reporte = forms.ChoiceField(
        label='Tipo de reporte',
        choices=TIPOS,
        widget=forms.Select(attrs={'class': 'w-full border-gray-300 rounded-lg'})
    )
    
    ciclo = forms.ModelChoiceField(
        queryset=AcademicPeriod.objects.all().order_by('-name'),
        label='Ciclo académico',
        empty_label=None,
        widget=forms.Select(attrs={'class': 'w-full border-gray-300 rounded-lg'})
    )
    
    curso_codigo = forms.CharField(
        label='Código del curso',
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-lg', 'placeholder': 'Ej: 1703240'})
    )
    
    estudiante_cui = forms.CharField(
        label='CUI del Estudiante',
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-lg', 'placeholder': 'Ej: 20210680'})
    )
   

    formato = forms.ChoiceField(
        label='Formato',
        choices=[('pdf', 'PDF')],
        widget=forms.Select(attrs={'class': 'w-full border-gray-300 rounded-lg'})
    )
    
    incluir_detalle = forms.BooleanField(
        label='Incluir detalle de sesiones',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600'})
    )

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_reporte')
        
        if tipo == 'por_curso' and not cleaned_data.get('curso_codigo'):
            self.add_error('curso_codigo', 'Debe ingresar el código del curso.')
            
        if tipo == 'por_estudiante' and not cleaned_data.get('estudiante_cui'):
            self.add_error('estudiante_cui', 'Debe ingresar el CUI del estudiante.')
            
        return cleaned_data

class ReporteNotasForm(forms.Form):
    TIPOS = [
        ('global', 'Reporte Global'),
        ('por_curso', 'Por Curso'),
        ('por_docente', 'Por Docente'),
    ]
    
    tipo_reporte = forms.ChoiceField(
        label='Tipo de reporte',
        choices=TIPOS,
        widget=forms.Select(attrs={'class': 'w-full border-gray-300 rounded-lg'})
    )
    
    ciclo = forms.ModelChoiceField(
        queryset=AcademicPeriod.objects.all().order_by('-name'),
        label='Ciclo académico',
        empty_label=None, 
        widget=forms.Select(attrs={'class': 'w-full border-gray-300 rounded-lg'})
    )
    
    curso_codigo = forms.CharField(
        label='Código del curso',
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-lg', 'placeholder': 'Ej: 1703240'})
    )
    
    docente_email = forms.EmailField(
        label='Email del docente',
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-lg', 'placeholder': 'docente@unsa.edu.pe'})
    )
    
    formato = forms.ChoiceField(
        label='Formato de exportación',
        choices=[('pdf', 'PDF')], 
        widget=forms.Select(attrs={'class': 'w-full border-gray-300 rounded-lg'})
    )
    
    incluir_estadisticas = forms.BooleanField(
        label='Incluir estadísticas',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600'})
    )

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_reporte')
        
        if tipo == 'por_curso' and not cleaned_data.get('curso_codigo'):
            self.add_error('curso_codigo', 'Este campo es obligatorio para reportes por curso.')
        
        if tipo == 'por_docente' and not cleaned_data.get('docente_email'):
            self.add_error('docente_email', 'El email es obligatorio para reportes por docente.')
            
        return cleaned_data


class ReporteEstadisticasForm(forms.Form):
   
    
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