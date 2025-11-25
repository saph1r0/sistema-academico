#!/usr/bin/env python3
"""
Script para verificar datos necesarios para los gráficos
"""
import os
import sys

# Añadir el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    
    from django.db import connection
    
    def verificar_datos():
        """Verifica si hay datos suficientes para generar gráficos"""
        
        print("🔍 Verificando datos para gráficos...")
        print("=" * 50)
        
        with connection.cursor() as cursor:
            # Verificar estudiantes
            cursor.execute("SELECT COUNT(*) FROM students;")
            student_count = cursor.fetchone()[0]
            print(f"📊 Estudiantes en BD: {student_count}")
            
            # Verificar tipos de evaluación
            cursor.execute("SELECT COUNT(*) FROM evaluation_types;")
            eval_types_count = cursor.fetchone()[0]
            print(f"📝 Tipos de evaluación: {eval_types_count}")
            
            if eval_types_count > 0:
                cursor.execute("SELECT id, name FROM evaluation_types ORDER BY name;")
                eval_types = cursor.fetchall()
                for eval_id, eval_name in eval_types:
                    print(f"  - {eval_name} (ID: {eval_id})")
            
            # Verificar notas
            cursor.execute("SELECT COUNT(*) FROM grades;")
            grades_count = cursor.fetchone()[0]
            print(f"📈 Notas registradas: {grades_count}")
            
            if grades_count > 0:
                # Estadísticas por tipo de evaluación
                cursor.execute("""
                    SELECT 
                        et.name,
                        COUNT(g.id) as count,
                        AVG(g.score) as avg_score,
                        MIN(g.score) as min_score,
                        MAX(g.score) as max_score
                    FROM evaluation_types et
                    LEFT JOIN grades g ON et.id = g.evaluation_type_id
                    GROUP BY et.id, et.name
                    ORDER BY et.name;
                """)
                
                print("\n📊 Estadísticas por evaluación:")
                for row in cursor.fetchall():
                    name, count, avg, min_score, max_score = row
                    if count > 0:
                        print(f"  {name}: {count} notas, promedio {avg:.2f}, rango {min_score}-{max_score}")
                    else:
                        print(f"  {name}: Sin notas registradas")
                
                # Distribución de notas para gráficos
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN g.score BETWEEN 0 AND 5 THEN '0-5'
                            WHEN g.score BETWEEN 6 AND 10 THEN '6-10'
                            WHEN g.score BETWEEN 11 AND 15 THEN '11-15'
                            WHEN g.score BETWEEN 16 AND 20 THEN '16-20'
                            ELSE 'Fuera de rango'
                        END as rango,
                        COUNT(*) as cantidad
                    FROM grades g
                    GROUP BY 
                        CASE 
                            WHEN g.score BETWEEN 0 AND 5 THEN '0-5'
                            WHEN g.score BETWEEN 6 AND 10 THEN '6-10'
                            WHEN g.score BETWEEN 11 AND 15 THEN '11-15'
                            WHEN g.score BETWEEN 16 AND 20 THEN '16-20'
                            ELSE 'Fuera de rango'
                        END
                    ORDER BY rango;
                """)
                
                print("\n📈 Distribución de notas para gráficos:")
                distribution = cursor.fetchall()
                for rango, cantidad in distribution:
                    print(f"  {rango}: {cantidad} estudiantes")
            
            # Verificar course_groups
            cursor.execute("SELECT COUNT(*) FROM course_groups;")
            course_groups_count = cursor.fetchone()[0]
            print(f"\n🏫 Grupos de curso: {course_groups_count}")
            
            # Verificar enrollments
            cursor.execute("SELECT COUNT(*) FROM enrollments;")
            enrollments_count = cursor.fetchone()[0]
            print(f"📝 Matriculaciones: {enrollments_count}")
            
            # Probar consulta de la API
            print("\n🔧 Probando consulta de API de gráficos...")
            try:
                cursor.execute("""
                    SELECT g.score
                    FROM grades g
                    JOIN evaluation_types et ON g.evaluation_type_id = et.id
                    JOIN course_groups cg ON et.course_group_id = cg.id
                    WHERE 1=1
                """)
                api_scores = [row[0] for row in cursor.fetchall()]
                print(f"✅ API query exitosa: {len(api_scores)} notas encontradas")
                
                if api_scores:
                    # Calcular distribución como lo hace la API
                    ranges = {'0-5': 0, '6-10': 0, '11-15': 0, '16-20': 0}
                    for score in api_scores:
                        score_float = float(score) if score else 0
                        if 0 <= score_float <= 5:
                            ranges['0-5'] += 1
                        elif 6 <= score_float <= 10:
                            ranges['6-10'] += 1
                        elif 11 <= score_float <= 15:
                            ranges['11-15'] += 1
                        elif 16 <= score_float <= 20:
                            ranges['16-20'] += 1
                    
                    print("📊 Distribución calculada para gráfico:")
                    for rango, cantidad in ranges.items():
                        print(f"  {rango}: {cantidad}")
                    
                    avg_score = sum(api_scores) / len(api_scores)
                    print(f"📈 Promedio general: {avg_score:.2f}")
                
            except Exception as e:
                print(f"❌ Error en consulta API: {str(e)}")
            
            print("\n" + "=" * 50)
            
            # Recomendaciones
            if grades_count == 0:
                print("⚠️  PROBLEMA: No hay notas en la base de datos")
                print("   Solución: Ejecutar el script de procesamiento de Excel")
            elif grades_count < 10:
                print("⚠️  ADVERTENCIA: Pocas notas para gráficos significativos")
            else:
                print("✅ Datos suficientes para generar gráficos")
            
            if eval_types_count == 0:
                print("⚠️  PROBLEMA: No hay tipos de evaluación configurados")
                print("   Solución: Ejecutar setup_evaluation_types.py")
            
            return grades_count > 0 and eval_types_count > 0
    
    if __name__ == "__main__":
        verificar_datos()

except ImportError as e:
    print(f"❌ Error importando Django: {e}")
    print("💡 Asegúrate de que el entorno virtual esté activado")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()