#!/usr/bin/env python3
"""
Script para crear la tabla de asistencia docente y configurar datos para todos los profesores
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, transaction
from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod, 
    Student, Enrollment, TeacherAttendance
)
from django.utils import timezone
from datetime import datetime, timedelta
import random

def check_and_create_teacher_attendance_table():
    """Verificar y crear la tabla de asistencia docente si no existe"""
    print("🔍 Verificando tabla teacher_attendance...")
    
    try:
        with connection.cursor() as cursor:
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'teacher_attendance'
                );
            """)
            
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("✅ Tabla teacher_attendance ya existe")
                return True
            else:
                print("🔧 Creando tabla teacher_attendance...")
                
                # Crear la tabla manualmente
                cursor.execute("""
                    CREATE TABLE teacher_attendance (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        teacher_id UUID NOT NULL,
                        course_group_id UUID,
                        login_time TIMESTAMP WITH TIME ZONE NOT NULL,
                        logout_time TIMESTAMP WITH TIME ZONE,
                        ip_address INET NOT NULL,
                        access_type VARCHAR(20) DEFAULT 'unknown',
                        user_agent TEXT DEFAULT '',
                        session_duration INTERVAL,
                        triggered_progress_update BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
                        FOREIGN KEY (course_group_id) REFERENCES course_groups(id) ON DELETE CASCADE
                    );
                """)
                
                # Crear índices
                cursor.execute("""
                    CREATE INDEX idx_teacher_att_teacher_login 
                    ON teacher_attendance(teacher_id, login_time);
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_teacher_att_login_time 
                    ON teacher_attendance(login_time);
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_teacher_att_course_group 
                    ON teacher_attendance(course_group_id);
                """)
                
                print("✅ Tabla teacher_attendance creada exitosamente")
                return True
                
    except Exception as e:
        print(f"❌ Error con tabla teacher_attendance: {str(e)}")
        return False

def create_sample_teacher_attendance():
    """Crear registros de asistencia de ejemplo para todos los profesores"""
    print("🔧 Creando registros de asistencia de ejemplo...")
    
    try:
        teachers = Teacher.objects.all()
        if not teachers.exists():
            print("❌ No hay profesores en el sistema")
            return False
        
        created_records = 0
        
        for teacher in teachers:
            # Crear registros de asistencia de los últimos 30 días
            base_date = timezone.now() - timedelta(days=30)
            
            for i in range(15):  # 15 sesiones en los últimos 30 días
                login_date = base_date + timedelta(days=i*2)
                login_time = login_date.replace(
                    hour=random.randint(7, 9),
                    minute=random.randint(0, 59),
                    second=0,
                    microsecond=0
                )
                
                # Duración de sesión entre 2 y 6 horas
                session_hours = random.randint(2, 6)
                logout_time = login_time + timedelta(hours=session_hours)
                
                # Obtener un curso del profesor si existe
                course_group = CourseGroup.objects.filter(teacher=teacher).first()
                
                attendance_record = TeacherAttendance.objects.create(
                    teacher=teacher,
                    course_group=course_group,
                    login_time=login_time,
                    logout_time=logout_time,
                    ip_address='192.168.1.100',
                    access_type='presential',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    session_duration=logout_time - login_time,
                    triggered_progress_update=random.choice([True, False])
                )
                
                created_records += 1
        
        print(f"✅ {created_records} registros de asistencia creados")
        return True
        
    except Exception as e:
        print(f"❌ Error creando registros de asistencia: {str(e)}")
        return False

