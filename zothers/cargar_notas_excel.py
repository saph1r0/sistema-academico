#!/usr/bin/env python3
"""
Script para cargar notas desde Excel a la base de datos
"""
import os
import django
import pandas as pd
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def cargar_notas_desde_excel():
    """Carga las notas desde el archivo Excel"""
    
    archivo_excel = "Notas p1 MATEMÁTICA APLICADA A LA COMPUTACIÓN.xlsx"
    
    if not os.path.exists(archivo_excel):
        print(f"❌ No se encuentra el archivo: {archivo_excel}")
        return False
    
    try:
        with connection.cursor() as cursor:
            print("🔍 Obteniendo configuración del sistema...")
            
            # Obtener IDs necesarios
            cursor.execute("""
                SELECT et.id, et.name 
                FROM evaluation_types et
                JOIN course_groups cg ON et.course_group_id = cg.id
                ORDER BY et.name;
            """)
            evaluation_types = {row[1]: row[0] for row in cursor.fetchall()}
            
            if not evaluation_types:
                print("❌ No hay tipos de evaluación configurados")
                return False
            
            print("✅ Tipos de evaluación disponibles:")
            for nombre, id_eval in evaluation_types.items():
                print(f"  - {nombre}: {id_eval}")
            
            # Obtener profesor (recorded_by)
            cursor.execute("SELECT id FROM teachers LIMIT 1;")
            teacher_result = cursor.fetchone()
            if not teacher_result:
                print("❌ No hay profesores disponibles")
                return False
            teacher_id = teacher_result[0]
            
            print(f"✅ Profesor registrador: {teacher_id}")
            
            # Leer Excel
            print(f"📖 Leyendo archivo Excel: {archivo_excel}")
            df = pd.read_excel(archivo_excel)
            
            print(f"📊 Archivo leído: {len(df)} filas, {len(df.columns)} columnas")
            print("📋 Columnas disponibles:")
            for i, col in enumerate(df.columns):
                print(f"  {i}: {col}")
            
            # Mostrar primeras filas para análisis
            print("\n📄 Primeras 3 filas:")
            print(df.head(3).to_string())
            
            # Identificar columnas
            codigo_col = None
            parcial1_col = None
            
            # Buscar columna de código de estudiante
            for col in df.columns:
                if 'codigo' in str(col).lower() or 'código' in str(col).lower():
                    codigo_col = col
                    break
            
            # Buscar columna de Parcial 1
            for col in df.columns:
                if 'parcial' in str(col).lower() and '1' in str(col):
                    parcial1_col = col
                    break
            
            if not codigo_col:
                print("❌ No se encontró columna de código de estudiante")
                return False
                
            if not parcial1_col:
                print("❌ No se encontró columna de Parcial 1")
                return False
            
            print(f"✅ Columna código: {codigo_col}")
            print(f"✅ Columna Parcial 1: {parcial1_col}")
            
            # Procesar notas
            print("\n📝 Procesando notas...")
            notas_cargadas = 0
            errores = 0
            
            parcial1_id = evaluation_types.get('Parcial 1')
            if not parcial1_id:
                print("❌ No se encontró el tipo de evaluación 'Parcial 1'")
                return False
            
            for index, row in df.iterrows():
                try:
                    codigo_estudiante = str(row[codigo_col]).strip()
                    nota = row[parcial1_col]
                    
                    # Validar nota
                    if pd.isna(nota) or nota == '' or nota == '-':
                        print(f"⚠️  Fila {index + 1}: Nota vacía para {codigo_estudiante}")
                        continue
                    
                    # Convertir nota a float
                    try:
                        nota_float = float(nota)
                    except (ValueError, TypeError):
                        print(f"⚠️  Fila {index + 1}: Nota inválida '{nota}' para {codigo_estudiante}")
                        errores += 1
                        continue
                    
                    # Validar rango de nota
                    if nota_float < 0 or nota_float > 20:
                        print(f"⚠️  Fila {index + 1}: Nota fuera de rango ({nota_float}) para {codigo_estudiante}")
                        errores += 1
                        continue
                    
                    # Buscar estudiante
                    cursor.execute("""
                        SELECT s.id 
                        FROM students s 
                        WHERE s.student_code = %s;
                    """, [codigo_estudiante])
                    
                    student_result = cursor.fetchone()
                    if not student_result:
                        print(f"⚠️  Fila {index + 1}: Estudiante no encontrado: {codigo_estudiante}")
                        errores += 1
                        continue
                    
                    student_id = student_result[0]
                    
                    # Verificar si ya existe la nota
                    cursor.execute("""
                        SELECT COUNT(*) FROM grades 
                        WHERE student_id = %s AND evaluation_type_id = %s;
                    """, [student_id, parcial1_id])
                    
                    if cursor.fetchone()[0] > 0:
                        print(f"⚠️  Fila {index + 1}: Nota ya existe para {codigo_estudiante}")
                        continue
                    
                    # Insertar nota
                    cursor.execute("""
                        INSERT INTO grades (student_id, evaluation_type_id, score, recorded_by)
                        VALUES (%s, %s, %s, %s);
                    """, [student_id, parcial1_id, nota_float, teacher_id])
                    
                    notas_cargadas += 1
                    print(f"✅ Fila {index + 1}: {codigo_estudiante} = {nota_float}")
                    
                except Exception as e:
                    print(f"❌ Error en fila {index + 1}: {str(e)}")
                    errores += 1
            
            print(f"\n📊 Resumen de carga:")
            print(f"  ✅ Notas cargadas: {notas_cargadas}")
            print(f"  ❌ Errores: {errores}")
            print(f"  📋 Total procesado: {len(df)} filas")
            
            # Verificar carga
            cursor.execute("SELECT COUNT(*) FROM grades WHERE evaluation_type_id = %s;", [parcial1_id])
            total_notas = cursor.fetchone()[0]
            print(f"  📊 Total notas en BD: {total_notas}")
            
            return notas_cargadas > 0
            
    except Exception as e:
        print(f"❌ Error al cargar notas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("📚 Cargando notas desde Excel...")
    print("=" * 50)
    
    if cargar_notas_desde_excel():
        print("\n🎉 Notas cargadas exitosamente!")
    else:
        print("\n❌ Error al cargar notas")