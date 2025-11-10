#!/usr/bin/env python3
"""
Script para analizar la estructura del archivo Excel de notas
"""
import pandas as pd
import os

def analizar_excel():
    """Analiza la estructura del archivo Excel"""
    
    archivo_excel = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
    
    if not os.path.exists(archivo_excel):
        print(f"❌ No se encuentra el archivo: {archivo_excel}")
        return False
    
    try:
        print(f"📖 Analizando archivo: {archivo_excel}")
        print("=" * 60)
        
        # Leer las primeras 15 filas para ver la estructura
        print("🔍 Leyendo primeras 15 filas sin header...")
        df_raw = pd.read_excel(archivo_excel, header=None, nrows=15)
        
        print(f"📊 Dimensiones: {df_raw.shape[0]} filas x {df_raw.shape[1]} columnas")
        print("\n📋 Contenido de las primeras 15 filas:")
        
        for i, row in df_raw.iterrows():
            print(f"Fila {i+1:2d}: {list(row.values)}")
        
        print("\n" + "=" * 60)
        
        # Probar diferentes headers
        for header_row in range(15):
            try:
                df_test = pd.read_excel(archivo_excel, header=header_row, nrows=5)
                print(f"\n🧪 Con header en fila {header_row+1}:")
                print(f"   Columnas: {list(df_test.columns)}")
                
                # Buscar columnas que podrían ser códigos de estudiante
                possible_code_cols = []
                possible_grade_cols = []
                
                for col in df_test.columns:
                    col_str = str(col).upper()
                    if any(keyword in col_str for keyword in ['CUI', 'CODIGO', 'CODE', 'ESTUDIANTE', 'ALUMNO']):
                        possible_code_cols.append(col)
                    if any(keyword in col_str for keyword in ['P1', 'PARCIAL', 'NOTA', 'GRADE']):
                        possible_grade_cols.append(col)
                
                if possible_code_cols or possible_grade_cols:
                    print(f"   🎯 Posibles columnas de código: {possible_code_cols}")
                    print(f"   🎯 Posibles columnas de notas: {possible_grade_cols}")
                    
                    # Mostrar algunos datos de muestra
                    if not df_test.empty:
                        print(f"   📄 Muestra de datos:")
                        for idx, row in df_test.head(3).iterrows():
                            print(f"      {dict(row)}")
                
            except Exception as e:
                continue
        
        print("\n" + "=" * 60)
        print("💡 Recomendaciones:")
        print("1. Identifica qué fila contiene los headers (nombres de columnas)")
        print("2. Identifica qué columna contiene los códigos de estudiante")
        print("3. Identifica qué columna contiene las notas del Parcial 1")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al analizar archivo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analizar_excel()