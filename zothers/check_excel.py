#!/usr/bin/env python
"""
Script para revisar el contenido del archivo Excel
"""
import pandas as pd

try:
    # Leer el archivo Excel
    df = pd.read_excel('alumnos_450_1703240_B_A (1).xlsx')
    
    print("=== INFORMACIÓN DEL ARCHIVO ===")
    print(f"Número de filas: {len(df)}")
    print(f"Número de columnas: {len(df.columns)}")
    print(f"Columnas: {list(df.columns)}")
    
    print("\n=== PRIMERAS 5 FILAS ===")
    print(df.head())
    
    print("\n=== DATOS DE EJEMPLO (fila 0) ===")
    if len(df) > 0:
        for i, col in enumerate(df.columns):
            print(f"Columna {i} ({col}): {df.iloc[0, i]}")
    
    print("\n=== BUSCAR FILAS CON DATOS ===")
    # Buscar filas que no estén completamente vacías
    for i in range(min(10, len(df))):
        row_data = []
        for col in df.columns:
            val = df.iloc[i][col]
            if pd.notna(val) and str(val).strip():
                row_data.append(f"{col}: {val}")
        if row_data:
            print(f"Fila {i}: {', '.join(row_data)}")

except Exception as e:
    print(f"Error: {e}")