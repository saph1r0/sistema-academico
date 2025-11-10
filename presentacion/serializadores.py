# presentacion/serializadores.py

from rest_framework import serializers

class EstudianteSerializer(serializers.Serializer):
    """
    Serializador para convertir la entidad de dominio Estudiante (que usas en el repositorio) 
    a un formato JSON estándar para la API.
    """
    codigo = serializers.CharField()
    apellidos = serializers.CharField()
    nombres = serializers.CharField()
    correo = serializers.EmailField(source='correo_institucional')
    estado = serializers.CharField()
    