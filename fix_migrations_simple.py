#!/usr/bin/env python3
"""
Script simple para arreglar las migraciones
"""
import subprocess
import sys

def run_command(cmd):
    """Ejecuta un comando y muestra el resultado"""
    print(f"🔧 Ejecutando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.stdout:
            print("📤 Salida:")
            print(result.stdout)
            
        if result.stderr:
            print("⚠️ Errores:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def main():
    print("🔧 Arreglando migraciones...")
    
    # Intentar marcar la migración problemática como aplicada
    commands_to_try = [
        [sys.executable, 'manage.py', 'migrate', 'postgres_repository', '0011', '--fake'],
        [sys.executable, 'manage.py', 'migrate', '--fake-initial'],
        [sys.executable, 'manage.py', 'migrate']
    ]
    
    for cmd in commands_to_try:
        print(f"\n📝 Intentando: {' '.join(cmd)}")
        if run_command(cmd):
            print("✅ Comando ejecutado exitosamente")
            break
        else:
            print("❌ Comando falló, intentando siguiente...")
    
    # Verificar estado final
    print("\n📊 Estado final de migraciones:")
    run_command([sys.executable, 'manage.py', 'showmigrations'])

if __name__ == "__main__":
    main()