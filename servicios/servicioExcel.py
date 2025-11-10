"""
Servicio para procesamiento automático de archivos Excel
"""
import pandas as pd
from django.db import connection
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class ExcelGradeProcessor:
    """Procesador de archivos Excel de notas"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.results = {
            'success': False,
            'processed_count': 0,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
    
    def process_grades_file(self, file_path_or_buffer):
        """
        Procesa un archivo Excel de notas y las carga en la base de datos
        
        Args:
            file_path_or_buffer: Ruta del archivo o buffer de archivo
            
        Returns:
            dict: Resultados del procesamiento
        """
        try:
            # Leer Excel con header en fila 10 (índice 9)
            df = pd.read_excel(file_path_or_buffer, header=9)
            
            logger.info(f"Excel leído: {len(df)} filas, columnas: {list(df.columns)}")
            
            # Verificar columnas requeridas
            if 'CUI' not in df.columns:
                self.results['errors'].append("No se encontró la columna 'CUI' en el archivo")
                return self.results
            
            # Detectar columnas de notas (P1, P2, P3, etc.)
            grade_columns = [col for col in df.columns if col.startswith('P') and col[1:].isdigit()]
            
            if not grade_columns:
                self.results['errors'].append("No se encontraron columnas de notas (P1, P2, P3, etc.)")
                return self.results
            
            logger.info(f"Columnas de notas encontradas: {grade_columns}")
            
            with connection.cursor() as cursor:
                # Obtener configuración del sistema
                config = self._get_system_config(cursor)
                if not config:
                    return self.results
                
                # Procesar cada columna de notas
                for grade_col in grade_columns:
                    self._process_grade_column(cursor, df, grade_col, config)
                
                # Calcular estadísticas finales
                self._calculate_statistics(cursor, config)
                
                self.results['success'] = True
                
        except Exception as e:
            error_msg = f"Error al procesar archivo Excel: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
        
        return self.results
    
    def _get_system_config(self, cursor):
        """Obtiene la configuración necesaria del sistema"""
        try:
            # Obtener tipos de evaluación
            cursor.execute("""
                SELECT et.id, et.name, cg.id as course_group_id
                FROM evaluation_types et
                JOIN course_groups cg ON et.course_group_id = cg.id
                ORDER BY et.name;
            """)
            
            evaluation_types = {}
            course_group_id = None
            
            for row in cursor.fetchall():
                eval_id, eval_name, cg_id = row
                evaluation_types[eval_name] = eval_id
                course_group_id = cg_id
            
            if not evaluation_types:
                self.results['errors'].append("No se encontraron tipos de evaluación configurados")
                return None
            
            return {
                'evaluation_types': evaluation_types,
                'course_group_id': course_group_id
            }
            
        except Exception as e:
            self.results['errors'].append(f"Error obteniendo configuración: {str(e)}")
            return None
    
    def _process_grade_column(self, cursor, df, grade_col, config):
        """Procesa una columna específica de notas"""
        try:
            # Mapear columna a tipo de evaluación
            eval_name_map = {
                'P1': 'Parcial 1',
                'P2': 'Parcial 2', 
                'P3': 'Parcial 3',
                'EF': 'Examen Final',
                'EP': 'Examen Parcial'
            }
            
            eval_name = eval_name_map.get(grade_col)
            if not eval_name or eval_name not in config['evaluation_types']:
                self.results['warnings'].append(f"Tipo de evaluación '{grade_col}' no reconocido o no configurado")
                return
            
            eval_type_id = config['evaluation_types'][eval_name]
            processed_in_column = 0
            
            logger.info(f"Procesando columna {grade_col} -> {eval_name} (ID: {eval_type_id})")
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    cui = row['CUI']
                    nota = row[grade_col]
                    
                    # Validar CUI
                    if pd.isna(cui):
                        continue
                    
                    cui_str = str(int(cui)) if isinstance(cui, float) else str(cui)
                    
                    # Validar nota
                    if pd.isna(nota):
                        continue
                    
                    # Convertir nota a float
                    try:
                        nota_float = float(nota)
                    except (ValueError, TypeError):
                        self.results['warnings'].append(f"Nota inválida '{nota}' para CUI {cui_str} en {grade_col}")
                        continue
                    
                    # Validar rango de nota
                    if nota_float < 0 or nota_float > 20:
                        self.results['warnings'].append(f"Nota fuera de rango ({nota_float}) para CUI {cui_str} en {grade_col}")
                        continue
                    
                    # Buscar estudiante
                    cursor.execute("""
                        SELECT s.id FROM students s 
                        WHERE s.student_code = %s;
                    """, [cui_str])
                    
                    student_result = cursor.fetchone()
                    if not student_result:
                        self.results['warnings'].append(f"Estudiante con CUI {cui_str} no encontrado")
                        continue
                    
                    student_id = student_result[0]
                    
                    # Verificar si ya existe la nota
                    cursor.execute("""
                        SELECT COUNT(*) FROM grades 
                        WHERE student_id = %s AND evaluation_type_id = %s;
                    """, [student_id, eval_type_id])
                    
                    if cursor.fetchone()[0] > 0:
                        # Actualizar nota existente
                        cursor.execute("""
                            UPDATE grades 
                            SET score = %s, recorded_by = %s
                            WHERE student_id = %s AND evaluation_type_id = %s;
                        """, [nota_float, self.user_id, student_id, eval_type_id])
                        logger.info(f"Actualizada nota {cui_str}: {nota_float} en {eval_name}")
                    else:
                        # Insertar nueva nota
                        cursor.execute("""
                            INSERT INTO grades (student_id, evaluation_type_id, score, recorded_by)
                            VALUES (%s, %s, %s, %s);
                        """, [student_id, eval_type_id, nota_float, self.user_id])
                        logger.info(f"Insertada nota {cui_str}: {nota_float} en {eval_name}")
                    
                    processed_in_column += 1
                    
                except Exception as e:
                    self.results['warnings'].append(f"Error procesando fila {index + 1} en {grade_col}: {str(e)}")
            
            self.results['processed_count'] += processed_in_column
            logger.info(f"Procesadas {processed_in_column} notas en columna {grade_col}")
            
        except Exception as e:
            self.results['errors'].append(f"Error procesando columna {grade_col}: {str(e)}")
    
    def _calculate_statistics(self, cursor, config):
        """Calcula estadísticas finales del procesamiento"""
        try:
            # Obtener estadísticas por tipo de evaluación
            stats_by_eval = {}
            
            for eval_name, eval_id in config['evaluation_types'].items():
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        AVG(score) as average,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        COUNT(CASE WHEN score >= 10.5 THEN 1 END) as passed
                    FROM grades 
                    WHERE evaluation_type_id = %s;
                """, [eval_id])
                
                result = cursor.fetchone()
                if result and result[0] > 0:
                    total, average, min_score, max_score, passed = result
                    stats_by_eval[eval_name] = {
                        'total': total,
                        'average': round(float(average), 2) if average else 0,
                        'min_score': float(min_score) if min_score else 0,
                        'max_score': float(max_score) if max_score else 0,
                        'passed': passed,
                        'pass_rate': round((passed / total * 100), 1) if total > 0 else 0
                    }
            
            self.results['statistics'] = stats_by_eval
            
        except Exception as e:
            self.results['warnings'].append(f"Error calculando estadísticas: {str(e)}")


