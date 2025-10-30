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

# Nuevos modelos para el sistema de profesor y secretaria

class CourseContent(models.Model):
    """Modelo para el contenido/avance del curso basado en sílabo"""
    CONTENT_TYPES = [
        ('unit', 'Unidad'),
        ('chapter', 'Capítulo'),
        ('topic', 'Tema'),
        ('subtopic', 'Subtema'),
        ('exam', 'Examen'),
        ('assignment', 'Tarea'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contents', verbose_name='Curso')
    unit_name = models.CharField(max_length=200, verbose_name='Nombre de Unidad')
    chapter_name = models.CharField(max_length=200, blank=True, verbose_name='Nombre del Capítulo')
    topic_number = models.CharField(max_length=20, verbose_name='Número de Tema')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descripción')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='topic', verbose_name='Tipo')
    week_number = models.IntegerField(verbose_name='Semana')
    order = models.IntegerField(default=1, verbose_name='Orden')
    is_completed = models.BooleanField(default=False, verbose_name='Completado')
    completion_date = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Completado')
    file_upload = models.FileField(upload_to='course_content/', null=True, blank=True, verbose_name='Archivo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_contents'
        verbose_name = 'Contenido del Curso'
        verbose_name_plural = 'Contenidos del Curso'
        ordering = ['week_number', 'order']
    
    def __str__(self):
        return f"{self.course.name} - {self.topic_number}: {self.title}"


class TeacherAttendance(models.Model):
    """Modelo para registro automático de asistencia docente"""
    ACCESS_TYPES = [
        ('presential', 'Presencial'),
        ('remote', 'Remoto'),
        ('virtual', 'Virtual/VPN'),
        ('unknown', 'Desconocido')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendance_records')
    login_time = models.DateTimeField(verbose_name='Hora de Ingreso')
    logout_time = models.DateTimeField(null=True, blank=True, verbose_name='Hora de Salida')
    ip_address = models.GenericIPAddressField(verbose_name='Dirección IP')
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES, verbose_name='Tipo de Acceso')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'teacher_attendance'
        verbose_name = 'Asistencia Docente'
        verbose_name_plural = 'Asistencias Docentes'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"


class Grade(models.Model):
    """Modelo para notas de estudiantes"""
    EXAM_TYPES = [
        ('parcial_1', 'Primer Parcial'),
        ('parcial_2', 'Segundo Parcial'),
        ('parcial_3', 'Tercer Parcial'),
        ('sustitutorio', 'Examen Sustitutorio'),
        ('final', 'Examen Final'),
        ('tarea', 'Tarea'),
        ('proyecto', 'Proyecto')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES, verbose_name='Tipo de Evaluación')
    grade_component = models.CharField(max_length=50, verbose_name='Componente')  # Nota 1, Nota 2, etc.
    grade = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Nota')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'grades'
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'
        unique_together = ['student', 'course', 'exam_type', 'grade_component']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.course.name} - {self.exam_type}: {self.grade}"


class ExamStatistics(models.Model):
    """Modelo para estadísticas de exámenes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_stats')
    exam_type = models.CharField(max_length=20, choices=Grade.EXAM_TYPES, verbose_name='Tipo de Examen')
    max_grade = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Nota Máxima')
    min_grade = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Nota Mínima')
    avg_grade = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Nota Promedio')
    total_students = models.IntegerField(verbose_name='Total Estudiantes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'exam_statistics'
        verbose_name = 'Estadística de Examen'
        verbose_name_plural = 'Estadísticas de Exámenes'
        unique_together = ['course', 'exam_type']
    
    def __str__(self):
        return f"{self.course.name} - {self.exam_type} - Promedio: {self.avg_grade}"


class Attendance(models.Model):
    """Modelo para asistencia de estudiantes"""
    STATUS_CHOICES = [
        ('present', 'Presente'),
        ('absent', 'Ausente'),
        ('late', 'Tardanza'),
        ('justified', 'Justificado'),
        ('pending', 'Pendiente')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(verbose_name='Fecha')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Estado')
    notes = models.TextField(blank=True, verbose_name='Observaciones')
    recorded_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name='Registrado por')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_attendance'
        verbose_name = 'Asistencia Estudiante'
        verbose_name_plural = 'Asistencias Estudiantes'
        unique_together = ['student', 'course', 'date']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.course.name} - {self.date}: {self.status}"


class Classroom(models.Model):
    """Modelo para aulas y laboratorios"""
    ROOM_TYPES = [
        ('classroom', 'Aula'),
        ('laboratory', 'Laboratorio'),
        ('auditorium', 'Auditorio'),
        ('workshop', 'Taller')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nombre')
    code = models.CharField(max_length=20, unique=True, verbose_name='Código')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, verbose_name='Tipo')
    capacity = models.IntegerField(verbose_name='Capacidad')
    equipment = models.TextField(blank=True, verbose_name='Equipamiento')
    location = models.CharField(max_length=100, verbose_name='Ubicación')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'classrooms'
        verbose_name = 'Aula/Laboratorio'
        verbose_name_plural = 'Aulas/Laboratorios'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Reservation(models.Model):
    """Modelo para reservas de aulas y laboratorios"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
        ('cancelled', 'Cancelada')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='reservations')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='reservations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reservations')
    date = models.DateField(verbose_name='Fecha')
    start_time = models.TimeField(verbose_name='Hora Inicio')
    end_time = models.TimeField(verbose_name='Hora Fin')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Estado')
    purpose = models.TextField(verbose_name='Propósito')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Aprobado por')
    
    class Meta:
        db_table = 'reservations'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.classroom.name} - {self.date}"


# Métodos adicionales para el modelo Course (sin campos adicionales por ahora)
def get_expected_progress(self):
    """Calcula el progreso esperado basado en la semana actual"""
    # Simplificado: asumimos que estamos en la semana 8 de 17
    current_week = 8  # En una implementación real, esto se calcularía basado en fechas
    total_weeks = 17  # Valor por defecto
    return min((current_week / total_weeks) * 100, 100)

def get_actual_progress(self):
    """Calcula el progreso real basado en contenido completado"""
    # Por ahora retorna un valor simulado
    return 35.0

Course.add_to_class('get_expected_progress', get_expected_progress)
Course.add_to_class('get_actual_progress', get_actual_progress)

# Modelos adicionales para el sistema de reportes y gráficos

class AttendanceRecord(models.Model):
    """Modelo mejorado para registro de asistencia con soporte para gráficos"""
    STATUS_CHOICES = [
        ('present', 'Presente'),
        ('absent', 'Ausente'),
        ('late', 'Tardanza'),
        ('excused', 'Justificado')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records_new')
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(verbose_name='Fecha')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name='Estado')
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Registrado por')
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    notes = models.TextField(blank=True, verbose_name='Observaciones')
    
    class Meta:
        db_table = 'attendance_records'
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        unique_together = ['student', 'course_group', 'date']
        indexes = [
            models.Index(fields=['date'], name='idx_attendance_date'),
            models.Index(fields=['status'], name='idx_attendance_status'),
            models.Index(fields=['course_group', 'date'], name='idx_attendance_course_date'),
        ]
    
    def __str__(self):
        return f"{self.student.student_code} - {self.course_group} - {self.date}: {self.get_status_display()}"


class AttendanceStatistics(models.Model):
    """Modelo para estadísticas precalculadas de asistencia"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_stats')
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='attendance_stats')
    total_classes = models.IntegerField(default=0, verbose_name='Total de clases')
    present_count = models.IntegerField(default=0, verbose_name='Asistencias')
    absent_count = models.IntegerField(default=0, verbose_name='Faltas')
    late_count = models.IntegerField(default=0, verbose_name='Tardanzas')
    excused_count = models.IntegerField(default=0, verbose_name='Justificadas')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Porcentaje')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        db_table = 'attendance_statistics'
        verbose_name = 'Estadística de Asistencia'
        verbose_name_plural = 'Estadísticas de Asistencia'
        unique_together = ['student', 'course_group']
        indexes = [
            models.Index(fields=['percentage'], name='idx_attendance_percentage'),
            models.Index(fields=['course_group'], name='idx_attendance_course_group'),
        ]
    
    def __str__(self):
        return f"{self.student.student_code} - {self.course_group}: {self.percentage}%"
    
    def update_statistics(self):
        """Actualiza las estadísticas basadas en los registros de asistencia"""
        records = AttendanceRecord.objects.filter(
            student=self.student,
            course_group=self.course_group
        )
        
        self.total_classes = records.count()
        self.present_count = records.filter(status='present').count()
        self.absent_count = records.filter(status='absent').count()
        self.late_count = records.filter(status='late').count()
        self.excused_count = records.filter(status='excused').count()
        
        if self.total_classes > 0:
            # Considerar tardanzas como 0.5 asistencia
            effective_present = self.present_count + (self.late_count * 0.5) + self.excused_count
            self.percentage = (effective_present / self.total_classes) * 100
        else:
            self.percentage = 0
        
        self.save()


class EvaluationType(models.Model):
    """Modelo para tipos de evaluación (mapea a evaluation_types existente)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='evaluation_types_new')
    name = models.CharField(max_length=100, verbose_name='Nombre')
    weight = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, verbose_name='Peso')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, verbose_name='Puntaje máximo')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evaluation_types'
        verbose_name = 'Tipo de Evaluación'
        verbose_name_plural = 'Tipos de Evaluación'
    
    def __str__(self):
        return f"{self.course_group} - {self.name}"


class GradeRecord(models.Model):
    """Modelo para registros de notas (mapea a grades existente)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grade_records')
    evaluation_type = models.ForeignKey(EvaluationType, on_delete=models.CASCADE, related_name='grade_records')
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Puntaje')
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Registrado por')
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'grade_records_new'
        verbose_name = 'Registro de Nota'
        verbose_name_plural = 'Registros de Notas'
        unique_together = ['student', 'evaluation_type']
        indexes = [
            models.Index(fields=['score'], name='idx_grade_score_new'),
            models.Index(fields=['evaluation_type'], name='idx_grade_evaluation_type_new'),
        ]
    
    def __str__(self):
        return f"{self.student.student_code} - {self.evaluation_type.name}: {self.score}"


class CourseAssignment(models.Model):
    """Modelo para asignaciones de profesores a cursos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_assignments')
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='assignments')
    academic_period = models.ForeignKey(AcademicPeriod, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de asignación')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        db_table = 'course_assignments'
        verbose_name = 'Asignación de Curso'
        verbose_name_plural = 'Asignaciones de Curso'
        unique_together = ['teacher', 'course_group', 'academic_period']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.course_group}"