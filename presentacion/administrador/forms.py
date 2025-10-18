from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator


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