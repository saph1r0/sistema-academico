"""
Configuración de la aplicación de repositorios
"""
from django.apps import AppConfig


class PostgresRepositoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repositorio.postgres_repository'
    verbose_name = 'Repositorios PostgreSQL'
    