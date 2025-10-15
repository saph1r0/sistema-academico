"""
Modelos Django ORM para PostgreSQL
Estos modelos representan las tablas en la base de datos
"""
from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator


class EstudianteModel(models.Model):
    """
    Modelo ORM para la tabla de estudiantes
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        validators=[MinLengthValidator(6)],
        db_index=True,
        verbose_name="Código CUI"
    )
    apellidos = models.CharField(max_length=200, verbose_name="Apellidos")
    nombres = models.CharField(max_length=200, verbose_name="Nombres")
    correo_institucional = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name="Correo Institucional"
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('DESACTIVADO', 'Desactivado'),  
            ('ACTIVO', 'Activo'),
            ('RETIRADO', 'Retirado'),
            ('ABANDONO', 'Abandono'),
        ],
        default='DESACTIVADO',  
        db_index=True,
        verbose_name="Estado"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'estudiantes'
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['apellidos', 'nombres']
        indexes = [
            models.Index(fields=['codigo'], name='idx_estudiante_codigo'),
            models.Index(fields=['estado'], name='idx_estudiante_estado'),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.apellidos}, {self.nombres}"


class MatriculaModel(models.Model):
    """
    Modelo ORM para la tabla de matrículas
    """
    estudiante_codigo = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(6)],
        db_index=True,
        verbose_name="Código del Estudiante"
    )
    curso_codigo = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Código del Curso"
    )
    ciclo = models.CharField(
        max_length=10,
        db_index=True,
        verbose_name="Ciclo Académico"
    )
    grupo = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Grupo A'),
            ('B', 'Grupo B'),
            ('C', 'Grupo C'),
            ('D', 'Grupo D'),
        ],
        verbose_name="Grupo"
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden Alfabético"
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('MATRICULADO', 'Matriculado'),
            ('RETIRADO', 'Retirado'),
        ],
        default='MATRICULADO',
        db_index=True,
        verbose_name="Estado"
    )
    fecha_matricula = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'matriculas'
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        ordering = ['curso_codigo', 'grupo', 'orden']
        unique_together = [
            ['estudiante_codigo', 'curso_codigo', 'ciclo']
        ]
        indexes = [
            models.Index(fields=['estudiante_codigo'], name='idx_matricula_estudiante'),
            models.Index(fields=['curso_codigo', 'ciclo'], name='idx_matricula_curso'),
            models.Index(fields=['ciclo', 'grupo'], name='idx_matricula_ciclo_grupo'),
        ]
    
    def __str__(self):
        return f"{self.estudiante_codigo} - {self.curso_codigo} ({self.ciclo}-{self.grupo})"