class ExcelSyllabusProcessor:
    """Procesador de archivos Excel de sílabo"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.results = {
            'success': False,
            'course_assigned': False,
            'course_info': {},
            'errors': [],
            'warnings': []
        }
    
    def process_syllabus_file(self, file_path_or_buffer):
        """
        Procesa un archivo Excel de sílabo y asigna automáticamente el curso
        
        Args:
            file_path_or_buffer: Ruta del archivo o buffer de archivo
            
        Returns:
            dict: Resultados del procesamiento
        """
        try:
            # Leer las primeras filas para extraer información del curso
            df_header = pd.read_excel(file_path_or_buffer, nrows=10)
            
            # Extraer información del curso desde las primeras filas
            course_info = self._extract_course_info(df_header)
            
            if course_info:
                # Asignar curso al profesor
                self._assign_course_to_teacher(course_info)
                self.results['success'] = True
            else:
                self.results['errors'].append("No se pudo extraer información del curso del sílabo")
                
        except Exception as e:
            error_msg = f"Error al procesar sílabo: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
        
        return self.results
    
    def _extract_course_info(self, df):
        """Extrae información del curso desde el DataFrame del sílabo"""
        try:
            course_info = {}
            
            # Buscar información en las primeras filas
            for index, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col]).strip() if pd.notna(row[col]) else ""
                    
                    # Buscar nombre del curso
                    if "CURSO" in cell_value.upper() or "ASIGNATURA" in cell_value.upper():
                        # El nombre del curso podría estar en la siguiente celda o en la misma
                        if ":" in cell_value:
                            course_info['name'] = cell_value.split(":", 1)[1].strip()
                        else:
                            # Buscar en celdas adyacentes
                            for next_col in df.columns:
                                if next_col != col:
                                    next_value = str(row[next_col]).strip() if pd.notna(row[next_col]) else ""
                                    if next_value and len(next_value) > 5:
                                        course_info['name'] = next_value
                                        break
                    
                    # Buscar código del curso
                    if "CÓDIGO" in cell_value.upper() or "CODIGO" in cell_value.upper():
                        if ":" in cell_value:
                            course_info['code'] = cell_value.split(":", 1)[1].strip()
                        else:
                            # Buscar en celdas adyacentes
                            for next_col in df.columns:
                                if next_col != col:
                                    next_value = str(row[next_col]).strip() if pd.notna(row[next_col]) else ""
                                    if next_value and next_value.isdigit():
                                        course_info['code'] = next_value
                                        break
            
            return course_info if course_info else None
            
        except Exception as e:
            logger.error(f"Error extrayendo información del curso: {str(e)}")
            return None
    
    def _assign_course_to_teacher(self, course_info):
        """Asigna el curso al profesor actual"""
        try:
            with connection.cursor() as cursor:
                # Verificar si el curso ya existe
                cursor.execute("""
                    SELECT id FROM courses 
                    WHERE name ILIKE %s OR code = %s;
                """, [f"%{course_info.get('name', '')}%", course_info.get('code', '')])
                
                course_result = cursor.fetchone()
                
                if course_result:
                    course_id = course_result[0]
                    self.results['course_info'] = {
                        'id': course_id,
                        'name': course_info.get('name', ''),
                        'code': course_info.get('code', ''),
                        'assigned': True
                    }
                    self.results['course_assigned'] = True
                else:
                    self.results['warnings'].append("Curso no encontrado en el sistema")
                    
        except Exception as e:
            self.results['errors'].append(f"Error asignando curso: {str(e)}")