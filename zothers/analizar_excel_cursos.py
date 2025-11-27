#!/usr/bin/env python3
"""
Script para analizar la estructura de los archivos Excel de cursos
"""
import openpyxl
import os

def analizar_archivos_cursos():
    """Analiza todos los archivos Excel de cursos"""
    
    print("🔍 ANALIZANDO ARCHIVOS EXCEL DE CURSOS")
    print("=" * 60)
    
    # Obtener todos los archivos de cursos
    course_files = []
    if os.path.exists('EXELS'):
        for file in os.listdir('EXELS'):
            if file.startswith('alumnos_') and file.endswith('.xlsx'):
                course_files.append(file)
    
    print(f"📚 Archivos de cursos encontrados: {len(course_files)}")
    
    for file in course_files:
        print(f"\n" + "="*50)
        print(f"📋 ANALIZANDO: {file}")
        print("="*50)
        
        try:
            file_path = os.path.join('EXELS', file)
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
            
            print(f"📊 Dimensiones: {sheet.max_row} filas x {sheet.max_column} columnas")
            print(f"📄 Hoja: {sheet.title}")
            
            # Mostrar primeras 3 filas completas
            print(f"\n📋 PRIMERAS 3 FILAS:")
            for row in range(1, min(4, sheet.max_row + 1)):
                row_data = []
                for col in range(1, sheet.max_column + 1):
                    cell_value = sheet.cell(row=row, column=col).value
                    if cell_value is not None:
                        row_data.append(str(cell_value)[:30])  # Truncar a 30 chars
                    else:
                        row_data.append("None")
                print(f"Fila {row}: {row_data}")
            
            # Buscar emails en todo el archivo
            print(f"\n🔍 BUSCANDO EMAILS:")
            emails_found = []
            email_positions = []
            
            for row in range(1, min(sheet.max_row + 1, 50)):  # Revisar primeras 50 filas
                for col in range(1, sheet.max_column + 1):
                    cell_value = sheet.cell(row=row, column=col).value
                    
                    if cell_value and isinstance(cell_value, str) and '@' in cell_value:
                        email = cell_value.strip().lower()
                        if email not in emails_found:
                            emails_found.append(email)
                            email_positions.append(f"Fila {row}, Col {col}")
            
            print(f"📧 Total emails únicos encontrados: {len(emails_found)}")
            
            if emails_found:
                print(f"📍 Posiciones de emails:")
                for i, (email, pos) in enumerate(zip(emails_found[:5], email_positions[:5])):
                    print(f"   {pos}: {email}")
                
                if len(emails_found) > 5:
                    print(f"   ... y {len(emails_found) - 5} emails más")
            else:
                print("❌ No se encontraron emails")
                
                # Buscar patrones que podrían ser códigos de estudiante
                print(f"\n🔍 BUSCANDO CÓDIGOS DE ESTUDIANTE:")
                codes_found = []
                
                for row in range(1, min(sheet.max_row + 1, 20)):
                    for col in range(1, sheet.max_column + 1):
                        cell_value = sheet.cell(row=row, column=col).value
                        
                        if cell_value and isinstance(cell_value, (str, int, float)):
                            str_value = str(cell_value).strip()
                            # Buscar patrones como códigos de estudiante (números de 8 dígitos)
                            if str_value.isdigit() and len(str_value) == 8:
                                if str_value not in codes_found:
                                    codes_found.append(str_value)
                
                print(f"🔢 Códigos de estudiante encontrados: {len(codes_found)}")
                for code in codes_found[:5]:
                    print(f"   • {code}")
                
                if len(codes_found) > 5:
                    print(f"   ... y {len(codes_found) - 5} más")
            
            # Buscar nombres que podrían coincidir con el Excel global
            print(f"\n👤 BUSCANDO NOMBRES:")
            names_found = []
            
            for row in range(1, min(sheet.max_row + 1, 20)):
                for col in range(1, sheet.max_column + 1):
                    cell_value = sheet.cell(row=row, column=col).value
                    
                    if cell_value and isinstance(cell_value, str):
                        str_value = str(cell_value).strip()
                        # Buscar patrones de nombres (solo letras, más de 2 caracteres)
                        if str_value.isalpha() and len(str_value) > 2 and str_value.isupper():
                            if str_value not in names_found:
                                names_found.append(str_value)
            
            print(f"📝 Nombres encontrados: {len(names_found)}")
            for name in names_found[:5]:
                print(f"   • {name}")
            
            if len(names_found) > 5:
                print(f"   ... y {len(names_found) - 5} más")
                
        except Exception as e:
            print(f"❌ Error analizando {file}: {e}")

if __name__ == "__main__":
    analizar_archivos_cursos()