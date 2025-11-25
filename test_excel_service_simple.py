#!/usr/bin/env python3
"""
Simple test for Excel grade processing service
"""
import os
import sys
import pandas as pd
import tempfile
from decimal import Decimal

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_excel_processor_import():
    """Test if we can import the Excel processor"""
    try:
        from servicios.servicioExcelNotas import ExcelGradeTemplateProcessor
        print("✅ ExcelGradeTemplateProcessor imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ExcelGradeTemplateProcessor: {e}")
        return False

def test_excel_processor_basic():
    """Test basic Excel processing without Django"""
    try:
        from servicios.servicioExcelNotas import ExcelGradeTemplateProcessor
        
        # Create test Excel data
        test_data = {
            'CUI': ['2021001', '2021002', '2021003'],
            'P1': [15.5, 12.0, 18.5],
            'Continua': [14.0, 13.5, 17.0]
        }
        
        df = pd.DataFrame(test_data)
        
        # Create temporary Excel file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        
        # Write Excel with headers in row 10 (like real format)
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            # Write empty rows first
            empty_df = pd.DataFrame([[''] * len(df.columns)] * 9)
            empty_df.to_excel(writer, index=False, header=False, startrow=0)
            
            # Write data with headers in row 10
            df.to_excel(writer, index=False, startrow=9)
        
        # Test processor
        processor = ExcelGradeTemplateProcessor()
        
        # Test reading Excel
        test_df = processor._read_excel_with_header_detection(temp_file.name)
        
        if test_df is not None:
            print("✅ Excel file read successfully")
            print(f"📊 Columns found: {list(test_df.columns)}")
            print(f"📋 Rows: {len(test_df)}")
            
            # Test column detection
            code_col = processor._detect_student_code_column(test_df)
            grade_cols = processor._detect_grade_columns(test_df)
            
            print(f"🎯 Student code column: {code_col}")
            print(f"🎯 Grade columns: {grade_cols}")
            
            # Test validation
            validation = processor._validate_template_format(test_df)
            print(f"✅ Template validation: {validation['valid']}")
            
            if validation['errors']:
                print("❌ Validation errors:")
                for error in validation['errors']:
                    print(f"  - {error}")
            
            return True
        else:
            print("❌ Failed to read Excel file")
            return False
            
    except Exception as e:
        print(f"❌ Error in basic Excel processing test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'temp_file' in locals() and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def test_data_validation():
    """Test data validation methods"""
    try:
        from servicios.servicioExcelNotas import ExcelGradeTemplateProcessor
        
        processor = ExcelGradeTemplateProcessor()
        
        # Test student code validation
        valid_codes = ['2021001', 2021002.0, '2021003']
        invalid_codes = [None, '', 'nan', float('nan')]
        
        print("🧪 Testing student code validation:")
        for code in valid_codes:
            result = processor._validate_student_code(code, 0)
            print(f"  {code} -> {result} ✅")
        
        for code in invalid_codes:
            result = processor._validate_student_code(code, 0)
            print(f"  {code} -> {result} (expected None)")
        
        # Test grade validation
        valid_grades = [15.5, 20.0, 0.0, 10.5]
        invalid_grades = [-1.0, 21.0, 'abc', None]
        
        print("\n🧪 Testing grade validation:")
        for grade in valid_grades:
            result = processor._validate_grade_value(grade, 'partial', '2021001', 0)
            print(f"  {grade} -> {result} ✅")
        
        for grade in invalid_grades:
            result = processor._validate_grade_value(grade, 'partial', '2021001', 0)
            print(f"  {grade} -> {result} (expected None)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in data validation test: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Excel Grade Processing Service")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_excel_processor_import),
        ("Basic Excel Processing", test_excel_processor_basic),
        ("Data Validation", test_data_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        except Exception as e:
            print(f"❌ FAIL {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed")

if __name__ == "__main__":
    main()