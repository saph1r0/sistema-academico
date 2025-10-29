"""
Modelos Django ORM simplificados para PostgreSQL
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, institutional_email, password=None, **extra_fields):
        if not institutional_email:
            raise ValueError('El email institucional es obligatorio')
        
        institutional_email = self.normalize_email(institutional_email)
        user = self.model(institutional_email=institutional_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, institutional_email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(institutional_email, password, **extra_fields)


class User(AbstractUser):
    """Modelo de usuario que mapea a la tabla 'users' de PostgreSQL"""
    
    ROLE_CHOICES = [
        ('student', 'Estudiante'),
        ('teacher', 'Profesor'),
        ('secretary', 'Secretario'),
        ('admin', 'Administrador'),
    ]
    
    # Reemplazar username con institutional_email
    username = None
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institutional_email = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # Campos heredados de AbstractUser que necesitamos mantener
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    
    USERNAME_FIELD = 'institutional_email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.institutional_email} - {self.get_role_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
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


# Alias para compatibilidad con el código existente
UsuarioModel = User


class Student(models.Model):
    """Modelo de estudiante que mapea a la tabla 'students'"""
    
    ACADEMIC_STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
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
    """Modelo de profesor que mapea a la tabla 'teachers'"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
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


class AcademicPeriod(models.Model):
    """Modelo de período académico"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)  # Ej: '2024-I', '2024-II'
    start_date = models.DateField()
    end_date = models.DateField()
    laboratory_enrollment_start = models.DateField()
    laboratory_enrollment_end = models.DateField()
    enrollment_change_deadline = models.DateField()
    is_active = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'academic_periods'
        verbose_name = 'Período Académico'
        verbose_name_plural = 'Períodos Académicos'
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """Modelo de curso"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    credits = models.IntegerField()
    theory_hours = models.IntegerField(default=0)
    practice_hours = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'courses'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseGroup(models.Model):
    """Modelo de grupo de curso (secciones)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    academic_period = models.ForeignKey(AcademicPeriod, on_delete=models.CASCADE)
    group_code = models.CharField(max_length=10)  # 'A', 'B', 'C'
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.IntegerField()
    enrolled_students = models.IntegerField(default=0)
    schedule_info = models.JSONField(null=True, blank=True)
    classroom = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'course_groups'
        verbose_name = 'Grupo de Curso'
        verbose_name_plural = 'Grupos de Curso'
        unique_together = ['course', 'academic_period', 'group_code']
    
    def __str__(self):
        return f"{self.course.code} - {self.group_code} ({self.academic_period.name})"


class Laboratory(models.Model):
    """Modelo de laboratorio"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE)
    lab_code = models.CharField(max_length=10)  # 'L1', 'L2'
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.IntegerField()
    enrolled_students = models.IntegerField(default=0)
    schedule_info = models.JSONField()
    lab_room = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'laboratories'
        verbose_name = 'Laboratorio'
        verbose_name_plural = 'Laboratorios'
    
    def __str__(self):
        return f"{self.course_group.course.code} - {self.lab_code}"


class Enrollment(models.Model):
    """Modelo de matrícula principal"""
    
    ENROLLMENT_TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('special', 'Especial'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('withdrawn', 'Retirado'),
        ('failed', 'Desaprobado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE)
    academic_period = models.ForeignKey(AcademicPeriod, on_delete=models.CASCADE)
    enrollment_date = models.DateField(default=timezone.now)
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPE_CHOICES, default='regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        db_table = 'enrollments'
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        unique_together = ['student', 'course_group', 'academic_period']
    
    def __str__(self):
        return f"{self.student.student_code} - {self.course_group}"


class LaboratoryEnrollment(models.Model):
    """Modelo de matrícula en laboratorio"""
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('withdrawn', 'Retirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    enrollment_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'laboratory_enrollments'
        verbose_name = 'Matrícula de Laboratorio'
        verbose_name_plural = 'Matrículas de Laboratorio'
        unique_together = ['student', 'laboratory']
    
    def __str__(self):
        return f"{self.student.student_code} - {self.laboratory}"


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


# Modelos de compatibilidad con el código existente

class EstudianteModel(models.Model):
    """Modelo de compatibilidad para el código existente"""
    
    ESTADOS_ESTUDIANTE = [
        ('DESACTIVADO', 'Desactivado'),
        ('ACTIVO', 'Activo'),
        ('RETIRADO', 'Retirado'),
        ('ABANDONO', 'Abandono'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de Estudiante")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    correo_institucional = models.EmailField(unique=True, verbose_name="Correo Institucional")
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_ESTUDIANTE,
        default='DESACTIVADO',
        verbose_name="Estado"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Relación opcional con el nuevo sistema de usuarios
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='estudiante_legacy',
        null=True, 
        blank=True,
        verbose_name="Usuario Asociado"
    )
    
    class Meta:
        db_table = 'estudiantes_legacy'
        verbose_name = 'Estudiante (Legacy)'
        verbose_name_plural = 'Estudiantes (Legacy)'
        ordering = ['apellidos', 'nombres']
        indexes = [
            models.Index(fields=['codigo'], name='idx_estudiante_codigo'),
            models.Index(fields=['correo_institucional'], name='idx_estudiante_correo'),
            models.Index(fields=['estado'], name='idx_estudiante_estado'),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.apellidos}, {self.nombres}"
    
    def get_nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class MatriculaModel(models.Model):
    """Modelo de matrícula para compatibilidad"""
    
    ESTADOS_MATRICULA = [
        ('ACTIVA', 'Activa'),
        ('RETIRADA', 'Retirada'),
        ('ANULADA', 'Anulada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estudiante = models.ForeignKey(EstudianteModel, on_delete=models.CASCADE, related_name='matriculas', null=True, blank=True)
    periodo_academico = models.CharField(max_length=20, verbose_name="Período Académico")
    fecha_matricula = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_MATRICULA,
        default='ACTIVA',
        verbose_name="Estado"
    )
    
    class Meta:
        db_table = 'matriculas_legacy'
        verbose_name = 'Matrícula (Legacy)'
        verbose_name_plural = 'Matrículas (Legacy)'
        unique_together = ['estudiante', 'periodo_academico']
    
    def __str__(self):
        return f"{self.estudiante.codigo} - {self.periodo_academico}"


# Alias para compatibilidad con el código existente
UsuarioModel = User
DocenteModel = Teacher