from django.contrib.auth import get_user_model
from repositorio.postgres_repository.models import (
    Teacher, CourseGroup, AcademicPeriod, Horario, Laboratory
)

User = get_user_model()

# 1. Ubicar al profesor por su correo
u = User.objects.get(email="esarmientoca@unsa.edu.pe")  # cambia el correo si hace falta
teacher = u.teacher
print("Profesor:", teacher.id, teacher.user.get_full_name())

# 2. Ver período académico activo (es el mismo que usa ServicioHorario)
periodo_activo = AcademicPeriod.objects.filter(is_active=True).first()
print("Periodo activo:", periodo_activo)

# 3. Ver TODOS los CourseGroup del profesor en el período activo
course_groups = (
    CourseGroup.objects
    .filter(teacher=teacher, academic_period=periodo_activo)
    .select_related('course')
    .prefetch_related('horarios')
)

print("\n=== COURSE GROUPS DEL PROFESOR (PERIODO ACTIVO) ===")
for cg in course_groups:
    print(
        f"- cg_id={cg.id} | {cg.course.code} {cg.course.name} | "
        f"Grupo={cg.group_code} | horarios={cg.horarios.count()}"
    )
    for h in cg.horarios.all():
        aula_codigo = h.aula.codigo if h.aula else None
        print(f"    · {h.dia_semana} {h.hora_inicio}-{h.hora_fin} | Aula={aula_codigo}")
