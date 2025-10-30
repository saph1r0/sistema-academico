#!/usr/bin/env python3
"""
Script simple para cargar notas desde Excel directamente a PostgreSQL
"""
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def cargar_notas_excel():
    """Carga notas desde Excel directamente a la base de datos"""
    
    archivo_excel = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
    
    if not os.path.exists(archivo_excel):
        print(f"❌ No se encuentra el archivo: {archivo_excel}")
        return False
    
    # Configuración de conexión
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
        
        # Obtener configuración del sistema
        print("🔧 Obteniendo configuración...")
        
        # Obtener tipos de evaluación
        cursor.execute("""
            SELECT et.id, et.name 
            FROM evaluation_types et
            JOIN course_groups cg ON et.course_group_id = cg.id
            ORDER BY et.name;
        """)
        evaluation_types = {row['name']: row['id'] for row in cursor.fetchall()}
        
        if 'Parcial 1' not in evaluation_types:
            print("❌ No se encontró el tipo de evaluación 'Parcial 1'")
            print("💡 Ejecuta setup_evaluation_types.py primero")
            return False
        
        parcial1_id = evaluation_types['Parcial 1']
        print(f"✅ Parcial 1 ID: {parcial1_id}")
        
        # Obtener user_id del profesor (usar el primero disponible)
        cursor.execute("""
            SELECT t.id, t.user_id, u.first_name, u.last_name 
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            LIMIT 1;
        """)
        teacher_result = cursor.fetchone()
        if not teacher_result:
            print("❌ No hay profesores disponibles")
            return False
        
        user_id = teacher_result['user_id']
        teacher_name = f"{teacher_result['first_name']} {teacher_result['last_name']}"
        print(f"✅ Profesor: {teacher_name} (User ID: {user_id})")
        
        # Leer Excel
        print(f"📖 Leyendo archivo Excel...")
        df = pd.read_excel(archivo_excel, header=8)  # Header en fila 9 (índice 8)
        
        print(f"📊 Datos leídos: {len(df)} filas")
        print(f"📋 Columnas: {list(df.columns)}")
        
        # Verificar columnas
        if 'CUI' not in df.columns or 'P1' not in df.columns:
            print("❌ No se encontraron las columnas esperadas (CUI, P1)")
            print(f"📋 Columnas disponibles: {list(df.columns)}")
            return False
        
        print("✅ Columnas encontradas correctamente")
        
        # Procesar notas
        print("\n📝 Procesando notas...")
        notas_cargadas = 0
        errores = 0
        estudiantes_no_encontrados = []
        
        for index, row in df.iterrows():
            try:
                cui = row['CUI']
                nota = row['P1']
                
                # Validar CUI
                if pd.isna(cui):
                    continue
                
                cui_str = str(int(cui)) if isinstance(cui, float) else str(cui)
                
                # Validar nota
                if pd.isna(nota):
                    print(f"⚠️  Fila {index + 1}: Nota vacía para CUI {cui_str}")
                    continue
                
                # Convertir nota a float
                try:
                    nota_float = float(nota)
                except (ValueError, TypeError):
                    print(f"⚠️  Fila {index + 1}: Nota inválida '{nota}' para CUI {cui_str}")
                    errores += 1
                    continue
                
                # Validar rango de nota
                if nota_float < 0 or nota_float > 20:
                    print(f"⚠️  Fila {index + 1}: Nota fuera de rango ({nota_float}) para CUI {cui_str}")
                    errores += 1
                    continue
                
                # Buscar estudiante por CUI
                cursor.execute("""
                    SELECT s.id, s.student_code
                    FROM students s 
                    WHERE s.student_code = %s;
                """, [cui_str])
                
                student_result = cursor.fetchone()
                if not student_result:
                    estudiantes_no_encontrados.append(cui_str)
                    continue
                
                student_id = student_result['id']
                student_code = student_result['student_code']
                
                # Verificar si ya existe la nota
                cursor.execute("""
                    SELECT COUNT(*) as count FROM grades 
                    WHERE student_id = %s AND evaluation_type_id = %s;
                """, [student_id, parcial1_id])
                
                if cursor.fetchone()['count'] > 0:
                    # Actualizar nota existente
                    cursor.execute("""
                        UPDATE grades 
                        SET score = %s, recorded_by = %s
                        WHERE student_id = %s AND evaluation_type_id = %s;
                    """, [nota_float, user_id, student_id, parcial1_id])
                    print(f"🔄 {student_code}: {nota_float} (actualizada)")
                else:
                    # Insertar nueva nota
                    cursor.execute("""
                        INSERT INTO grades (student_id, evaluation_type_id, score, recorded_by)
                        VALUES (%s, %s, %s, %s);
                    """, [student_id, parcial1_id, nota_float, user_id])
                    print(f"✅ {student_code}: {nota_float}")
                
                notas_cargadas += 1
                
            except Exception as e:
                print(f"❌ Error en fila {index + 1}: {str(e)}")
                errores += 1
        
        # Confirmar cambios
        conn.commit()
        
        # Mostrar resumen
        print(f"\n📊 Resumen de carga:")
        print(f"  ✅ Notas cargadas: {notas_cargadas}")
        print(f"  ❌ Errores: {errores}")
        print(f"  📋 Total procesado: {len(df)} filas")
        
        if estudiantes_no_encontrados:
            print(f"  ⚠️  Estudiantes no encontrados ({len(estudiantes_no_encontrados)}):")
            for cui in estudiantes_no_encontrados[:10]:
                print(f"    - {cui}")
            if len(estudiantes_no_encontrados) > 10:
                print(f"    ... y {len(estudiantes_no_encontrados) - 10} más")
        
        # Verificar carga final
        cursor.execute("SELECT COUNT(*) as count FROM grades WHERE evaluation_type_id = %s;", [parcial1_id])
        total_notas = cursor.fetchone()['count']
        print(f"  📊 Total notas en BD: {total_notas}")
        
        # Mostrar estadísticas
        if total_notas > 0:
            cursor.execute("""
                SELECT MIN(score) as min_score, MAX(score) as max_score, AVG(score) as avg_score, COUNT(*) as count
                FROM grades 
                WHERE evaluation_type_id = %s;
            """, [parcial1_id])
            
            stats = cursor.fetchone()
            print(f"\n📈 Estadísticas de Parcial 1:")
            print(f"  📊 Cantidad: {stats['count']}")
            print(f"  📉 Mínima: {stats['min_score']:.1f}")
            print(f"  📈 Máxima: {stats['max_score']:.1f}")
            print(f"  📊 Promedio: {stats['avg_score']:.2f}")
        
        cursor.close()
        conn.close()
        
        return notas_cargadas > 0
        
    except psycopg2.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📚 Cargando notas desde Excel...")
    print("=" * 50)
    
    if cargar_notas_simple():
        print("\n🎉 Notas cargadas exitosamente!")
        print("💡 Ahora los gráficos deberían mostrar datos reales")
    else:
        print("\n❌ Error al cargar notas")