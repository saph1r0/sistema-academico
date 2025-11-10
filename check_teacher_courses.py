#!/usr/bin/env python3
"""
Script para verificar y asignar cursos a profesores
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import (
    User, Teacher, Course, CourseGroup, AcademicPeriod, Enrollment, Student
)

def check_teacher_data():
    """Verificar datos de profesores y cursos"""
    print("🔍 Verificando datos de profesores...")
    
    # Buscar profesores
    teachers = Teacher.objects.select_related('user').all()
    print(f"📊 Total de profesores: {teachers.count()}")
    
    for teacher in teachers:
        print(f"\n👨‍🏫 Profesor: {teacher.user.get_full_name()}")
        print(f"   - Email: {teacher.user.email}")
        print(f"   - Código: {teacher.employee_code}")
        print(f"   - Departamento: {teacher.department}")
        
        # Verificar cursos asignados
        courses = CourseGroup.objects.filter(teacher=teacher).select_related('course', 'academic_period')
        print(f"   - Cursos asignados: {courses.count()}")
        
        for course in courses:
            print(f"     * {course.course.name} ({course.course.code}) - Grupo {course.group_code}")
            print(f"       Período: {course.academic_period.name}")
            print(f"       Progreso: {course.course_progress_percentage}%")
            
            # Contar estudiantes matriculados
            enrolled = Enrollment.objects.filter(course_group=course, status='active').count()
            print(f"       Estudiantes: {enrolled}")

def check_available_courses():
    """Verificar cursos disponibles sin profesor"""
    print("\n🔍 Verificando cursos sin profesor asignado...")
    
    unassigned_courses = CourseGroup.objects.filter(teacher__isnull=True).select_related('course', 'academic_period')
    print(f"📊 Cursos sin profesor: {unassigned_courses.count()}")
    
    for course in unassigned_courses:
        print(f"   - {course.course.name} ({course.course.code}) - Grupo {course.group_code}")
        print(f"     Período: {course.academic_period.name}")
        print(f"     Capacidad: {course.capacity}")

def assign_course_to_yessenia():
    """Asignar un curso a Yessenia si no tiene ninguno"""
    print("\n🎯 Verificando asignación de cursos para Yessenia...")
    
    try:
        # Buscar a Yessenia
        yessenia_user = User.objects.filter(first_name__icontains='Yessenia').first()
        if not yessenia_user:
            print("❌ No se encontró usuario Yessenia")
            return False
        
        print(f"✅ Usuario encontrado: {yessenia_user.get_full_name()}")
        
        # Verificar si es profesor
        try:
            teacher = yessenia_user.teacher
            print(f"✅ Profesor encontrado: {teacher.employee_code}")
        except:
            print("❌ El usuario no tiene perfil de profesor")
            return False
        
        # Verificar cursos asignados
        assigned_courses = CourseGroup.objects.filter(teacher=teacher).count()
        print(f"📊 Cursos ya asignados: {assigned_courses}")
        
        if assigned_courses == 0:
            print("🔧 Asignando curso a Yessenia...")
            
            # Buscar un curso sin profesor
            available_course = CourseGroup.objects.filter(teacher__isnull=True).first()
            
            if available_course:
                available_course.teacher = teacher
                available_course.save()
                
                print(f"✅ Curso asignado: {available_course.course.name} - Grupo {available_course.group_code}")
                
                # Crear algunos estudiantes matriculados si no existen
                create_sample_enrollments(available_course)
                
                return True
            else:
                print("❌ No hay cursos disponibles para asignar")
                # Crear un curso de ejemplo
                return create_sample_course_for_yessenia(teacher)
        else:
            print("✅ Yessenia ya tiene cursos asignados")
            return True
            
    except Exception as e:
        print(f"❌ Error asignando curso: {str(e)}")
        return False

def create_sample_course_for_yessenia(teacher):
    """Crear un curso de ejemplo para Yessenia"""
    print("🔧 Creando curso de ejemplo para Yessenia...")
    
    try:
        # Verificar si existe el período académico
        period = AcademicPeriod.objects.filter(is_active=True).first()
        if not period:
            period = AcademicPeriod.objects.create(
                name='2024-II',
                start_date='2024-08-01',
                end_date='2024-12-15',
                is_active=True
            )
            print(f"✅ Período académico creado: {period.name}")
        
        # Verificar si existe el curso
        course = Course.objects.filter(code='MAT101').first()
        if not course:
            course = Course.objects.create(
                code='MAT101',
                name='Matemática Aplicada a la Computación',
                credits=4,
                description='Curso de matemática aplicada para estudiantes de computación'
            )
            print(f"✅ Curso creado: {course.name}")
        
        # Crear grupo de curso
        course_group = CourseGroup.objects.create(
            course=course,
            teacher=teacher,
            academic_period=period,
            group_code='A',
            capacity=30,
            enrolled_students=0,
            total_planned_classes=68,
            classes_attended_by_teacher=15,
            course_progress_percentage=22.1,
            classroom='Aula 301'
        )
        
        print(f"✅ Grupo de curso creado: {course_group}")
        
        # Crear estudiantes matriculados
        create_sample_enrollments(course_group)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando curso: {str(e)}")
        return False

def create_sample_enrollments(course_group):
    """Crear matrículas de ejemplo"""
    print("🔧 Creando estudiantes matriculados...")
    
    try:
        # Verificar si ya hay estudiantes matriculados
        existing_enrollments = Enrollment.objects.filter(course_group=course_group).count()
        if existing_enrollments > 0:
            print(f"✅ Ya existen {existing_enrollments} estudiantes matriculados")
            return
        
        # Buscar estudiantes existentes
        students = Student.objects.select_related('user').all()[:10]  # Tomar los primeros 10
        
        if students.count() == 0:
            print("❌ No hay estudiantes en el sistema")
            return
        
        enrolled_count = 0
        for student in students:
            # Verificar que no esté ya matriculado
            if not Enrollment.objects.filter(
                student=student, 
                course_group=course_group
            ).exists():
                Enrollment.objects.create(
                    student=student,
                    course_group=course_group,
                    academic_period=course_group.academic_period,
                    status='active'
                )
                enrolled_count += 1
        
        # Actualizar el contador en el curso
        course_group.enrolled_students = enrolled_count
        course_group.save()
        
        print(f"✅ {enrolled_count} estudiantes matriculados en el curso")
        
    except Exception as e:
        print(f"❌ Error creando matrículas: {str(e)}")

def main():
    """Función principal"""
    print("🚀 Verificando y configurando datos de profesores...")
    print("=" * 60)
    
    # Verificar datos actuales
    check_teacher_data()
    check_available_courses()
    
    # Asignar curso a Yessenia si es necesario
    success = assign_course_to_yessenia()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡Configuración completada exitosamente!")
        print("\n📋 Verificación final:")
        check_teacher_data()
    else:
        print("❌ Hubo problemas en la configuración")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)