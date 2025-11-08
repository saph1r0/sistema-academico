"""
Formularios para el módulo de estudiantes
"""
from django import forms


class MatriculaLaboratorioForm(forms.Form):
    """Formulario para matrícula en laboratorios"""
    laboratorio_id = forms.UUIDField(widget=forms.HiddenInput())
    accion = forms.ChoiceField(
        choices=[
            ('matricular', 'Matricular'),
            ('desmatricular', 'Desmatricular')
        ],
        widget=forms.HiddenInput()
    )

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        laboratorio_id = cleaned_data.get('laboratorio_id')
        
        if not accion or not laboratorio_id:
            raise forms.ValidationError('Datos incompletos para procesar la solicitud.')
        
        return cleaned_data