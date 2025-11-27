#!/usr/bin/env python3
"""
Script simple para verificar datos en la base de datos usando psycopg2 directamente
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def check_database():
    """Verifica datos en la base de datos"""
    
    # Configuración de conexión (ajustar según tu configuración)
    conn_params = {
        'host': 'localhost',
        'database': 'sistema_academico',
        'user': 'postgres',
        'password': 'postgres',
        'port': 5432
    }
    
    try:
        print("🔍 Conectando a la base de datos...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ Conexión exitosa")
        print("=" * 50)
        
        # Verificar estudiantes
        cursor.execute("SELECT COUNT(*) as count FROM students;")
        student_count = cursor.fetchone()['count']
        print(f"📊 Estudiantes: {student_count}")
        
        # Verificar tipos de evaluación
        cursor.execute("SELECT COUNT(*) as count FROM evaluation_types;")
        eval_count = cursor.fetchone()['count']
        print(f"📝 Tipos de evaluación: {eval_count}")
        
        if eval_count > 0:
            cursor.execute("SELECT name FROM evaluation_types ORDER BY name;")
            eval_types = cursor.fetchall()
            for eval_type in eval_types:
                print(f"  - {eval_type['name']}")
        
        # Verificar notas
        cursor.execute("SELECT COUNT(*) as count FROM grades;")
        grades_count = cursor.fetchone()['count']
        print(f"📈 Notas registradas: {grades_count}")
        
        if grades_count > 0:
            # Estadísticas básicas
            cursor.execute("""
                SELECT 
                    AVG(score) as avg_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score
                FROM grades;
            """)
            stats = cursor.fetchone()
            print(f"📊 Promedio: {stats['avg_score']:.2f}")
            print(f"📊 Rango: {stats['min_score']} - {stats['max_score']}")
            
            # Distribución por rangos
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN score BETWEEN 0 AND 5 THEN '0-5'
                        WHEN score BETWEEN 6 AND 10 THEN '6-10'
                        WHEN score BETWEEN 11 AND 15 THEN '11-15'
                        WHEN score BETWEEN 16 AND 20 THEN '16-20'
                        ELSE 'Fuera de rango'
                    END as rango,
                    COUNT(*) as cantidad
                FROM grades
                GROUP BY 
                    CASE 
                        WHEN score BETWEEN 0 AND 5 THEN '0-5'
                        WHEN score BETWEEN 6 AND 10 THEN '6-10'
                        WHEN score BETWEEN 11 AND 15 THEN '11-15'
                        WHEN score BETWEEN 16 AND 20 THEN '16-20'
                        ELSE 'Fuera de rango'
                    END
                ORDER BY rango;
            """)
            
            print("\n📈 Distribución para gráficos:")
            distribution = cursor.fetchall()
            for row in distribution:
                print(f"  {row['rango']}: {row['cantidad']} estudiantes")
        
        # Verificar course_groups
        cursor.execute("SELECT COUNT(*) as count FROM course_groups;")
        cg_count = cursor.fetchone()['count']
        print(f"\n🏫 Grupos de curso: {cg_count}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        
        # Diagnóstico
        if grades_count == 0:
            print("❌ PROBLEMA: No hay notas para generar gráficos")
            print("💡 Necesitas procesar el archivo Excel de notas")
        elif grades_count < 5:
            print("⚠️  ADVERTENCIA: Pocas notas para gráficos significativos")
        else:
            print("✅ Datos suficientes para gráficos")
        
        return grades_count > 0
        
    except psycopg2.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_database()