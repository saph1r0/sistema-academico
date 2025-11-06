"""
Servicio para mapear nombres de archivos a cursos en la base de datos
"""
import os
import re
import uuid
import logging
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class CourseMapping:
    """Resultado del mapeo de curso"""
    course_id: str
    course_name: str
    course_code: str
    created: bool = False
    normalized_name: str = ""


class CourseMapper:
    """
    Servicio para mapear nombres de archivos a cursos en la base de datos
    
    Extrae nombres de cursos desde nombres de archivos y los mapea a registros
    en la base de datos, creando nuevos cursos si es necesario.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Mapeo de nombres de archivos a nombres de cursos
        self.filename_mappings = {
            'alumnos_isII(1)': 'INGENIERIA DE SOFTWARE II',
            'alumnos_ada(1)': 'ANALISIS Y DISEÑO DE ALGORITMOS',
            'alumnos_mac(1)': 'MATEMATICA APLICADA A LA COMPUTACION',
            'alumnos_trabajo_interdiciplinarII (1)': 'TRABAJO INTERDISCIPLINARIO II',
            'alumnos_trabajo_interdiciplinarIII': 'TRABAJO INTERDISCIPLINARIO III'
        }
    
    def extract_course_name(self, filename: str) -> str:
        """
        Extrae el nombre del curso desde el nombre del archivo
        
        Args:
            filename: Nombre del archivo (con o sin ruta)
            
        Returns:
            Nombre del curso normalizado
        """
        self.logger.debug(f"Extrayendo nombre de curso de: {filename}")
        
        base_filename = os.path.basename(filename)
        name_without_ext = os.path.splitext(base_filename)[0]
        
        if name_without_ext in self.filename_mappings:
            course_name = self.filename_mappings[name_without_ext]
            self.logger.debug(f"Mapeo encontrado: {name_without_ext} -> {course_name}")
            return course_name
        
        course_name = self._extract_from_filename_pattern(name_without_ext)
        self.logger.debug(f"Nombre extraído: {course_name}")
        return course_name 
   
    def find_or_create_course(self, course_name: str) -> CourseMapping:
        """
        Encuentra o crea un curso en la base de datos
        
        Args:
            course_name: Nombre del curso
            
        Returns:
            CourseMapping con información del curso
        """
        # Importar Django solo cuando se necesite
        try:
            from django.db import connection, transaction
        except ImportError:
            raise RuntimeError("Django no está disponible para operaciones de base de datos")
        
        self.logger.info(f"Buscando o creando curso: {course_name}")
        
        # Normalizar nombre del curso
        normalized_name = self._normalize_course_name(course_name)
        
        try:
            with transaction.atomic():
                # Buscar curso existente
                existing_course = self._find_existing_course(normalized_name)
                if existing_course:
                    self.logger.info(f"Curso encontrado: {existing_course['name']}")
                    return CourseMapping(
                        course_id=existing_course['id'],
                        course_name=existing_course['name'],
                        course_code=existing_course['code'],
                        created=False,
                        normalized_name=normalized_name
                    )
                
                # Crear nuevo curso
                new_course = self._create_new_course(normalized_name)
                self.logger.info(f"Curso creado: {new_course['name']} ({new_course['code']})")
                
                return CourseMapping(
                    course_id=new_course['id'],
                    course_name=new_course['name'],
                    course_code=new_course['code'],
                    created=True,
                    normalized_name=normalized_name
                )
                
        except Exception as e:
            error_msg = f"Error procesando curso '{course_name}': {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _normalize_course_name(self, name: str) -> str:
        """
        Normaliza el nombre del curso para consistencia
        
        Args:
            name: Nombre del curso original
            
        Returns:
            Nombre normalizado
        """
        if not name:
            return ""
        
        normalized = name.upper().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        replacements = {
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N', 'Ü': 'U'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        normalized = normalized.replace('&', 'Y')
        normalized = normalized.replace(' DE LA ', ' DE ')
        normalized = normalized.replace(' A LA ', ' A ')
        
        return normalized.strip()
    
    def _extract_from_filename_pattern(self, filename: str) -> str:
        """
        Extrae nombre del curso usando patrones del nombre de archivo
        
        Args:
            filename: Nombre del archivo sin extensión
            
        Returns:
            Nombre del curso extraído
        """
        if filename.startswith('alumnos_'):
            course_part = filename[8:]
        else:
            course_part = filename
        
        course_name = course_part.replace('_', ' ')
        course_name = re.sub(r'\s*\(\d+\)\s*', '', course_name)
        course_name = re.sub(r'\s*\d+\s*', '', course_name)
        course_name = re.sub(r'\s+', ' ', course_name).strip()
        
        return course_name.upper() if course_name else "CURSO SIN NOMBRE"
    
    def _find_existing_course(self, normalized_name: str) -> Optional[Dict]:
        """
        Busca un curso existente en la base de datos
        
        Args:
            normalized_name: Nombre normalizado del curso
            
        Returns:
            Diccionario con datos del curso o None si no existe
        """
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, code, name FROM courses WHERE UPPER(TRIM(name)) = %s AND is_active = TRUE",
                [normalized_name]
            )
            result = cursor.fetchone()
            
            if result:
                return {'id': result[0], 'code': result[1], 'name': result[2]}
            
            words = normalized_name.split()
            if len(words) >= 2:
                pattern = '%'.join(words[:3])
                cursor.execute(
                    "SELECT id, code, name FROM courses WHERE UPPER(name) LIKE %s AND is_active = TRUE",
                    [f'%{pattern}%']
                )
                result = cursor.fetchone()
                
                if result:
                    return {'id': result[0], 'code': result[1], 'name': result[2]}
            
            return None    

    def _create_new_course(self, normalized_name: str) -> Dict:
        """
        Crea un nuevo curso en la base de datos
        
        Args:
            normalized_name: Nombre normalizado del curso
            
        Returns:
            Diccionario con datos del curso creado
        """
        from django.db import connection
        
        course_id = str(uuid.uuid4())
        course_code = self._generate_course_code(normalized_name)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO courses (
                    id, code, name, credits, theory_hours, practice_hours, 
                    is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, [course_id, course_code, normalized_name, 3, 2, 2, True])
        
        return {'id': course_id, 'code': course_code, 'name': normalized_name}
    
    def _generate_course_code(self, course_name: str) -> str:
        """
        Genera un código único para el curso
        
        Args:
            course_name: Nombre del curso
            
        Returns:
            Código único del curso
        """
        words = course_name.split()
        code_parts = []
        
        skip_words = {'DE', 'LA', 'EL', 'LOS', 'LAS', 'Y', 'A', 'EN', 'CON', 'PARA'}
        
        for word in words:
            if word not in skip_words and len(word) >= 2:
                if len(word) >= 3:
                    code_parts.append(word[:3])
                else:
                    code_parts.append(word)
                
                if len(code_parts) >= 3:
                    break
        
        if len(code_parts) < 2:
            code_parts = [word[:3] for word in words[:2] if len(word) >= 2]
        
        base_code = ''.join(code_parts).upper()
        
        if len(base_code) < 3:
            base_code = f"CUR{base_code}"
        
        return self._make_unique_code(base_code)
    
    def _make_unique_code(self, base_code: str) -> str:
        """
        Hace único un código base agregando un número
        
        Args:
            base_code: Código base
            
        Returns:
            Código único
        """
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM courses WHERE code = %s", [base_code])
            if cursor.fetchone()[0] == 0:
                return base_code
            
            for i in range(1, 100):
                test_code = f"{base_code}{i:02d}"
                cursor.execute("SELECT COUNT(*) FROM courses WHERE code = %s", [test_code])
                if cursor.fetchone()[0] == 0:
                    return test_code
        
        return f"CURSO{uuid.uuid4().hex[:6].upper()}"