def ensure_all_teachers_have_courses():
    """Asegurar que todos los profesores tengan al menos un curso asignado"""
    print("🔧 Verificando asignación de cursos a profesores...")
    
    try:
        # Obtener profesores sin cursos asignados
        teachers_without_courses = Teacher.objects.filter(
            coursegroup__isnull=True
        ).distinct()
        
        if not teachers_without_courses.exists():
            print("✅ Todos los profesores tienen cursos asignados")
            return True
        
        print(f"📊 Profesores sin cursos: {teachers_without_courses.count()}")
        
        # Crear período académico si no existe
        period, created = AcademicPeriod.objects.get_or_create(
            name='2024-II',
            defaults={
                'start_date': '2024-08-01',
                'end_date': '2024-12-15',
                'is_active': True
            }
        )
        
        # Cursos de ejemplo
        sample_courses = [
            {'code': 'MAT101', 'name': 'Matemática Aplicada a la Computación', 'credits': 4},
            {'code': 'PRG101', 'name': 'Programación I', 'credits': 4},
            {'code': 'ALG101', 'name': 'Algoritmos y Estructuras de Datos', 'credits': 4},
            {'code': 'BD101', 'name': 'Base de Datos I', 'credits': 4},
            {'code': 'ING101', 'name': 'Ingeniería de Software I', 'credits': 4},
        ]
        
        courses_assigned = 0
        
        for i, teacher in enumerate(teachers_without_courses):
            # Seleccionar curso de forma rotativa
            course_data = sample_courses[i % len(sample_courses)]
            
            # Crear curso si no existe
            course, course_created = Course.objects.get_or_create(
                code=course_data['code'],
                defaults={
                    'name': course_data['name'],
                    'credits': course_data['credits'],
                    'description': f'Curso de {course_data["name"]}'
                }
            )
            
            # Crear grupo de curso
            course_group = CourseGroup.objects.create(
                course=course,
                teacher=teacher,
                academic_period=period,
                group_code=f'{chr(65 + (i % 26))}',  # A, B, C, etc.
                capacity=30,
                enrolled_students=0,
                total_planned_classes=68,
                classes_attended_by_teacher=random.randint(10, 25),
                course_progress_percentage=random.uniform(15.0, 45.0),
                classroom=f'Aula {300 + i}'
            )
            
            print(f"  ✓ {teacher.user.get_full_name()} -> {course.name} - Grupo {course_group.group_code}")
            courses_assigned += 1
        
        print(f"✅ {courses_assigned} cursos asignados a profesores")
        return True
        
    except Exception as e:
        print(f"❌ Error asignando cursos: {str(e)}")
        return False

def create_sample_students_for_courses():
    """Crear estudiantes de ejemplo y matricularlos en los cursos"""
    print("🔧 Creando estudiantes de ejemplo...")
    
    try:
        # Verificar si ya hay estudiantes
        if Student.objects.count() >= 20:
            print("✅ Ya hay suficientes estudiantes en el sistema")
            return True
        
        # Datos de estudiantes de ejemplo
        students_data = [
            {'first_name': 'Ana', 'last_name': 'García', 'code': '20241001'},
            {'first_name': 'Carlos', 'last_name': 'López', 'code': '20241002'},
            {'first_name': 'María', 'last_name': 'Rodríguez', 'code': '20241003'},
            {'first_name': 'José', 'last_name': 'Martínez', 'code': '20241004'},
            {'first_name': 'Laura', 'last_name': 'Sánchez', 'code': '20241005'},
            {'first_name': 'Diego', 'last_name': 'Torres', 'code': '20241006'},
            {'first_name': 'Sofia', 'last_name': 'Vargas', 'code': '20241007'},
            {'first_name': 'Miguel', 'last_name': 'Herrera', 'code': '20241008'},
            {'first_name': 'Carmen', 'last_name': 'Jiménez', 'code': '20241009'},
            {'first_name': 'Roberto', 'last_name': 'Morales', 'code': '20241010'},
            {'first_name': 'Patricia', 'last_name': 'Ruiz', 'code': '20241011'},
            {'first_name': 'Fernando', 'last_name': 'Castro', 'code': '20241012'},
            {'first_name': 'Gabriela', 'last_name': 'Mendoza', 'code': '20241013'},
            {'first_name': 'Andrés', 'last_name': 'Paredes', 'code': '20241014'},
            {'first_name': 'Valeria', 'last_name': 'Ramos', 'code': '20241015'},
        ]
        
        students_created = 0
        
        for student_data in students_data:
            # Crear usuario estudiante
            student_user, user_created = User.objects.get_or_create(
                institutional_email=f"{student_data['code']}@unsa.edu.pe",
                defaults={
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name'],
                    'role': 'student',
                    'is_active': True,
                }
            )
            
            if user_created:
                student_user.set_password(student_data['code'])
                student_user.save()
            
            # Crear perfil de estudiante
            student, student_created = Student.objects.get_or_create(
                user=student_user,
                defaults={
                    'student_code': student_data['code'],
                    'career': 'Ingeniería de Sistemas',
                    'current_cycle': random.randint(3, 8),
                    'academic_status': 'active'
                }
            )
            
            if student_created:
                students_created += 1
        
        print(f"✅ {students_created} estudiantes creados")
        
        # Matricular estudiantes en cursos
        enroll_students_in_courses()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando estudiantes: {str(e)}")
        return False

