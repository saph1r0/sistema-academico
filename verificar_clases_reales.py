#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar las clases reales creadas
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from repositorio.postgres_repository.models import (
    User, Teacher, Student, Course, CourseGroup, AcademicPeriod,
    Enrollment, AttendanceRecord, Grade
)


def main():
    """Verifica las clases reales creadas"""
    print("=" * 80)
    print("VERIFICANDO CLASES REALES CREADAS")
    print("=" * 80)
    
    try:
        # Verificar usuarios y profesores
        print("\n1. USUARIOS Y PROFESORES:")
        teachers = Teacher.objects.all()
        teacher_users = User.objects.filter(role='teacher')
        
        print(f"   Usuarios profesores: {teacher_users.count()}")
        print(f"   Registros de profesores: {teachers.count()}")
        
        if teachers.exists():
            print("   Primeros 5 profesores:")
            for teacher in teachers[:5]:
                print(f"     - {teacher.user.get_full_name()} ({teacher.user.institutional_email})")
        
        # Verificar estudiantes
        print("\n2. ESTUDIANTES:")
        students = Student.objects.all()
        student_users = User.objects.filter(role='student')
        
        print(f"   Usuarios estudiantes: {student_users.count()}")
        print(f"   Registros de estudiantes: {students.count()}")
        
        if students.exists():
            print("   Primeros 5 estudiantes:")
            for student in students[:5]:
                print(f"     - {student.student_code}: {student.user.get_full_name()}")
        
        # Verificar cursos y grupos
        print("\n3. CURSOS Y GRUPOS:")
        courses = Course.objects.all()
        course_groups = CourseGroup.objects.all()
        
        print(f"   Cursos: {courses.count()}")
        print(f"   Grupos de cursos: {course_groups.count()}")
        
        if course_groups.exists():
            print("   Grupos de cursos:")
            for group in course_groups:
                teacher_name = group.teacher.user.get_full_name() if group.teacher else "Sin asignar"
                print(f"     - {group.course.name} (Grupo {group.group_code})")
                print(f"       Profesor: {teacher_name}")
                print(f"       Estudiantes matriculados: {group.enrolled_students}")
        
        # Verificar matrículas
        print("\n4. MATRÍCULAS:")
        enrollments = Enrollment.objects.all()
        active_enrollments = Enrollment.objects.filter(status='active')
        
        print(f"   Total matrículas: {enrollments.count()}")
        print(f"   Matrículas activas: {active_enrollments.count()}")
        
        # Verificar asistencia
        print("\n5. REGISTROS DE ASISTENCIA:")
        attendance_records = AttendanceRecord.objects.all()
        
        print(f"   Total registros: {attendance_records.count()}")
        
        if attendance_records.exists():
            # Estadísticas por estado
            from django.db.models import Count
            stats = attendance_records.values('status').annotate(count=Count('status'))
            print("   Por estado:")
            for stat in stats:
                print(f"     - {stat['status']}: {stat['count']}")
        
        # Verificar notas
        print("\n6. NOTAS:")
        grades = Grade.objects.all()
        
        print(f"   Total notas: {grades.count()}")
        
        if grades.exists():
            # Estadísticas por tipo de examen
            from django.db.models import Count, Avg
            stats = grades.values('exam_type').annotate(
                count=Count('exam_type'),
                avg_grade=Avg('grade')
            )
            print("   Por tipo de examen:")
            for stat in stats:
                print(f"     - {stat['exam_type']}: {stat['count']} notas, promedio: {stat['avg_grade']:.2f}")
        
        # Verificar período académico
        print("\n7. PERÍODO ACADÉMICO:")
        periods = AcademicPeriod.objects.all()
        active_period = AcademicPeriod.objects.filter(is_active=True).first()
        
        print(f"   Total períodos: {periods.count()}")
        if active_period:
            print(f"   Período activo: {active_period.name}")
        
        # Resumen de clases reales
        print("\n" + "=" * 80)
        print("RESUMEN DE CLASES REALES:")
        print("=" * 80)
        
        if course_groups.exists():
            print(f"✓ {course_groups.count()} clases reales creadas")
            print(f"✓ {teachers.count()} profesores disponibles")
            print(f"✓ {active_enrollments.count()} estudiantes matriculados")
            print(f"✓ {attendance_records.count()} registros de asistencia")
            print(f"✓ {grades.count()} notas registradas")
            
            # Mostrar detalle de cada clase
            print(f"\nDETALLE DE CLASES:")
            for group in course_groups:
                enrollments_count = Enrollment.objects.filter(
                    course_group=group, 
                    status='active'
                ).count()
                
                attendance_count = AttendanceRecord.objects.filter(
                    course_group=group
                ).count()
                
                grades_count = Grade.objects.filter(
                    course=group.course
                ).count()
                
                teacher_name = group.teacher.user.get_full_name() if group.teacher else "Sin asignar"
                
                print(f"\n  📚 {group.course.name}")
                print(f"     👨‍🏫 Profesor: {teacher_name}")
                print(f"     👥 Estudiantes: {enrollments_count}")
                print(f"     📅 Asistencias: {attendance_count}")
                print(f"     📝 Notas: {grades_count}")
                print(f"     🏫 Aula: {group.classroom or 'No asignada'}")
        else:
            print("⚠️  No se encontraron clases reales creadas")
        
        print("\n" + "=" * 80)
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)