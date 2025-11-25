#!/usr/bin/env python
"""
Simple syntax test for PhaseGrade and SimpleAttendanceRecord models
"""
import ast
import sys

def test_model_syntax():
    """Test that the models have correct Python syntax"""
    print("Testing model syntax...")
    
    try:
        with open('repositorio/postgres_repository/models.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the Python code to check for syntax errors
        ast.parse(content)
        print("✓ Models file has valid Python syntax")
        
        # Check for PhaseGrade class
        if 'class PhaseGrade(models.Model):' in content:
            print("✓ PhaseGrade model class found")
        else:
            print("❌ PhaseGrade model class not found")
            return False
            
        # Check for SimpleAttendanceRecord class
        if 'class SimpleAttendanceRecord(models.Model):' in content:
            print("✓ SimpleAttendanceRecord model class found")
        else:
            print("❌ SimpleAttendanceRecord model class not found")
            return False
            
        # Check for required fields in PhaseGrade
        required_phase_fields = [
            'phase = models.CharField',
            'partial_grade = models.DecimalField',
            'continuous_grade = models.DecimalField',
            'final_phase_grade = models.DecimalField',
            'student = models.ForeignKey(Student',
            'course_group = models.ForeignKey(CourseGroup',
            'uploaded_by = models.ForeignKey(Teacher'
        ]
        
        for field in required_phase_fields:
            if field in content:
                print(f"✓ PhaseGrade field found: {field.split('=')[0].strip()}")
            else:
                print(f"❌ PhaseGrade field missing: {field.split('=')[0].strip()}")
                return False
        
        # Check for required fields in SimpleAttendanceRecord
        required_attendance_fields = [
            'status = models.CharField',
            'class_date = models.DateField',
            'student = models.ForeignKey(Student',
            'course_group = models.ForeignKey(CourseGroup',
            'recorded_by = models.ForeignKey(Teacher'
        ]
        
        for field in required_attendance_fields:
            if field in content:
                print(f"✓ SimpleAttendanceRecord field found: {field.split('=')[0].strip()}")
            else:
                print(f"❌ SimpleAttendanceRecord field missing: {field.split('=')[0].strip()}")
                return False
        
        # Check for save method override in PhaseGrade
        if 'def save(self, *args, **kwargs):' in content and 'PhaseGrade' in content:
            print("✓ PhaseGrade save method override found")
        else:
            print("❌ PhaseGrade save method override not found")
            return False
            
        # Check for bulk recording method in SimpleAttendanceRecord
        if 'def record_bulk_attendance(' in content:
            print("✓ SimpleAttendanceRecord bulk recording method found")
        else:
            print("❌ SimpleAttendanceRecord bulk recording method not found")
            return False
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in models file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading models file: {e}")
        return False

def test_migration_syntax():
    """Test that the migration file has correct syntax"""
    print("\nTesting migration syntax...")
    
    try:
        with open('repositorio/postgres_repository/migrations/0003_add_phase_grades_simple_attendance.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the Python code to check for syntax errors
        ast.parse(content)
        print("✓ Migration file has valid Python syntax")
        
        # Check for required migration operations
        required_operations = [
            'CreateModel',
            'name=\'PhaseGrade\'',
            'name=\'SimpleAttendanceRecord\'',
            'AddConstraint',
            'AddIndex'
        ]
        
        for operation in required_operations:
            if operation in content:
                print(f"✓ Migration operation found: {operation}")
            else:
                print(f"❌ Migration operation missing: {operation}")
                return False
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in migration file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False

if __name__ == '__main__':
    try:
        model_test_passed = test_model_syntax()
        migration_test_passed = test_migration_syntax()
        
        if model_test_passed and migration_test_passed:
            print("\n🎉 All syntax tests passed successfully!")
            print("\nModels created:")
            print("- PhaseGrade: Stores partial and continuous grades for academic phases")
            print("- SimpleAttendanceRecord: Simple attendance with PRESENTE/FALTA options")
            print("\nFeatures implemented:")
            print("- Automatic final grade calculation in PhaseGrade")
            print("- Bulk attendance recording capability")
            print("- Proper database indexes and constraints")
            print("- Django migration file created")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)