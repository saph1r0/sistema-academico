#!/usr/bin/env python3
"""
Debug script to test imports
"""

print("Testing imports...")

try:
    print("1. Importing servicios.servicioCourseMapper...")
    import servicios.servicioCourseMapper as cm
    print(f"   Module loaded: {cm}")
    print(f"   Dir: {dir(cm)}")
    
    print("2. Trying to access CourseMapper...")
    if hasattr(cm, 'CourseMapper'):
        print("   CourseMapper found!")
        CourseMapper = cm.CourseMapper
        print(f"   CourseMapper: {CourseMapper}")
    else:
        print("   CourseMapper NOT found!")
        
    print("3. Trying to access CourseMapping...")
    if hasattr(cm, 'CourseMapping'):
        print("   CourseMapping found!")
        CourseMapping = cm.CourseMapping
        print(f"   CourseMapping: {CourseMapping}")
    else:
        print("   CourseMapping NOT found!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting direct import...")
try:
    from servicios.servicioCourseMapper import CourseMapper, CourseMapping
    print("Direct import successful!")
except Exception as e:
    print(f"Direct import failed: {e}")
    import traceback
    traceback.print_exc()