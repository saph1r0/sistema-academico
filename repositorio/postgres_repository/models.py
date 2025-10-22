"""
Modelos Django ORM para PostgreSQL
Estos modelos representan las tablas en la base de datos
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator, EmailValidator


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo UsuarioModel
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el email y contraseña dados
        """
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el email y contraseña dados
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        extra_fields.setdefault('activo', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class UsuarioModel(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser
    Integra con el dominio Usuario existente
    """
    ROLES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
        ('secretaria', 'Secretaria'),
        ('admin', 'Administrador'),
    ]
    
    # Usar email como username
    username = None
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name="Correo Institucional"
    )
    
    # Campos adicionales del dominio
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    apellido = models.CharField(max_length=200, verbose_name="Apellido")
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='estudiante',
        db_index=True,
        verbose_name="Rol"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Usuario Activo"
    )
    ultimo_acceso = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Último Acceso"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'rol']
    
    objects = UsuarioManager()
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['apellido', 'nombre']
        indexes = [
            models.Index(fields=['email'], name='idx_usuario_email'),
            models.Index(fields=['rol'], name='idx_usuario_rol'),
            models.Index(fields=['activo'], name='idx_usuario_activo'),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.get_rol_display()}"
    
    def is_admin(self):
        """Verifica si el usuario tiene rol de administrador"""
        return self.rol == 'admin' and self.activo and self.is_active
    
    def is_secretaria(self):
        """Verifica si el usuario tiene rol de secretaria"""
        return self.rol == 'secretaria' and self.activo and self.is_active
    
    def is_docente(self):
        """Verifica si el usuario tiene rol de docente"""
        return self.rol == 'docente' and self.activo and self.is_active
    
    def is_estudiante(self):
        """Verifica si el usuario tiene rol de estudiante"""
        return self.rol == 'estudiante' and self.activo and self.is_active
    
    def activar_usuario(self):
        """Activa el usuario"""
        self.activo = True
        self.is_active = True
        self.save()
    
    def desactivar_usuario(self):
        """Desactiva el usuario"""
        self.activo = False
        self.is_active = False
        self.save()
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha de último acceso"""
        from django.utils import timezone
        self.ultimo_acceso = timezone.now()
        self.save(update_fields=['ultimo_acceso'])


class LaboratorioModel(models.Model):
    """
    Modelo ORM para laboratorios/ambientes
    """
    TIPOS_LABORATORIO = [
        ('COMPUTO', 'Laboratorio de Cómputo'),
        ('FISICA', 'Laboratorio de Física'),
        ('QUIMICA', 'Laboratorio de Química'),
        ('ELECTRONICA', 'Laboratorio de Electrónica'),
        ('AULA', 'Aula Regular'),
        ('AUDITORIO', 'Auditorio'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Laboratorio")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_LABORATORIO,
        default='COMPUTO',
        verbose_name="Tipo de Laboratorio"
    )
    capacidad = models.PositiveIntegerField(verbose_name="Capacidad Máxima")
    ubicacion = models.CharField(max_length=200, verbose_name="Ubicación")
    equipamiento = models.TextField(blank=True, verbose_name="Descripción del Equipamiento")
    activo = models.BooleanField(default=True, verbose_name="Laboratorio Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'laboratorios'
        verbose_name = 'Laboratorio'
        verbose_name_plural = 'Laboratorios'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['codigo'], name='idx_laboratorio_codigo'),
            models.Index(fields=['tipo'], name='idx_laboratorio_tipo'),
            models.Index(fields=['activo'], name='idx_laboratorio_activo'),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ReservaModel(models.Model):
    """
    Modelo ORM para reservas de laboratorios
    """
    ESTADOS_RESERVA = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada Automáticamente'),
        ('APROBADA_MANUAL', 'Aprobada Manualmente'),
        ('RECHAZADA', 'Rechazada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    ]
    
    laboratorio = models.ForeignKey(
        LaboratorioModel,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name="Laboratorio"
    )
    docente = models.ForeignKey(
        UsuarioModel,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'docente'},
        related_name='reservas_docente',
        verbose_name="Docente Solicitante"
    )
    fecha_reserva = models.DateField(verbose_name="Fecha de Reserva")
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(verbose_name="Hora de Fin")
    proposito = models.CharField(max_length=200, verbose_name="Propósito de la Reserva")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_RESERVA,
        default='PENDIENTE',
        db_index=True,
        verbose_name="Estado"
    )
    aprobada_automaticamente = models.BooleanField(
        default=False,
        verbose_name="Aprobada Automáticamente"
    )
    motivo_rechazo = models.TextField(blank=True, verbose_name="Motivo de Rechazo")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    procesada_por = models.ForeignKey(
        UsuarioModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservas_procesadas',
        verbose_name="Procesada Por"
    )
    
    class Meta:
        db_table = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['laboratorio', 'fecha_reserva'], name='idx_reserva_lab_fecha'),
            models.Index(fields=['estado'], name='idx_reserva_estado'),
            models.Index(fields=['docente'], name='idx_reserva_docente'),
            models.Index(fields=['fecha_reserva', 'hora_inicio'], name='idx_reserva_horario'),
        ]
        unique_together = [
            ['laboratorio', 'fecha_reserva', 'hora_inicio', 'hora_fin']
        ]
    
    def __str__(self):
        return f"{self.laboratorio.codigo} - {self.fecha_reserva} {self.hora_inicio}-{self.hora_fin}"
    
    def tiene_conflicto(self):
        """Verifica si existe conflicto con otras reservas"""
        conflictos = ReservaModel.objects.filter(
            laboratorio=self.laboratorio,
            fecha_reserva=self.fecha_reserva,
            estado__in=['APROBADA', 'APROBADA_MANUAL']
        ).exclude(id=self.id if self.id else None)
        
        for reserva in conflictos:
            if (self.hora_inicio < reserva.hora_fin and self.hora_fin > reserva.hora_inicio):
                return True
        return False
    
    def duracion_horas(self):
        """Calcula la duración de la reserva en horas"""
        from datetime import datetime, timedelta
        inicio = datetime.combine(self.fecha_reserva, self.hora_inicio)
        fin = datetime.combine(self.fecha_reserva, self.hora_fin)
        duracion = fin - inicio
        return duracion.total_seconds() / 3600


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