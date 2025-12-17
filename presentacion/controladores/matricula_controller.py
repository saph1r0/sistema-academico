# presentacion/controladores/matricula_controller.py 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser 
from rest_framework.permissions import AllowAny 
import os

from django.core.exceptions import ObjectDoesNotExist 
from servicios.servicioMatriculaLaboratorio import ServicioMatriculaLaboratorio
from repositorio.postgres_repository.estudiantePostgresRepository import EstudiantePostgresRepository 
from presentacion.serializadores import EstudianteSerializer 
from presentacion.permisos import IsSecretariaOrAdmin


class MatriculaAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsSecretariaOrAdmin]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = EstudiantePostgresRepository() 
        self.servicio_matricula = ServicioMatriculaLaboratorio(repo=self.repo)
    # -----------------------------------------------------------
    # Tarea 1: POST /api/matriculas/upload_excel/
    # -----------------------------------------------------------
    def post(self, request, format=None):
        """Endpoint para subir y procesar el archivo de matrícula (.xlsx)."""
        if 'file' not in request.data:
            return Response(
                {"ok": False, "error": "Debe adjuntar un archivo con la clave 'file'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        archivo_subido = request.data['file']
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        ruta_temporal = os.path.join(temp_dir, archivo_subido.name)

        try:
            with open(ruta_temporal, 'wb+') as destination:
                for chunk in archivo_subido.chunks():
                    destination.write(chunk)
            
            estudiantes_cargados = self.servicio_matricula.procesar_lista_matricula(
                archivo_excel=ruta_temporal,
                periodo_id="2025-I" # Placeholder
            )
            
            return Response({
                "ok": True, 
                "mensaje": "Archivo procesado y estudiantes guardados con éxito.",
                "insertados": len(estudiantes_cargados),
                "errores": [] 
            }, status=status.HTTP_201_CREATED)

        except (ValueError, ObjectDoesNotExist) as e:
            return Response(
                {"ok": False, "error": f"Error de datos/validación: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
           return Response(
                {"ok": False, "error": f"Error interno del servidor al procesar el archivo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal) 

    # -----------------------------------------------------------
    # Tarea 2: GET /api/matriculas/
    # -----------------------------------------------------------
    def get(self, request, format=None):
        """Endpoint para listar todos los estudiantes."""
        try:
            estado_filtro = request.query_params.get('estado')
            
            estudiantes_dominio = self.repo.listar_todos(estado=estado_filtro)
            serializer = EstudianteSerializer(estudiantes_dominio, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error al obtener la lista de estudiantes: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )