# presentacion/serializadores.py

from rest_framework import serializers

class EstudianteSerializer(serializers.Serializer):
    """
    Serializador para convertir la entidad de dominio Estudiante (que usas en el repositorio) 
    a un formato JSON estándar para la API.
    """
    # Mapea el atributo 'student_id' de la entidad Estudiante a 'codigo' en JSON
    codigo = serializers.CharField(source='codigo') 
    
    # Mapea el atributo 'apellidos' de la entidad Estudiante a 'apellidos' en JSON
    apellidos = serializers.CharField()
    
    # Mapea el atributo 'nombres' de la entidad Estudiante a 'nombres' en JSON
    nombres = serializers.CharField()
    
    # Mapea el atributo 'correo_institucional' de la entidad Estudiante a 'correo' en JSON
    correo = serializers.EmailField(source='correo_institucional')
    
    # Mapea el atributo 'estado' de la entidad Estudiante a 'estado' en JSON
    estado = serializers.CharField()
    
    # (Opcional) Puedes añadir campos solo de lectura si la entidad los tiene
    # fecha_creacion = serializers.DateTimeField(read_only=True)
    # fecha_actualizacion = serializers.DateTimeField(read_only=True)
    
    # NOTA: Asegúrate de que los campos 'apellidos', 'nombres', etc., existan en tu entidad 'Estudiante'.