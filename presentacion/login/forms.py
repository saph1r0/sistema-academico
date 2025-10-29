"""
Formularios para el sistema de autenticación
"""
import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class InstitutionalLoginForm(AuthenticationForm):
    """Formulario de login con email institucional"""
    
    username = forms.EmailField(
        label='Email Institucional',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo: sesteba@unsa.edu.pe',
            'autofocus': True
        }),
        help_text='Usa tu email institucional'
    )
    
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
    )
    
    def clean_username(self):
        """Valida el formato del email institucional"""
        email = self.cleaned_data.get('username', '').lower().strip()
        
        if not email:
            raise ValidationError('El email institucional es requerido.')
        
        # Validar formato del email institucional
        pattern = r'^[a-z]+[a-z]*@unsa\.edu\.pe$'
        if not re.match(pattern, email):
            raise ValidationError(
                'Formato de email institucional inválido. '
                'Debe terminar en @unsa.edu.pe'
            )
        
        return email