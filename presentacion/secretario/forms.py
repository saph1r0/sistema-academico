"""
Formularios para el módulo de secretarios
"""
from django import forms


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


class GenerarReporteForm(forms.Form):
    """Formulario para generar reportes académicos"""
    TIPOS_REPORTE = [
        ('asistencia_general', 'Reporte de Asistencia General'),
        ('notas_por_curso', 'Reporte de Notas por Curso'),
        ('estadisticas_periodo', 'Estadísticas por Período'),
        ('ocupacion_laboratorios', 'Ocupación de Laboratorios'),
        ('rendimiento_academico', 'Rendimiento Académico')
    ]
    
    FORMATOS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ]
    
    tipo_reporte = forms.ChoiceField(
        choices=TIPOS_REPORTE,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Reporte'
    )
    formato = forms.ChoiceField(
        choices=FORMATOS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Formato',
        initial='pdf'
    )
    periodo_id = forms.UUIDField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Período Académico',
        required=False
    )
    curso_id = forms.UUIDField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Curso (opcional)',
        required=False
    )
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de Inicio',
        required=False
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de Fin',
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        tipo_reporte = cleaned_data.get('tipo_reporte')
        curso_id = cleaned_data.get('curso_id')
        
        # Validar que para reportes por curso se especifique el curso
        if tipo_reporte == 'notas_por_curso' and not curso_id:
            raise forms.ValidationError('Debe especificar un curso para este tipo de reporte.')
        
        return cleaned_data


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