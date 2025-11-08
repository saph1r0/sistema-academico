"""
Modelos Django ORM simplificados para PostgreSQL - Versión Simple
"""
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class User(models.Model):
    """Modelo de usuario simple sin herencia de AbstractUser"""
    
    ROLE_CHOICES = [
        ('student', 'Estudiante'),
        ('teacher', 'Profesor'),
        ('secretary', 'Secretario'),
        ('admin', 'Administrador'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institutional_email = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    password = models.CharField(max_length=128)  # Para almacenar contraseñas hasheadas
    
    # Campos de estado
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.institutional_email} - {self.get_role_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def set_password(self, raw_password):
        """Establece la contraseña hasheada"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verifica la contraseña"""
        return check_password(raw_password, self.password)
    
    def is_admin(self):
        return self.role == 'admin' and self.is_active
    
    def is_teacher(self):
        return self.role == 'teacher' and self.is_active
    
    def is_student(self):
        return self.role == 'student' and self.is_active
    
    def is_secretary(self):
        return self.role == 'secretary' and self.is_active
    
    # Métodos adicionales para compatibilidad con el sistema de permisos
    def is_secretaria(self):
        """Alias para compatibilidad"""
        return self.is_secretary()
    
    def is_docente(self):
        """Alias para compatibilidad"""
        return self.is_teacher()
    
    def is_estudiante(self):
        """Alias para compatibilidad"""
        return self.is_student()


class Student(models.Model):
    """Modelo de estudiante"""
    
    ACADEMIC_STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_code = models.CharField(max_length=20, unique=True)  # CUI
    career = models.CharField(max_length=100, null=True, blank=True)
    current_cycle = models.IntegerField(null=True, blank=True)
    academic_status = models.CharField(max_length=20, choices=ACADEMIC_STATUS_CHOICES, default='active')
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
    
    def __str__(self):
        return f"{self.student_code} - {self.user.get_full_name()}"


class Teacher(models.Model):
    """Modelo de profesor"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    specialty = models.CharField(max_length=100, null=True, blank=True)
    hours_per_week = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'teachers'
        verbose_name = 'Profesor'
        verbose_name_plural = 'Profesores'
    
    def __str__(self):
        return f"{self.teacher_code} - {self.user.get_full_name()}"