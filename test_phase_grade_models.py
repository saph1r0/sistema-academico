#!/usr/bin/env python
"""
Test script to validate PhaseGrade and SimpleAttendanceRecord models
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Configure Django
django.setup()

from repositorio.postgres_repository.models import (
    PhaseGrade, SimpleAttendanceRecord, Student, CourseGroup, Teacher, User
)
from decimal import Decimal

def test_phase_grade_model():
    """Test PhaseGrade model functionality"""
    print("Testing PhaseGrade model...")
    
    # Test model creation (without saving to DB)
    phase_grade = PhaseGrade(
        phase='primera',
        partial_grade=Decimal('15.50'),
        continuous_grade=Decimal('16.00')
    )
    
    # Test automatic calculation
    calculated_grade = phase_grade.calculate_final_grade()
    expected_grade = (Decimal('15.50') + Decimal('16.00')) / 2
    
    print(f"Partial Grade: {phase_grade.partial_grade}")
    print(f"Continuous Grade: {phase_grade.continuous_grade}")
    print(f"Calculated Final Grade: {calculated_grade}")
    print(f"Expected Final Grade: {expected_grade}")
    
    assert calculated_grade == expected_grade, f"Expected {expected_grade}, got {calculated_grade}"
    print("✓ PhaseGrade calculation test passed")
    
    # Test phase choices
    valid_phases = ['primera', 'segunda', 'tercera']
    for phase in valid_phases:
        test_grade = PhaseGrade(phase=phase, partial_grade=Decimal('10.0'), continuous_grade=Decimal('12.0'))
        assert test_grade.phase in [choice[0] for choice in PhaseGrade.PHASE_CHOICES]
    print("✓ PhaseGrade phase choices test passed")

def test_simple_attendance_model():
    """Test SimpleAttendanceRecord model functionality"""
    print("\nTesting SimpleAttendanceRecord model...")
    
    # Test model creation
    attendance = SimpleAttendanceRecord(
        status='PRESENTE',
        class_date='2024-11-05'
    )
    
    print(f"Status: {attendance.status}")
    print(f"Class Date: {attendance.class_date}")
    
    # Test status choices
    valid_statuses = ['PRESENTE', 'FALTA']
    for status in valid_statuses:
        test_attendance = SimpleAttendanceRecord(status=status, class_date='2024-11-05')
        assert test_attendance.status in [choice[0] for choice in SimpleAttendanceRecord.STATUS_CHOICES]
    print("✓ SimpleAttendanceRecord status choices test passed")

def test_model_meta():
    """Test model meta information"""
    print("\nTesting model meta information...")
    
    # Test PhaseGrade meta
    assert PhaseGrade._meta.db_table == 'phase_grades'
    assert PhaseGrade._meta.verbose_name == 'Nota por Fase'
    print("✓ PhaseGrade meta information correct")
    
    # Test SimpleAttendanceRecord meta
    assert SimpleAttendanceRecord._meta.db_table == 'simple_attendance_records'
    assert SimpleAttendanceRecord._meta.verbose_name == 'Registro de Asistencia Simple'
    print("✓ SimpleAttendanceRecord meta information correct")

if __name__ == '__main__':
    try:
        test_phase_grade_model()
        test_simple_attendance_model()
        test_model_meta()
        print("\n🎉 All model tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)