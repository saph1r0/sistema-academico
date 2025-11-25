#!/usr/bin/env python
"""
Script para analizar el archivo Silabo-Mac.xlsx
"""
import pandas as pd
import os

def main():
    try:
        print('📚 Analizando archivo: Silabo-Mac.xlsx')
        
        # Verificar si el archivo existe
        if not os.path.exists('Silabo-Mac.xlsx'):
            print('❌ Archivo Silabo-Mac.xlsx no encontrado')
            return
        
        # Leer el archivo Excel
        df = pd.read_excel('Silabo-Mac.xlsx')
        
        print(f'\n=== INFORMACIÓN GENERAL ===')
        print(f'Número de filas: {len(df)}')
        print(f'Número de columnas: {len(df.columns)}')
        print(f'Columnas: {list(df.columns)}')
        
        print(f'\n=== PRIMERAS 10 FILAS ===')
        print(df.head(10))
        
        print(f'\n=== ESTRUCTURA DETALLADA ===')
        for i in range(min(15, len(df))):
            row_data = df.iloc[i].to_dict()
            print(f'Fila {i}: {row_data}')
        
        print(f'\n=== INFORMACIÓN DE TIPOS ===')
        print(df.dtypes)
        
        print(f'\n=== VALORES ÚNICOS EN COLUMNAS PRINCIPALES ===')
        for col in df.columns:
            unique_values = df[col].dropna().unique()
            if len(unique_values) <= 20:  # Solo mostrar si hay pocos valores únicos
                print(f'{col}: {unique_values}')
            else:
                print(f'{col}: {len(unique_values)} valores únicos')
        
        # Buscar información específica del sílabo
        print(f'\n=== BÚSQUEDA DE INFORMACIÓN DEL SÍLABO ===')
        
        # Buscar filas que contengan información clave
        for i, row in df.iterrows():
            row_str = ' '.join([str(val) for val in row.values if pd.notna(val)]).upper()
            
            if any(keyword in row_str for keyword in ['CURSO', 'ASIGNATURA', 'MATERIA']):
                print(f'Fila {i} (CURSO): {row.to_dict()}')
            
            if any(keyword in row_str for keyword in ['PROFESOR', 'DOCENTE', 'INSTRUCTOR']):
                print(f'Fila {i} (PROFESOR): {row.to_dict()}')
            
            if any(keyword in row_str for keyword in ['SEMANA', 'UNIDAD', 'TEMA']):
                print(f'Fila {i} (CONTENIDO): {row.to_dict()}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()