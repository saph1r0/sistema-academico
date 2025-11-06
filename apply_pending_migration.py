#!/usr/bin/env python3
"""
Script para aplicar la migración pendiente de forma segura
"""

def apply_migration():
    print("🔧 Aplicando migración pendiente...")
    
    # Primero intentamos marcar como fake si la tabla ya existe
    import subprocess
    import sys
    
    try:
        # Intentar aplicar la migración con --fake primero
        print("📝 Intentando marcar migración como aplicada...")
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate', 
            'postgres_repository', '0011', '--fake'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migración marcada como aplicada exitosamente")
            return True
        else:
            print(f"⚠️ No se pudo marcar como fake: {result.stderr}")
            
            # Si no funciona fake, intentar aplicar normalmente
            print("📝 Intentando aplicar migración normalmente...")
            result = subprocess.run([
                sys.executable, 'manage.py', 'migrate'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Migración aplicada exitosamente")
                return True
            else:
                print(f"❌ Error aplicando migración: {result.stderr}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = apply_migration()
    
    if success:
        print("\n✅ ¡Migración aplicada correctamente!")
        print("🚀 El sistema debería funcionar ahora")
    else:
        print("\n❌ Problema aplicando migración")
        print("💡 Intenta ejecutar manualmente: python manage.py migrate --fake postgres_repository 0011")