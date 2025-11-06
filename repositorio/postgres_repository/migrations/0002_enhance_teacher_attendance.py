# Generated migration for enhanced TeacherAttendance model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('postgres_repository', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacherattendance',
            name='course_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='postgres_repository.coursegroup', verbose_name='Grupo de Curso'),
        ),
        migrations.AddField(
            model_name='teacherattendance',
            name='session_duration',
            field=models.DurationField(blank=True, null=True, verbose_name='Duración de Sesión'),
        ),
        migrations.AddField(
            model_name='teacherattendance',
            name='triggered_progress_update',
            field=models.BooleanField(default=False, verbose_name='Actualizó Progreso'),
        ),
        migrations.AlterField(
            model_name='teacherattendance',
            name='access_type',
            field=models.CharField(choices=[('presential', 'Presencial'), ('remote', 'Remoto'), ('virtual', 'Virtual/VPN'), ('unknown', 'Desconocido')], default='unknown', max_length=20, verbose_name='Tipo de Acceso'),
        ),
        migrations.AddIndex(
            model_name='teacherattendance',
            index=models.Index(fields=['teacher', 'login_time'], name='idx_teacher_att_teacher_login'),
        ),
        migrations.AddIndex(
            model_name='teacherattendance',
            index=models.Index(fields=['login_time'], name='idx_teacher_att_login_time'),
        ),
        migrations.AddIndex(
            model_name='teacherattendance',
            index=models.Index(fields=['course_group'], name='idx_teacher_att_course_group'),
        ),
    ]