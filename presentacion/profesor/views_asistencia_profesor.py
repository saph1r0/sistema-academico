from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import timedelta
from datetime import date
from repositorio.postgres_repository.models import (
    CourseGroup,
    TeacherAttendance,
    Syllabus,
    SyllabusMainTopic,
    SyllabusSubTopic,
)

DIAS_MAP = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
}

DIAS_CORTOS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def generar_fechas_clase(course_group):
    
    try:
        syllabus = course_group.syllabus
    except Syllabus.DoesNotExist:
        return []

    start = syllabus.start_date
    total_weeks = syllabus.total_weeks

    horarios = course_group.horarios.all()
    dias_unicos = {} 

    for h in horarios:
        dia_num = DIAS_MAP.get(h.dia_semana.lower())
        if dia_num is None:
            continue

        if dia_num not in dias_unicos:
            dias_unicos[dia_num] = []

        dias_unicos[dia_num].append({
            "hora_inicio": h.hora_inicio,
            "hora_fin": h.hora_fin,
        })

    fechas_finales = []

    for dia_num, lista_horas in dias_unicos.items():

        fecha = start
        while fecha.weekday() != dia_num:
            fecha += timedelta(days=1)

        for _ in range(total_weeks):
            fechas_finales.append({
                "fecha": fecha,
                "hora_inicio": lista_horas[0]["hora_inicio"],
                "hora_fin": lista_horas[0]["hora_fin"],
                "horarios": lista_horas,
            })
            fecha += timedelta(days=7)

    fechas_finales.sort(key=lambda x: x["fecha"])
    return fechas_finales


def distribuir_subtemas_en_clases(subtemas, num_clases):
    
    if not subtemas:
        return [""] * num_clases

    if len(subtemas) == 1:
        return [subtemas[0]] * num_clases

    n = len(subtemas)
    base = num_clases // n
    extra = num_clases % n

    distribucion = []
    for i in range(n):
        repeticiones = base + (1 if i < extra else 0)
        distribucion.extend([subtemas[i]] * repeticiones)

    return distribucion[:num_clases]


def anotar_temas_y_subtemas(course_group, fechas_clase):
    
    try:
        syllabus = course_group.syllabus
    except Syllabus.DoesNotExist:
        for item in fechas_clase:
            item["tema"] = "Sin sílabo"
            item["subtema"] = ""
        return

    for item in fechas_clase:
        dias = (item["fecha"] - syllabus.start_date).days
        item["week"] = (dias // 7) + 1

    for item in fechas_clase:
        item["tema"] = "Tema no asignado"
        item["subtema"] = ""

    temas = syllabus.main_topics.all().order_by("order").prefetch_related("subtopics")

    for topic in temas:
        inicio, fin = topic.get_assigned_weeks()

        indices_topic = [
            idx for idx, item in enumerate(fechas_clase)
            if inicio <= item["week"] <= fin
        ]

        if not indices_topic:
            continue

        num_clases_topic = len(indices_topic)
        subtemas = [s.title for s in topic.subtopics.all().order_by("order")]

        distribucion = distribuir_subtemas_en_clases(subtemas, num_clases_topic)

        for pos, idx in enumerate(indices_topic):
            fechas_clase[idx]["tema"] = topic.title
            fechas_clase[idx]["subtema"] = distribucion[pos]


class ProfesorAsistenciaPersonalView(LoginRequiredMixin, View):
    template_name = "profesor/mi_asistencia.html"

    def get(self, request):
        teacher = request.user.teacher

        cursos = CourseGroup.objects.filter(
            teacher=teacher
        ).select_related("course", "academic_period")

        curso_id = request.GET.get("curso")
        curso_seleccionado = None
        fechas_clase = []

        if curso_id:
            try:
                curso_seleccionado = cursos.get(id=curso_id)
            except CourseGroup.DoesNotExist:
                curso_seleccionado = None

        if curso_seleccionado:
            fechas_clase_raw = generar_fechas_clase(curso_seleccionado)
            hoy = date.today()
            fechas_clase_raw = [f for f in fechas_clase_raw if f["fecha"] <= hoy]
            
            anotar_temas_y_subtemas(curso_seleccionado, fechas_clase_raw)

            registros = TeacherAttendance.objects.filter(
                teacher=teacher,
                course_group=curso_seleccionado
            )
            registros_fecha = {r.login_time.date(): r for r in registros}

            fechas_clase = []
            for item in fechas_clase_raw:
                fecha = item["fecha"]
                reg = registros_fecha.get(fecha)

                fechas_clase.append({
                    "fecha": fecha,
                    "fecha_mostrar": f"{DIAS_CORTOS[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}",
                    "tema": item.get("tema", "Tema no asignado"),
                    "subtema": item.get("subtema", ""),
                    "asistio": bool(reg),
                    "ip": reg.ip_address if reg else "—",
                })

        context = {
            "cursos": cursos,
            "curso_seleccionado": curso_seleccionado,
            "fechas_clase": fechas_clase,
        }
        return render(request, self.template_name, context)