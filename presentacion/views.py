from django.shortcuts import render
from django.http import HttpResponse
from repositorio.memoria_repository.estudianteRepositorioMemoria import EstudianteRepositorioMemoria
from servicios.servicioMatricula import ServicioMatricula
from django.contrib.auth.decorators import login_required
from repositorio.postgres_repository.models import Enrollment



# inicializamos el repositorio en memoria
repo = EstudianteRepositorioMemoria()
servicio = ServicioMatricula(repo)

def index(request):
    estudiantes = repo.listar()
    return render(request, "index.html", {"estudiantes": estudiantes})

def cargar(request):
    if request.method == "POST":
        file = request.FILES["file"]
        servicio.procesar_lista_matricula(file, periodo_id=2025)
        return HttpResponse("Archivo cargado con éxito. <a href='/'>Ver lista</a>")
    return HttpResponse("Método no permitido", status=405)

@login_required
def cursos(request):
    student = request.user.student
    enrollments = Enrollment.objects.filter(student=student).select_related(
        "course_group__course", "academic_period"
    )
    return render(request, "estudiante/cursos.html", {"enrollments": enrollments})

