"""
Formularios para el módulo de secretarios
"""
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, date
from repositorio.postgres_repository.models import UsuarioModel, AcademicPeriod, Course, Teacher


class GestionarInscripcionForm(forms.Form):
    """Formulario para gestionar inscripciones de laboratorio"""
    inscripcion_id = forms.UUIDField(widget=forms.HiddenInput())
    accion = forms.ChoiceField(
        choices=[
            ('aprobar', 'Aprobar'),
            ('rechazar', 'Rechazar'),
            ('redistribuir', 'Redistribuir')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label='Motivo (opcional)',
        required=False
    )
    nuevo_laboratorio_id = forms.UUIDField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Nuevo Laboratorio',
        required=False
    )


class FiltroLaboratoriosForm(forms.Form):
    """Formulario para filtrar inscripciones de laboratorio"""
    curso = forms.UUIDField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Curso',
        required=False
    )
    laboratorio = forms.UUIDField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Laboratorio',
        required=False
    )
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('active', 'Activo'),
            ('withdrawn', 'Retirado'),
            ('pending', 'Pendiente')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Estado',
        required=False
    )



from repositorio.postgres_repository.models import AcademicPeriod, Course, Teacher


class SecretaryExamFilterForm(forms.Form):
    academic_period = forms.ModelChoiceField(
        queryset=AcademicPeriod.objects.filter(is_active=True).order_by('-start_date'),
        required=False,
        label="Periodo académico"
    )

    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True).order_by('name'),
        required=False,
        label="Asignatura"
    )

    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.select_related("user").order_by('user__last_name', 'user__first_name'),
        required=False,
        label="Docente"
    )

    exam_number = forms.ChoiceField(
        choices=[
            ("", "Todos"),
            ("1", "Primer Parcial"),
            ("2", "Segundo Parcial"),
            ("3", "Tercer Parcial"),
        ],
        required=False,
        label="Parcial"
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Desde"
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Hasta"
    )
class ReporteAsistenciaForm(forms.Form):
    TIPOS = [
        ('global', 'Global (Todos los Cursos)'),
        ('por_curso', 'Por Curso Específico'),
        ('por_estudiante', 'Por Estudiante'),
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
        required=False,
        initial=True,
        widget=forms.HiddenInput()
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
        ('global', 'Global (Todos los Cursos)'),
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
        required=False,
        initial=True,
        widget=forms.HiddenInput()
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
        label='Fecha de inicio',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        })
    )
    
    fecha_fin = forms.DateField(
        label='Fecha de fin',
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
        required=False,
        initial=True,
        widget=forms.HiddenInput()
    )
    
    def clean(self):
        cleaned_data = super().clean()
        periodo = cleaned_data.get('periodo')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if periodo == 'personalizado':
            if not fecha_inicio or not fecha_fin:
                raise forms.ValidationError('Debe especificar las fechas de inicio y fin para el período personalizado.')
            
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin.')
        
        return cleaned_data