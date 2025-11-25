#!/usr/bin/env python
"""
Script para crear la tabla course_topic_contents manualmente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from repositorio.postgres_repository.models import CourseTopicContent

def create_course_topic_content_table():
    """Crea la tabla course_topic_contents en la base de datos"""
    print("=== Creando tabla course_topic_contents ===")
    
    cursor = connection.cursor()
    
    try:
        # Verificar si la tabla ya existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'course_topic_contents'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ La tabla course_topic_contents ya existe")
            return True
        
        # Crear la tabla
        create_table_sql = """
        CREATE TABLE course_topic_contents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            course_group_id UUID NOT NULL,
            topic_title VARCHAR(200) NOT NULL,
            topic_description TEXT DEFAULT '',
            topic_order INTEGER NOT NULL,
            percentage_weight FLOAT NOT NULL,
            is_completed BOOLEAN DEFAULT FALSE,
            completion_date TIMESTAMP WITH TIME ZONE NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT fk_course_topic_content_course_group 
                FOREIGN KEY (course_group_id) 
                REFERENCES course_groups(id) 
                ON DELETE CASCADE,
            
            CONSTRAINT unique_course_group_topic_order 
                UNIQUE (course_group_id, topic_order)
        );
        """
        
        cursor.execute(create_table_sql)
        print("✅ Tabla course_topic_contents creada")
        
        # Crear índices
        indexes = [
            "CREATE INDEX idx_ctc_group ON course_topic_contents (course_group_id);",
            "CREATE INDEX idx_ctc_order ON course_topic_contents (topic_order);",
            "CREATE INDEX idx_ctc_completed ON course_topic_contents (is_completed);"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        print("✅ Índices creados")
        
        # Crear trigger para updated_at
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_course_topic_contents_updated_at 
            BEFORE UPDATE ON course_topic_contents 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        cursor.execute(trigger_sql)
        print("✅ Trigger para updated_at creado")
        
        connection.commit()
        print("\n🎉 Tabla course_topic_contents creada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear la tabla: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def test_table_creation():
    """Prueba que la tabla se creó correctamente"""
    print("\n=== Probando la tabla creada ===")
    
    try:
        # Verificar que podemos hacer consultas básicas
        cursor = connection.cursor()
        
        # Contar registros (debería ser 0)
        cursor.execute("SELECT COUNT(*) FROM course_topic_contents;")
        count = cursor.fetchone()[0]
        print(f"✅ Tabla accesible, registros: {count}")
        
        # Verificar estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'course_topic_contents'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("✅ Estructura de la tabla:")
        for col_name, data_type, nullable in columns:
            print(f"   - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al probar la tabla: {e}")
        return False

if __name__ == "__main__":
    success = create_course_topic_content_table()
    if success:
        success = test_table_creation()
    
    if success:
        print("\n🎉 Creación de tabla completada exitosamente!")
    else:
        print("\n💥 Error en la creación de la tabla")
        sys.exit(1)