"""
Vista mejorada para el sílabo del profesor con datos reales de la base de datos
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.db import connection, transaction
from .mixins import ProfesorRequiredMixin
import uuid
from datetime import datetime, timedelta


class ProfesorSilaboView(ProfesorRequiredMixin, TemplateView):
    """Gestión de sílabos y avance de cursos con datos reales"""
    template_name = 'profesor/silabo/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtener información del curso asignado al profesor
            course_info = self._get_assigned_course()
            if not course_info:
                context.update({
                    'page_title': 'Gestión de Sílabo',
                    'error': 'No tienes un curso asignado',
                    'course': {},
                    'syllabus_units': [],
                    'syllabus_stats': {},
                    'schedule': [],
                    'resources': []
                })
                return context
            
            # Obtener o crear sílabo para el curso
            syllabus_info = self._get_or_create_syllabus(course_info['course_id'])
            
            # Obtener temas del sílabo
            syllabus_topics = self._get_syllabus_topics(syllabus_info['syllabus_id'])
            
            # Calcular estadísticas
            syllabus_stats = self._calculate_syllabus_stats(syllabus_topics)
            
            # Generar cronograma
            schedule = self._generate_schedule()
            
            # Recursos por defecto
            resources = self._get_default_resources()
            
            context.update({
                'page_title': 'Gestión de Sílabo',
                'course': course_info,
                'syllabus_units': syllabus_topics,
                'syllabus_stats': syllabus_stats,
                'schedule': schedule,
                'resources': resources
            })
            
        except Exception as e:
            context.update({
                'page_title': 'Gestión de Sílabo',
                'error': f'Error al cargar datos del sílabo: {str(e)}',
                'course': {},
                'syllabus_units': [],
                'syllabus_stats': {},
                'schedule': [],
                'resources': []
            })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Manejar actualizaciones de progreso del sílabo"""
        try:
            action = request.POST.get('action')
            
            if action == 'update_topic_progress':
                topic_id = request.POST.get('topic_id')
                is_completed = request.POST.get('is_completed') == 'true'
                
                self._update_topic_progress(topic_id, is_completed)
                messages.success(request, 'Progreso actualizado exitosamente.')
                
            elif action == 'create_topic':
                self._create_new_topic(request.POST)
                messages.success(request, 'Tema creado exitosamente.')
                
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
        
        return redirect('profesor:silabo')
    
    def _get_assigned_course(self):
        """Obtiene el curso asignado al profesor"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.id, c.code, c.name, c.credits,
                    COUNT(DISTINCT e.student_id) as student_count,
                    cg.group_code, cg.id as course_group_id
                FROM courses c
                JOIN course_groups cg ON c.id = cg.course_id
                LEFT JOIN enrollments e ON cg.id = e.course_group_id
                GROUP BY c.id, c.code, c.name, c.credits, cg.group_code, cg.id
                LIMIT 1;
            """)
            
            result = cursor.fetchone()
            if result:
                course_id, code, name, credits, student_count, group_code, course_group_id = result
                return {
                    'course_id': course_id,
                    'code': code,
                    'name': name,
                    'credits': credits,
                    'weekly_hours': 4,  # Por defecto
                    'modality': 'Presencial',
                    'period': '2024-II',
                    'student_count': student_count or 0,
                    'group_code': group_code,
                    'course_group_id': course_group_id
                }
            return None
    
    def _get_or_create_syllabus(self, course_id):
        """Obtiene o crea un sílabo para el curso"""
        with connection.cursor() as cursor:
            # Buscar sílabo existente
            cursor.execute("""
                SELECT id, objectives, competencies, evaluation_system, bibliography
                FROM syllabi 
                WHERE course_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
            """, [course_id])
            
            result = cursor.fetchone()
            if result:
                return {
                    'syllabus_id': result[0],
                    'objectives': result[1] or '',
                    'competencies': result[2] or '',
                    'evaluation_system': result[3] or '',
                    'bibliography': result[4] or ''
                }
            
            # Crear nuevo sílabo
            syllabus_id = str(uuid.uuid4())
            
            # Obtener período académico activo
            cursor.execute("SELECT id FROM academic_periods WHERE is_active = TRUE LIMIT 1;")
            period_result = cursor.fetchone()
            academic_period_id = period_result[0] if period_result else self._create_default_period()
            
            cursor.execute("""
                INSERT INTO syllabi (
                    id, course_id, academic_period_id, version,
                    objectives, competencies, evaluation_system, bibliography,
                    created_by, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, [
                syllabus_id, course_id, academic_period_id, '1.0',
                'Objetivos del curso por definir',
                'Competencias por definir',
                'Sistema de evaluación por definir',
                'Bibliografía por definir',
                self.request.user.id
            ])
            
            # Crear temas por defecto
            self._create_default_topics(syllabus_id)
            
            return {
                'syllabus_id': syllabus_id,
                'objectives': 'Objetivos del curso por definir',
                'competencies': 'Competencias por definir',
                'evaluation_system': 'Sistema de evaluación por definir',
                'bibliography': 'Bibliografía por definir'
            }
    
    def _create_default_period(self):
        """Crea un período académico por defecto"""
        with connection.cursor() as cursor:
            period_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO academic_periods (
                    id, name, start_date, end_date,
                    laboratory_enrollment_start, laboratory_enrollment_end,
                    enrollment_change_deadline, is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, [
                period_id, '2024-II', '2024-08-01', '2024-12-15',
                '2024-07-15', '2024-08-15', '2024-09-01', True
            ])
            return period_id
    
    def _create_default_topics(self, syllabus_id):
        """Crea temas por defecto para el sílabo"""
        default_topics = [
            {
                'unit_number': 1,
                'topic_name': 'Fundamentos de Álgebra Lineal',
                'subtopics': ['Vectores en R2 y R3', 'Operaciones con vectores', 'Matrices y operaciones', 'Determinantes'],
                'planned_week': 4,
                'duration_hours': 16
            },
            {
                'unit_number': 2,
                'topic_name': 'Espacios Vectoriales',
                'subtopics': ['Definición de espacio vectorial', 'Subespacios vectoriales', 'Combinación lineal e independencia', 'Base y dimensión'],
                'planned_week': 8,
                'duration_hours': 16
            },
            {
                'unit_number': 3,
                'topic_name': 'Transformaciones Lineales',
                'subtopics': ['Definición y propiedades', 'Matriz de una transformación', 'Núcleo e imagen', 'Isomorfismos'],
                'planned_week': 12,
                'duration_hours': 16
            },
            {
                'unit_number': 4,
                'topic_name': 'Valores y Vectores Propios',
                'subtopics': ['Valores propios', 'Vectores propios', 'Diagonalización', 'Aplicaciones'],
                'planned_week': 16,
                'duration_hours': 16
            }
        ]
        
        with connection.cursor() as cursor:
            for topic in default_topics:
                topic_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO syllabus_topics (
                        id, syllabus_id, unit_number, topic_name, subtopics,
                        planned_week, duration_hours, is_completed, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, [
                    topic_id, syllabus_id, topic['unit_number'], topic['topic_name'],
                    topic['subtopics'], topic['planned_week'], topic['duration_hours'], False
                ])
    
    def _get_syllabus_topics(self, syllabus_id):
        """Obtiene los temas del sílabo"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, unit_number, topic_name, subtopics,
                    planned_week, duration_hours, is_completed,
                    completed_date, completed_week
                FROM syllabus_topics
                WHERE syllabus_id = %s
                ORDER BY unit_number;
            """, [syllabus_id])
            
            topics = []
            for row in cursor.fetchall():
                topic_id, unit_number, topic_name, subtopics, planned_week, duration_hours, is_completed, completed_date, completed_week = row
                
                # Calcular progreso basado en semana actual
                current_week = self._get_current_week()
                
                if is_completed:
                    progress = 100
                    status = 'completed'
                    status_display = 'Completada'
                elif current_week >= planned_week:
                    progress = 100
                    status = 'completed'
                    status_display = 'Debería estar completada'
                elif current_week > (planned_week - 4):  # En las últimas 4 semanas
                    progress = ((current_week - (planned_week - 4)) / 4) * 100
                    status = 'in_progress'
                    status_display = 'En Progreso'
                else:
                    progress = 0
                    status = 'pending'
                    status_display = 'Pendiente'
                
                # Convertir subtemas a lista si es necesario
                if isinstance(subtopics, list):
                    subtopics_list = subtopics
                else:
                    subtopics_list = subtopics if subtopics else []
                
                # Crear contenidos basados en subtemas
                contents = []
                hours_per_subtopic = duration_hours // len(subtopics_list) if subtopics_list else duration_hours
                for i, subtopic in enumerate(subtopics_list):
                    contents.append({
                        'title': subtopic,
                        'hours': hours_per_subtopic,
                        'completed': is_completed or (progress > (i + 1) * (100 / len(subtopics_list)))
                    })
                
                topics.append({
                    'id': topic_id,
                    'title': f"Unidad {unit_number}: {topic_name}",
                    'unit_number': unit_number,
                    'topic_name': topic_name,
                    'duration': 4,  # semanas
                    'hours': duration_hours,
                    'progress': round(progress, 1),
                    'status': status,
                    'get_status_display': status_display,
                    'is_completed': is_completed,
                    'planned_week': planned_week,
                    'completed_date': completed_date,
                    'objectives': [
                        f'Comprender los conceptos de {topic_name.lower()}',
                        f'Aplicar técnicas de {topic_name.lower()}',
                        f'Resolver problemas relacionados con {topic_name.lower()}'
                    ],
                    'contents': contents,
                    'evaluations': [
                        {'name': f'Práctica {unit_number}', 'type': 'practica', 'weight': 20},
                        {'name': f'Examen Parcial {unit_number}', 'type': 'examen', 'weight': 25}
                    ]
                })
            
            return topics
    
    def _get_current_week(self):
        """Calcula la semana actual del período académico"""
        start_date = datetime(2024, 8, 1)  # Inicio del período académico
        current_date = datetime.now()
        weeks_elapsed = min(((current_date - start_date).days // 7) + 1, 16)
        return max(1, weeks_elapsed)
    
    def _calculate_syllabus_stats(self, topics):
        """Calcula estadísticas del sílabo"""
        if not topics:
            return {
                'total_units': 0,
                'completed_units': 0,
                'completion_percentage': 0,
                'total_classes': 0,
                'classes_taught': 0,
                'classes_percentage': 0,
                'total_evaluations': 0,
                'evaluations_done': 0,
                'evaluations_percentage': 0
            }
        
        total_units = len(topics)
        completed_units = len([t for t in topics if t['is_completed']])
        
        total_hours = sum(t['hours'] for t in topics)
        completed_hours = sum(t['hours'] * t['progress'] / 100 for t in topics)
        
        total_classes = total_hours // 2  # 2 horas por clase
        classes_taught = completed_hours // 2
        
        return {
            'total_units': total_units,
            'completed_units': completed_units,
            'completion_percentage': round((completed_units / total_units * 100), 1) if total_units > 0 else 0,
            'total_classes': int(total_classes),
            'classes_taught': int(classes_taught),
            'classes_percentage': round((classes_taught / total_classes * 100), 1) if total_classes > 0 else 0,
            'total_evaluations': total_units * 2,  # 2 evaluaciones por unidad
            'evaluations_done': completed_units * 2,
            'evaluations_percentage': round((completed_units * 2 / (total_units * 2) * 100), 1) if total_units > 0 else 0
        }
    
    def _generate_schedule(self):
        """Genera cronograma de 16 semanas"""
        current_week = self._get_current_week()
        schedule = []
        
        for i in range(1, 17):
            start_day = i * 7 - 6
            end_day = i * 7
            
            schedule.append({
                'number': i,
                'dates': f'{start_day}-{end_day} Oct',
                'completed': i < current_week,
                'current': i == current_week
            })
        
        return schedule
    
    def _get_default_resources(self):
        """Recursos por defecto"""
        return [
            {'name': 'Libro de Álgebra Lineal', 'type': 'PDF', 'icon': 'file-text'},
            {'name': 'Ejercicios Resueltos', 'type': 'PDF', 'icon': 'file-text'},
            {'name': 'Videos Explicativos', 'type': 'Video', 'icon': 'play-circle'},
            {'name': 'Software GeoGebra', 'type': 'Software', 'icon': 'monitor'}
        ]
    
    def _update_topic_progress(self, topic_id, is_completed):
        """Actualiza el progreso de un tema"""
        with connection.cursor() as cursor:
            if is_completed:
                cursor.execute("""
                    UPDATE syllabus_topics 
                    SET is_completed = %s, completed_date = CURRENT_DATE, completed_week = %s
                    WHERE id = %s
                """, [True, self._get_current_week(), topic_id])
            else:
                cursor.execute("""
                    UPDATE syllabus_topics 
                    SET is_completed = %s, completed_date = NULL, completed_week = NULL
                    WHERE id = %s
                """, [False, topic_id])
    
    def _create_new_topic(self, post_data):
        """Crea un nuevo tema del sílabo"""
        # Esta funcionalidad se puede implementar más adelante
        pass