def enroll_students_in_courses():
    """Matricular estudiantes en cursos disponibles"""
    print("🔧 Matriculando estudiantes en cursos...")
    
    try:
        students = list(Student.objects.all())
        course_groups = CourseGroup.objects.all()
        
        enrollments_created = 0
        
        for course_group in course_groups:
            # Matricular entre 8 y 15 estudiantes por curso
            num_students = min(random.randint(8, 15), len(students))
            selected_students = random.sample(students, num_students)
            
            for student in selected_students:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course_group=course_group,
                    academic_period=course_group.academic_period,
                    defaults={
                        'status': 'active'
                    }
                )
                
                if created:
                    enrollments_created += 1
            
            # Actualizar contador de estudiantes matriculados
            course_group.enrolled_students = num_students
            course_group.save()
        
        print(f"✅ {enrollments_created} matrículas creadas")
        return True
        
    except Exception as e:
        print(f"❌ Error matriculando estudiantes: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🚀 Configurando sistema de asistencia docente...")
    print("=" * 60)
    
    success_steps = []
    
    # Paso 1: Crear tabla de asistencia docente
    if check_and_create_teacher_attendance_table():
        success_steps.append("✅ Tabla teacher_attendance")
    else:
        success_steps.append("❌ Tabla teacher_attendance")
    
    # Paso 2: Asegurar que todos los profesores tengan cursos
    if ensure_all_teachers_have_courses():
        success_steps.append("✅ Cursos asignados a profesores")
    else:
        success_steps.append("❌ Cursos asignados a profesores")
    
    # Paso 3: Crear estudiantes y matrículas
    if create_sample_students_for_courses():
        success_steps.append("✅ Estudiantes y matrículas")
    else:
        success_steps.append("❌ Estudiantes y matrículas")
    
    # Paso 4: Crear registros de asistencia
    if create_sample_teacher_attendance():
        success_steps.append("✅ Registros de asistencia docente")
    else:
        success_steps.append("❌ Registros de asistencia docente")
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    
    for step in success_steps:
        print(f"   {step}")
    
    all_success = all("✅" in step for step in success_steps)
    
    if all_success:
        print("\n🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
        print("\n📊 Estadísticas del sistema:")
        
        try:
            teachers_count = Teacher.objects.count()
            courses_count = CourseGroup.objects.count()
            students_count = Student.objects.count()
            enrollments_count = Enrollment.objects.count()
            attendance_count = TeacherAttendance.objects.count()
            
            print(f"   👨‍🏫 Profesores: {teachers_count}")
            print(f"   📚 Grupos de cursos: {courses_count}")
            print(f"   🎓 Estudiantes: {students_count}")
            print(f"   📝 Matrículas: {enrollments_count}")
            print(f"   📊 Registros de asistencia: {attendance_count}")
            
            print("\n🚀 SISTEMA LISTO PARA USAR:")
            print("   - Todos los profesores tienen cursos asignados")
            print("   - Estudiantes matriculados en cada curso")
            print("   - Registros de asistencia docente disponibles")
            print("   - Dashboard funcionará correctamente para todos")
            
        except Exception as e:
            print(f"   ⚠️  Error obteniendo estadísticas: {str(e)}")
        
        return True
    else:
        print("\n❌ Algunos pasos fallaron. Revisar errores arriba.")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        sys.exit(1)