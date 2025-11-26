
from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from repositorio.postgres_repository.models import CourseGroup, TeacherAttendance
from datetime import timedelta
from datetime import date


# Mapeo de nombres de días a número de weekday() de Python
DIAS_MAP = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
}

def generar_fechas_clase(course_group):
    """
    Genera una lista de fechas de clase sin repetir por día.
    Si un curso tiene varios horarios el mismo día, se agrupan.
    """
    period = course_group.academic_period
    horarios = course_group.horarios.all()

    fechas_dict = {}  

    for h in horarios:
        
        dia_num = DIAS_MAP.get(h.dia_semana.lower())
        if dia_num is None:
            continue

        fecha = period.start_date

        while fecha.weekday() != dia_num and fecha <= period.end_date:
            fecha += timedelta(days=1)

        hoy = date.today()
        limite = min(period.end_date, hoy)

        while fecha <= limite:
            if fecha not in fechas_dict:
                fechas_dict[fecha] = []

            fechas_dict[fecha].append({
                "hora_inicio": h.hora_inicio,
                "hora_fin": h.hora_fin,
                "aula": h.aula.nombre if h.aula else "",
            })
            fecha += timedelta(days=7)

    fechas_finales = []
    for fecha, horarios_dia in fechas_dict.items():

        aulas_lista = [h["aula"] for h in horarios_dia if h["aula"]]
        aulas_unicas = list(dict.fromkeys(aulas_lista))

        aulas_final = " / ".join(aulas_unicas)

        primer = horarios_dia[0]

        fechas_finales.append({
            "fecha": fecha,
            "horarios": horarios_dia,
            "hora_inicio": primer["hora_inicio"],
            "hora_fin": primer["hora_fin"],
            "aula": aulas_final, 
        })

    fechas_finales.sort(key=lambda x: x["fecha"])
    return fechas_finales


class ProfesorAsistenciaPersonalView(LoginRequiredMixin, View):
    template_name = "profesor/mi_asistencia.html"

    def get(self, request):
        # Perfil de profesor
        teacher = request.user.teacher

        # 1) Cursos asignados al profesor
        cursos = CourseGroup.objects.filter(teacher=teacher).select_related("course", "academic_period")

        # 2) Curso seleccionado (por GET)
        curso_id = request.GET.get("curso")
        curso_seleccionado = None
        fechas_clase = []
        registros = []

        if curso_id:
            try:
                curso_seleccionado = cursos.get(id=curso_id)
            except CourseGroup.DoesNotExist:
                curso_seleccionado = None

        if curso_seleccionado:
            # 3) Todas las fechas reales de clase (según horario y periodo)
            fechas_clase = generar_fechas_clase(curso_seleccionado)

            # 4) Registros de asistencia del profesor en ese curso
            registros = TeacherAttendance.objects.filter(
                teacher=teacher,
                course_group=curso_seleccionado
            ).order_by("login_time")  # ascendente para trabajar por fecha

            # 5) Mapear registros por fecha para marcar asistió/faltó
            registros_por_fecha = {}
            for r in registros:
                fecha = r.login_time.date()
                # Si hay varios registros el mismo día, nos quedamos con el primero
                if fecha not in registros_por_fecha:
                    registros_por_fecha[fecha] = r

            # 6) Enriquecer cada fecha_clase con info de asistencia
            for f in fechas_clase:
                fecha = f["fecha"]
                registro = registros_por_fecha.get(fecha)
                if registro:
                    f["asistio"] = True
                    f["ip"] = registro.ip_address
                    f["hora_registro"] = registro.login_time.time()
                else:
                    f["asistio"] = False
                    f["ip"] = ""
                    f["hora_registro"] = None

        context = {
            "cursos": cursos,
            "curso_seleccionado": curso_seleccionado,
            "fechas_clase": fechas_clase,
        }
        return render(request, self.template_name, context)
