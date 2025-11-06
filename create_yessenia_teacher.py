#!/usr/bin/env python
"""
Script para crear el usuario Yessenia como profesora y asignarle un curso
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod, 
    Student, Enrollment
)
from django.db import transaction

def create_yessenia_teacher():
    """Crear usuario Yessenia como profesora"""
    print("🔧 Creando usuario Yessenia como profesora...")
    
    try:
        with transaction.atomic():
            # Crear o actualizar usuario Yessenia
            yessenia_user, created = User.objects.get_or_create(
                institutional_email='yessenia@unsa.edu.pe',
                defaults={
                    'first_name': 'Yessenia',
                    'last_name': 'Docente',
                    'role': 'teacher',
                    'is_active': True,
                }
            )
            
            if created:
                yessenia_user.set_password('yessenia123')
                yessenia_user.save()
                print("✅ Usuario Yessenia creado: yessenia@unsa.edu.pe / yessenia123")
            else:
                # Actualizar rol si no es profesor
                if yessenia_user.role != 'teacher':
                    yessenia_user.role = 'teacher'
                    yessenia_user.save()
                    print("✅ Usuario Yessenia actualizado a rol de profesor")
                else:
                    print("ℹ️  Usuario Yessenia ya existe como profesor")
            
            # Crear perfil de profesor si no existe
            teacher, teacher_created = Teacher.objects.get_or_create(
                user=yessenia_user,
                defaults={
                    'teacher_code': 'YESS001',
                    'department': 'Matemáticas',
                    'specialty': 'Matemática Aplicada',
                    'hours_per_week': 20
                }
            )
            
            if teacher_created:
                print("✅ Perfil de profesor creado para Yessenia")
            else:
                print("ℹ️  Perfil de profesor ya existe para Yessenia")
            
            return teacher
            
    except Exception as e:
        print(f"❌ Error creando usuario Yessenia: {str(e)}")
        return None

def create_course_and_assign_to_yessenia(teacher):
    """Crear curso y asignarlo a Yessenia"""
    print("🔧 Creando curso para Yessenia...")
    
    try:
        with transaction.atomic():
            # Crear período académico si no existe
            period, period_created = AcademicPeriod.objects.get_or_create(
                name='2024-II',
                defaults={
                    'start_date': '2024-08-01',
                    'end_date': '2024-12-15',
                    'is_active': True
                }
            )
            
            if period_created:
                print("✅ Período académico 2024-II creado")
            else:
                print("ℹ️  Período académico 2024-II ya existe")
            
            # Crear curso si no existe
            course, course_created = Course.objects.get_or_create(
                code='MAT101',
                defaults={
                    'name': 'Matemática Aplicada a la Computación',
                    'credits': 4,
                    'description': 'Curso de matemática aplicada para estudiantes de computación'
                }
            )
            
            if course_created:
                print("✅ Curso MAT101 creado")
            else:
                print("ℹ️  Curso MAT101 ya existe")
            
            # Crear grupo de curso para Yessenia
            course_group, group_created = CourseGroup.objects.get_or_create(
                course=course,
                academic_period=period,
                group_code='A',
                defaults={
                    'teacher': teacher,
                    'capacity': 30,
                    'enrolled_students': 0,
                    'total_planned_classes': 68,
                    'classes_attended_by_teacher': 15,
                    'course_progress_percentage': 22.1,
                    'classroom': 'Aula 301'
                }
            )
            
            if group_created:
                print("✅ Grupo de curso MAT101-A creado y asignado a Yessenia")
            else:
                # Si ya existe, asignar a Yessenia si no tiene profesor
                if not course_group.teacher:
                    course_group.teacher = teacher
                    course_group.save()
                    print("✅ Grupo de curso MAT101-A asignado a Yessenia")
                else:
                    print(f"ℹ️  Grupo de curso MAT101-A ya está asignado a {course_group.teacher.user.get_full_name()}")
            
            return course_group
            
    except Exception as e:
        print(f"❌ Error creando curso: {str(e)}")
        return None

def create_sample_students_and_enrollments(course_group):
    """Crear estudiantes de ejemplo y matricularlos"""
    print("🔧 Creando estudiantes de ejemplo...")
    
    try:
        students_data = [
            {'first_name': 'Ana', 'last_name': 'García', 'code': '20241001'},
            {'first_name': 'Carlos', 'last_name': 'López', 'code': '20241002'},
            {'first_name': 'María', 'last_name': 'Rodríguez', 'code': '20241003'},
            {'first_name': 'José', 'last_name': 'Martínez', 'code': '20241004'},
            {'first_name': 'Laura', 'last_name': 'Sánchez', 'code': '20241005'},
            {'first_name': 'Diego', 'last_name': 'Torres', 'code': '20241006'},
            {'first_name': 'Sofia', 'last_name': 'Vargas', 'code': '20241007'},
            {'first_name': 'Miguel', 'last_name': 'Herrera', 'code': '20241008'},
        ]
        
        enrolled_count = 0
        
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
                    'current_cycle': 5,
                    'academic_status': 'active'
                }
            )
            
            # Matricular en el curso
            enrollment, enrollment_created = Enrollment.objects.get_or_create(
                student=student,
                course_group=course_group,
                academic_period=course_group.academic_period,
                defaults={
                    'status': 'active'
                }
            )
            
            if enrollment_created:
                enrolled_count += 1
        
        # Actualizar contador de estudiantes matriculados
        course_group.enrolled_students = enrolled_count
        course_group.save()
        
        print(f"✅ {enrolled_count} estudiantes creados y matriculados")
        return enrolled_count
        
    except Exception as e:
        print(f"❌ Error creando estudiantes: {str(e)}")
        return 0

def main():
    """Función principal"""
    print("🚀 Configurando usuario Yessenia como profesora...")
    print("=" * 60)
    
    # Crear usuario Yessenia como profesora
    teacher = create_yessenia_teacher()
    if not teacher:
        print("❌ No se pudo crear el usuario Yessenia")
        return False
    
    # Crear curso y asignarlo
    course_group = create_course_and_assign_to_yessenia(teacher)
    if not course_group:
        print("❌ No se pudo crear el curso")
        return False
    
    # Crear estudiantes de ejemplo
    enrolled_count = create_sample_students_and_enrollments(course_group)
    
    print("\n" + "=" * 60)
    print("🎉 ¡Configuración completada exitosamente!")
    print("\n📋 Resumen:")
    print(f"   👨‍🏫 Profesora: {teacher.user.get_full_name()}")
    print(f"   📚 Curso: {course_group.course.name}")
    print(f"   🏷️  Código: {course_group.course.code} - Grupo {course_group.group_code}")
    print(f"   🎓 Estudiantes matriculados: {enrolled_count}")
    print(f"   📊 Progreso actual: {course_group.course_progress_percentage}%")
    print(f"   🏫 Aula: {course_group.classroom}")
    
    print("\n🔑 Credenciales de acceso:")
    print(f"   Email: {teacher.user.institutional_email}")
    print(f"   Contraseña: yessenia123")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)