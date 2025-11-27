#!/usr/bin/env python
"""
Script para verificar que los nombres de índices sean válidos (≤30 caracteres)
"""

import re

def check_index_names_in_file(file_path):
    """Verifica los nombres de índices en un archivo"""
    print(f"Verificando índices en: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar patrones de índices
        index_pattern = r"name=['\"]([^'\"]+)['\"]"
        matches = re.findall(index_pattern, content)
        
        all_valid = True
        for match in matches:
            if 'idx_' in match:  # Solo verificar índices personalizados
                length = len(match)
                if length <= 30:
                    print(f"   ✓ {match} ({length} caracteres)")
                else:
                    print(f"   ✗ {match} ({length} caracteres) - DEMASIADO LARGO")
                    all_valid = False
        
        return all_valid
        
    except Exception as e:
        print(f"   ✗ Error leyendo archivo: {e}")
        return False

def main():
    print("=== VERIFICACIÓN DE NOMBRES DE ÍNDICES ===\n")
    
    files_to_check = [
        "repositorio/postgres_repository/models.py",
        "repositorio/postgres_repository/migrations/0002_enhance_teacher_attendance.py"
    ]
    
    all_files_valid = True
    
    for file_path in files_to_check:
        valid = check_index_names_in_file(file_path)
        all_files_valid = all_files_valid and valid
        print()
    
    if all_files_valid:
        print("🎉 ¡Todos los nombres de índices son válidos!")
        print("El servidor Django debería iniciarse sin errores de índices.")
    else:
        print("❌ Hay nombres de índices que exceden los 30 caracteres.")
        print("Necesitas acortar los nombres antes de ejecutar migraciones.")

if __name__ == '__main__':
    main()