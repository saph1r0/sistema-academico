"""
Servicio para mapear nombres de archivos a cursos y crear/encontrar cursos en la base de datos
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional
from django.db import transaction
from django.db import models
from repositorio.postgres_repository.models import Course

@dataclass
class CourseMapping:
    course_id: str
    course_name: str
    course_code: str
    created: bool = False

class CourseMapper:
    """
    Servicio para extraer nombres de cursos desde nombres de archivos
    y crear/encontrar cursos en la base de datos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_course_name(self, filename: str) -> str:
        """
        Extrae el nombre del curso desde el nombre del archivo
        
        Args:
            filename: Nombre del archivo (ej: alumnos_matematica_aplicada.xlsx)
            
        Returns:
            Nombre del curso limpio y formateado
        """
        # Remover extensión y prefijo 'alumnos_'
        course_name = filename.replace('.xlsx', '').replace('.xls', '')
        
        if course_name.startswith('alumnos_'):
            course_name = course_name[8:]  # Remover 'alumnos_'
        
        # Remover sufijos como (1), (2), etc.
        course_name = re.sub(r'\s*\(\d+\)\s*$', '', course_name)
        
        # Reemplazar guiones bajos con espacios
        course_name = course_name.replace('_', ' ')
        
        # Limpiar espacios extra
        course_name = ' '.join(course_name.split())
        
        # Capitalizar cada palabra
        course_name = course_name.title()
        
        # Mapeos específicos para nombres conocidos
        name_mappings = {
            'Ada': 'Análisis y Diseño de Algoritmos',
            'Isii': 'Ingeniería de Software II',
            'Mac': 'Matemática Aplicada a la Computación',
            'Trabajo Interdiciplinar Ii': 'Trabajo Interdisciplinario II',
            'Trabajo Interdiciplinar Iii': 'Trabajo Interdisciplinario III',
            'Matematica Aplicada': 'Matemática Aplicada a la Computación',
            'Programacion Web': 'Programación Web',
            'Base De Datos': 'Base de Datos',
            'Ingenieria Software': 'Ingeniería de Software'
        }
        
        # Aplicar mapeos si existe
        for key, value in name_mappings.items():
            if course_name.lower() == key.lower():
                course_name = value
                break
        
        self.logger.debug(f"Nombre de curso extraído: {filename} -> {course_name}")
        return course_name
    
    def find_or_create_course(self, course_name: str) -> CourseMapping:
        """
        Busca un curso existente o crea uno nuevo en la base de datos
        
        Args:
            course_name: Nombre del curso
            
        Returns:
            CourseMapping con información del curso
        """
        try:
            with transaction.atomic():
                # Generar código del curso basado en el nombre
                course_code = self._generate_course_code(course_name)
                
                # Buscar curso existente por nombre o código
                existing_course = Course.objects.filter(
                    models.Q(name__iexact=course_name) | 
                    models.Q(code__iexact=course_code)
                ).first()
                
                if existing_course:
                    self.logger.info(f"Curso encontrado: {existing_course.name} (ID: {existing_course.id})")
                    return CourseMapping(
                        course_id=str(existing_course.id),
                        course_name=existing_course.name,
                        course_code=existing_course.code,
                        created=False
                    )
                
                # Crear nuevo curso
                new_course = Course.objects.create(
                    name=course_name,
                    code=course_code,
                    credits=4,  # Valor por defecto
                    theory_hours=2,
                    practice_hours=2,
                    is_active=True
                )
                
                self.logger.info(f"Curso creado: {new_course.name} (ID: {new_course.id})")
                return CourseMapping(
                    course_id=str(new_course.id),
                    course_name=new_course.name,
                    course_code=new_course.code,
                    created=True
                )
                
        except Exception as e:
            error_msg = f"Error creando/buscando curso '{course_name}': {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _generate_course_code(self, course_name: str) -> str:
        """
        Genera un código de curso basado en el nombre
        
        Args:
            course_name: Nombre del curso
            
        Returns:
            Código del curso (ej: MAT101, ING201)
        """
        # Mapeos específicos para códigos conocidos
        code_mappings = {
            'Análisis y Diseño de Algoritmos': 'ADA301',
            'Ingeniería de Software II': 'IS202',
            'Matemática Aplicada a la Computación': 'MAC201',
            'Trabajo Interdisciplinario II': 'TI202',
            'Trabajo Interdisciplinario III': 'TI303',
            'Programación Web': 'PW301',
            'Base de Datos': 'BD201',
            'Ingeniería de Software': 'IS201'
        }
        
        # Usar mapeo específico si existe
        if course_name in code_mappings:
            return code_mappings[course_name]
        
        # Generar código automáticamente
        words = course_name.split()
        if len(words) >= 2:
            # Tomar primeras 2-3 letras de las primeras palabras
            code = ''.join(word[:2].upper() for word in words[:2])
        else:
            # Tomar primeras 3 letras de la única palabra
            code = words[0][:3].upper()
        
        # Agregar número por defecto
        code += '301'
        
        return code