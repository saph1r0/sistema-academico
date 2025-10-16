# presentacion/controladores/matricula_controller.py 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import AllowAny 
import os

from django.core.exceptions import ObjectDoesNotExist
from servicios.servicioMatricula import ServicioMatricula 
from repositorio.postgres_repository.estudiantePostgresRepository import EstudiantePostgresRepository 
from presentacion.serializadores import EstudianteSerializer 

# Decorador de permisos (Asumiendo su existencia para la Tarea 3)
# from presentacion.login.permisos import solo_secretaria_o_admin 


class MatriculaAPIView(APIView):
    # Permite recibir archivos
    parser_classes = [FileUploadParser]
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = EstudiantePostgresRepository() 
        self.servicio_matricula = ServicioMatricula(repo=self.repo)

    

    # @solo_secretaria_o_admin 
    def post(self, request, format=None):
        """Endpoint para subir y procesar el archivo de matrícula (.xlsx)."""
        if 'file' not in request.data:
            return Response(
                {"ok": False, "error": "Debe adjuntar un archivo con la clave 'file'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        archivo_subido = request.data['file']
        #filename = archivo_subido.name 
        # 1. Almacenamiento Temporal
        # Mejor usar el nombre del archivo subido en lugar del parámetro filename si es una ruta limpia
        temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        ruta_temporal = os.path.join(temp_dir, archivo_subido.name)

        try:
            # Escribir el archivo
            with open(ruta_temporal, 'wb+') as destination:
                for chunk in archivo_subido.chunks():
                    destination.write(chunk)
            
            # 2. Invocar la lógica del Servicio (Dev 2)
            # Nota: Debes obtener el periodo real. Usamos un placeholder aquí.
            estudiantes_cargados = self.servicio_matricula.procesar_lista_matricula(
                archivo_excel=ruta_temporal,
                periodo_id="2025-I" 
            )
            
            # 3. Formatear la Respuesta
            return Response({
                "ok": True, 
                "mensaje": "Archivo procesado y estudiantes guardados con éxito.",
                "insertados": len(estudiantes_cargados),
                "errores": [] 
            }, status=status.HTTP_201_CREATED)

        except (ValueError, ObjectDoesNotExist) as e:
             # Manejo de errores específicos del repositorio (ej: código duplicado) o servicio (ej: validación de Excel)
            return Response(
                {"ok": False, "error": f"Error de datos/validación: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Manejo de errores generales
            return Response(
                {"ok": False, "error": f"Error interno del servidor al procesar el archivo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # 4. Limpieza
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal) 

    # -----------------------------------------------------------
    # Tarea 2: GET /api/matriculas/
    # -----------------------------------------------------------
    # @solo_secretaria_o_admin 
    def get(self, request, format=None):
        """Endpoint para listar todos los estudiantes."""
        try:
            # Usar el método listar_todos() del repositorio. 
            # Permite filtrar por estado si se pasa un query parameter (e.g., /?estado=ACTIVO)
            estado_filtro = request.query_params.get('estado')
            
            # Obtener estudiantes del repositorio (Dev 1)
            estudiantes_dominio = self.repo.listar_todos(estado=estado_filtro)

            # Serializar la lista de objetos de dominio
            serializer = EstudianteSerializer(estudiantes_dominio, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error al obtener la lista de estudiantes: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )