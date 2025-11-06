# Generated migration for PhaseGrade and SimpleAttendanceRecord models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('postgres_repository', '0002_enhance_teacher_attendance'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhaseGrade',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phase', models.CharField(choices=[('primera', 'Primera Fase'), ('segunda', 'Segunda Fase'), ('tercera', 'Tercera Fase')], max_length=20, verbose_name='Fase Académica')),
                ('partial_grade', models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Nota Parcial')),
                ('continuous_grade', models.DecimalField(decimal_places=2, max_digits=4, verbose_name='Nota Continua')),
                ('final_phase_grade', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name='Nota Final de Fase')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')),
                ('course_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phase_grades', to='postgres_repository.coursegroup', verbose_name='Grupo de Curso')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phase_grades', to='postgres_repository.student', verbose_name='Estudiante')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='postgres_repository.teacher', verbose_name='Subido por')),
            ],
            options={
                'verbose_name': 'Nota por Fase',
                'verbose_name_plural': 'Notas por Fase',
                'db_table': 'phase_grades',
            },
        ),
        migrations.CreateModel(
            name='SimpleAttendanceRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('class_date', models.DateField(verbose_name='Fecha de Clase')),
                ('status', models.CharField(choices=[('PRESENTE', 'Presente'), ('FALTA', 'Falta')], max_length=20, verbose_name='Estado de Asistencia')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')),
                ('session_info', models.JSONField(blank=True, null=True, verbose_name='Información de Sesión')),
                ('bulk_session_id', models.UUIDField(blank=True, null=True, verbose_name='ID de Sesión Masiva')),
                ('notes', models.TextField(blank=True, verbose_name='Observaciones')),
                ('course_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='simple_attendance_records', to='postgres_repository.coursegroup', verbose_name='Grupo de Curso')),
                ('recorded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='postgres_repository.teacher', verbose_name='Registrado por')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='simple_attendance_records', to='postgres_repository.student', verbose_name='Estudiante')),
            ],
            options={
                'verbose_name': 'Registro de Asistencia Simple',
                'verbose_name_plural': 'Registros de Asistencia Simple',
                'db_table': 'simple_attendance_records',
            },
        ),
        migrations.AddConstraint(
            model_name='phasegrade',
            constraint=models.UniqueConstraint(fields=('student', 'course_group', 'phase'), name='unique_student_course_phase'),
        ),
        migrations.AddConstraint(
            model_name='simpleattendancerecord',
            constraint=models.UniqueConstraint(fields=('student', 'course_group', 'class_date'), name='unique_student_course_date'),
        ),
        migrations.AddIndex(
            model_name='phasegrade',
            index=models.Index(fields=['student', 'phase'], name='idx_phase_grade_student_phase'),
        ),
        migrations.AddIndex(
            model_name='phasegrade',
            index=models.Index(fields=['course_group', 'phase'], name='idx_phase_grade_course_phase'),
        ),
        migrations.AddIndex(
            model_name='phasegrade',
            index=models.Index(fields=['phase'], name='idx_phase_grade_phase'),
        ),
        migrations.AddIndex(
            model_name='simpleattendancerecord',
            index=models.Index(fields=['class_date'], name='idx_simple_att_date'),
        ),
        migrations.AddIndex(
            model_name='simpleattendancerecord',
            index=models.Index(fields=['course_group', 'class_date'], name='idx_simple_att_course_date'),
        ),
        migrations.AddIndex(
            model_name='simpleattendancerecord',
            index=models.Index(fields=['status'], name='idx_simple_att_status'),
        ),
        migrations.AddIndex(
            model_name='simpleattendancerecord',
            index=models.Index(fields=['bulk_session_id'], name='idx_simple_att_bulk_session'),
        ),
    ]