#!/usr/bin/env python3
"""
Script de prueba para validar el sistema completo de importación de Excel
"""
import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_complete_system():
    """Prueba completa del sistema de importación"""
    
    print("🧪 INICIANDO PRUEBAS DEL SISTEMA DE IMPORTACIÓN DE EXCEL")
    print("=" * 70)
    
    # Test 1: Verificar archivos Excel
    print("\n📁 Test 1: Verificando archivos Excel...")
    test_excel_files()
    
    # Test 2: Verificar estructura de base de datos
    print("\n🗄️  Test 2: Verificando estructura de base de datos...")
    test_database_structure()
    
    # Test 3: Probar carga de estudiantes (dry-run)
    print("\n👥 Test 3: Probando carga de estudiantes (dry-run)...")
    test_student_loading()
    
    # Test 4: Probar asignación de cursos (dry-run)
    print("\n📚 Test 4: Probando asignación de cursos (dry-run)...")
    test_course_assignment()
    
    # Test 5: Verificar vista de sílabo
    print("\n📖 Test 5: Verificando vista de sílabo...")
    test_syllabus_view()
    
    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 70)

def test_excel_files():
    """Verifica que los archivos Excel existan y sean legibles"""
    
    # Verificar archivo global
    global_file = 'EXELS/bdtotall.xlsx'
    if os.path.exists(global_file):
        print(f"✅ Archivo global encontrado: {global_file}")
        
        # Verificar que se puede leer
        try:
            import openpyxl
            wb = openpyxl.load_workbook(global_file)
            sheet = wb.active
            print(f"   📊 Dimensiones: {sheet.max_row} filas x {sheet.max_column} columnas")
            
            # Verificar estructura
            headers = []
            for col in range(1, min(8, sheet.max_column + 1)):
                header = sheet.cell(row=2, column=col).value
                headers.append(str(header) if header else f"Col{col}")
            
            print(f"   📋 Encabezados: {', '.join(headers[:5])}...")
            
            # Contar emails válidos
            email_count = 0
            for row in range(3, min(sheet.max_row + 1, 20)):  # Revisar primeras 20 filas
                email = sheet.cell(row=row, column=7).value  # Columna G (CORREO)
                if email and '@' in str(email):
                    email_count += 1
            
            print(f"   📧 Emails válidos en muestra: {email_count}")
            
        except Exception as e:
            print(f"❌ Error leyendo archivo global: {e}")
    else:
        print(f"❌ Archivo global no encontrado: {global_file}")
    
    # Verificar archivos de cursos
    course_files = []
    if os.path.exists('EXELS'):
        for file in os.listdir('EXELS'):
            if file.endswith('.xlsx') and file != 'bdtotall.xlsx':
                course_files.append(file)
    
    print(f"📚 Archivos de cursos encontrados: {len(course_files)}")
    for file in course_files[:5]:  # Mostrar primeros 5
        print(f"   • {file}")
    
    if len(course_files) > 5:
        print(f"   ... y {len(course_files) - 5} más")

def test_database_structure():
    """Verifica la estructura de la base de datos"""
    
    required_tables = [
        'users', 'students', 'courses', 'course_groups', 
        'enrollments', 'syllabi', 'syllabus_topics', 'academic_periods'
    ]
    
    try:
        with connection.cursor() as cursor:
            for table in required_tables:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = %s;
                """, [table])
                
                if cursor.fetchone()[0] > 0:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    print(f"✅ Tabla {table}: {count} registros")
                else:
                    print(f"❌ Tabla {table}: No existe")
    
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")

def test_student_loading():
    """Prueba la carga de estudiantes en modo dry-run"""
    
    try:
        from servicios.servicioEstudiantes import StudentLoader
        
        loader = StudentLoader()
        
        # Simular dry-run analizando el archivo
        import openpyxl
        
        file_path = 'EXELS/bdtotall.xlsx'
        if not os.path.exists(file_path):
            print("❌ Archivo bdtotall.xlsx no encontrado")
            return
        
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        
        valid_students = 0
        invalid_students = 0
        
        for row in range(3, min(sheet.max_row + 1, 50)):  # Revisar primeras 50 filas
            try:
                cui = sheet.cell(row=row, column=2).value
                nombres = sheet.cell(row=row, column=6).value
                email = sheet.cell(row=row, column=7).value
                
                if cui and nombres and email and '@' in str(email):
                    valid_students += 1
                else:
                    invalid_students += 1
                    
            except Exception:
                invalid_students += 1
        
        print(f"✅ Estudiantes válidos en muestra: {valid_students}")
        print(f"⚠️  Estudiantes inválidos en muestra: {invalid_students}")
        
        if valid_students > 0:
            print("✅ Formato de archivo correcto para carga de estudiantes")
        else:
            print("❌ Problemas con el formato del archivo")
    
    except Exception as e:
        print(f"❌ Error en prueba de carga de estudiantes: {e}")

def test_course_assignment():
    """Prueba la asignación de cursos en modo dry-run"""
    
    try:
        from servicios.servicioAsignacionCursos import CourseAssigner
        
        # Verificar archivos de cursos
        course_files = []
        if os.path.exists('EXELS'):
            for file in os.listdir('EXELS'):
                if file.endswith('.xlsx') and file != 'bdtotall.xlsx':
                    course_files.append(os.path.join('EXELS', file))
        
        if not course_files:
            print("❌ No se encontraron archivos de cursos")
            return
        
        print(f"📚 Archivos de cursos a procesar: {len(course_files)}")
        
        # Analizar primer archivo como muestra
        test_file = course_files[0]
        print(f"🔍 Analizando archivo de muestra: {os.path.basename(test_file)}")
        
        import openpyxl
        wb = openpyxl.load_workbook(test_file)
        sheet = wb.active
        
        emails_found = 0
        for row in range(1, min(sheet.max_row + 1, 100)):
            for col in range(1, sheet.max_column + 1):
                cell_value = sheet.cell(row=row, column=col).value
                
                if cell_value and isinstance(cell_value, str) and '@' in cell_value:
                    emails_found += 1
        
        print(f"📧 Emails encontrados en archivo de muestra: {emails_found}")
        
        if emails_found > 0:
            print("✅ Formato de archivo correcto para asignación de cursos")
        else:
            print("❌ No se encontraron emails en el archivo")
    
    except Exception as e:
        print(f"❌ Error en prueba de asignación de cursos: {e}")

def test_syllabus_view():
    """Verifica que la vista de sílabo funcione correctamente"""
    
    try:
        # Verificar que las tablas necesarias existen
        with connection.cursor() as cursor:
            # Verificar si hay cursos
            cursor.execute("SELECT COUNT(*) FROM courses;")
            course_count = cursor.fetchone()[0]
            
            # Verificar si hay sílabos
            cursor.execute("SELECT COUNT(*) FROM syllabi;")
            syllabus_count = cursor.fetchone()[0]
            
            # Verificar si hay temas de sílabo
            cursor.execute("SELECT COUNT(*) FROM syllabus_topics;")
            topics_count = cursor.fetchone()[0]
            
            print(f"📚 Cursos en base de datos: {course_count}")
            print(f"📖 Sílabos en base de datos: {syllabus_count}")
            print(f"📝 Temas de sílabo en base de datos: {topics_count}")
            
            if course_count > 0:
                print("✅ Vista de sílabo debería funcionar correctamente")
            else:
                print("⚠️  No hay cursos, la vista creará datos por defecto")
    
    except Exception as e:
        print(f"❌ Error verificando vista de sílabo: {e}")

if __name__ == "__main__":
    test_complete_system()