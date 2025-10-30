-- Script SQL para limpiar las migraciones de Django
-- Ejecutar este script en PostgreSQL para limpiar el estado de migraciones

-- Eliminar todas las entradas de migraciones de la tabla django_migrations
DELETE FROM django_migrations WHERE app = 'postgres_repository';

-- Opcional: Eliminar todas las tablas creadas por la app (descomenta si es necesario)
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP TABLE IF EXISTS students CASCADE;
-- DROP TABLE IF EXISTS teachers CASCADE;
-- DROP TABLE IF EXISTS academic_periods CASCADE;
-- DROP TABLE IF EXISTS courses CASCADE;
-- DROP TABLE IF EXISTS course_groups CASCADE;
-- DROP TABLE IF EXISTS laboratories CASCADE;
-- DROP TABLE IF EXISTS enrollments CASCADE;
-- DROP TABLE IF EXISTS laboratory_enrollments CASCADE;
-- DROP TABLE IF EXISTS laboratorios CASCADE;
-- DROP TABLE IF EXISTS estudiantes_legacy CASCADE;
-- DROP TABLE IF EXISTS matriculas_legacy CASCADE;

-- Mostrar el estado actual de las migraciones
SELECT * FROM django_migrations WHERE app = 'postgres_repository';