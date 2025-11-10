#!/usr/bin/env python3
"""
Script para procesar y cargar notas desde Excel con la estructura correcta
"""
import os
import django
import pandas as pd
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def procesar_notas_excel():
    """Procesa y carga las notas desde Excel usando la estructura correcta"""
    
    archivo_excel = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
    
    if not os.path.exists(archivo_excel):
        print(f"❌ No se encuentra el archivo: {archivo_excel}")
        return False
    
    try:
        with connection.cursor() as cursor:
            print("🔍 Obteniendo configuración del sistema...")
            
            # Obtener tipos de evaluación
            cursor.execute("""
                SELECT et.id, et.name 
                FROM evaluation_types et
                JOIN course_groups cg ON et.course_group_id = cg.id
                ORDER BY et.name;
            """)
            evaluation_types = {row[1]: row[0] for row in cursor.fetchall()}
            
            if 'Parcial 1' not in evaluation_types:
                print("❌ No se encontró el tipo de evaluación 'Parcial 1'")
                return False
            
            parcial1_id = evaluation_types['Parcial 1']
            print(f"✅ Parcial 1 ID: {parcial1_id}")
            
            # Obtener user_id del profesor
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
            teacher_id = teacher_result[0]
            user_id = teacher_result[1]
            teacher_name = f"{teacher_result[2]} {teacher_result[3]}"
            print(f"✅ Profesor: {teacher_name} (User ID: {user_id})")
            
            # Leer Excel con header en fila 9
            print(f"📖 Leyendo archivo Excel...")
            df = pd.read_excel(archivo_excel, header=9)
            
            print(f"📊 Datos leídos: {len(df)} filas")
            print(f"📋 Columnas: {list(df.columns)}")
            
            # Verificar que tenemos las columnas correctas
            if 'CUI' not in df.columns or 'P1' not in df.columns:
                print("❌ No se encontraron las columnas esperadas (CUI, P1)")
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
                    
                    student_id = student_result[0]
                    student_code = student_result[1]
                    
                    # Verificar si ya existe la nota
                    cursor.execute("""
                        SELECT COUNT(*) FROM grades 
                        WHERE student_id = %s AND evaluation_type_id = %s;
                    """, [student_id, parcial1_id])
                    
                    if cursor.fetchone()[0] > 0:
                        print(f"⚠️  Nota ya existe para {student_code}")
                        continue
                    
                    # Insertar nota
                    cursor.execute("""
                        INSERT INTO grades (student_id, evaluation_type_id, score, recorded_by)
                        VALUES (%s, %s, %s, %s);
                    """, [student_id, parcial1_id, nota_float, user_id])
                    
                    notas_cargadas += 1
                    print(f"✅ {student_code}: {nota_float}")
                    
                except Exception as e:
                    print(f"❌ Error en fila {index + 1}: {str(e)}")
                    errores += 1
            
            # Mostrar resumen
            print(f"\n📊 Resumen de carga:")
            print(f"  ✅ Notas cargadas: {notas_cargadas}")
            print(f"  ❌ Errores: {errores}")
            print(f"  📋 Total procesado: {len(df)} filas")
            
            if estudiantes_no_encontrados:
                print(f"  ⚠️  Estudiantes no encontrados ({len(estudiantes_no_encontrados)}):")
                for cui in estudiantes_no_encontrados[:10]:  # Mostrar solo los primeros 10
                    print(f"    - {cui}")
                if len(estudiantes_no_encontrados) > 10:
                    print(f"    ... y {len(estudiantes_no_encontrados) - 10} más")
            
            # Verificar carga final
            cursor.execute("SELECT COUNT(*) FROM grades WHERE evaluation_type_id = %s;", [parcial1_id])
            total_notas = cursor.fetchone()[0]
            print(f"  📊 Total notas en BD: {total_notas}")
            
            # Mostrar estadísticas de las notas cargadas
            if total_notas > 0:
                cursor.execute("""
                    SELECT MIN(score), MAX(score), AVG(score), COUNT(*)
                    FROM grades 
                    WHERE evaluation_type_id = %s;
                """, [parcial1_id])
                
                stats = cursor.fetchone()
                print(f"\n📈 Estadísticas de Parcial 1:")
                print(f"  📊 Cantidad: {stats[3]}")
                print(f"  📉 Mínima: {stats[0]:.1f}")
                print(f"  📈 Máxima: {stats[1]:.1f}")
                print(f"  📊 Promedio: {stats[2]:.2f}")
            
            return notas_cargadas > 0
            
    except Exception as e:
        print(f"❌ Error al procesar notas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📚 Procesando notas desde Excel...")
    print("=" * 50)
    
    if procesar_notas_excel():
        print("\n🎉 Notas procesadas exitosamente!")
    else:
        print("\n❌ Error al procesar notas")