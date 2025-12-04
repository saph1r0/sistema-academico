from django.views import View
from django.shortcuts import render
from repositorio.postgres_repository.models import Teacher, CourseGroup, TeacherAttendance
from datetime import date

DIAS_CORTOS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

class AdminAsistenciaProfesorView(View):
    template_name = "administrador/asistencia_profesor.html"

    def get(self, request):
        profesores = Teacher.objects.select_related("user").all().order_by("user__last_name")

        teacher_id = request.GET.get("profesor")
        course_id = request.GET.get("curso")

        cursos = []
        fechas_info = []

        porcentaje = None
        total_clases = 0 

        if teacher_id:
            cursos = CourseGroup.objects.filter(
                teacher_id=teacher_id
            ).select_related("course")

        if teacher_id and course_id:
            teacher = Teacher.objects.get(id=teacher_id)
            curso = CourseGroup.objects.get(id=course_id)

            from presentacion.profesor.views_asistencia_profesor import generar_fechas_clase, anotar_temas_y_subtemas

            fechas_clase = generar_fechas_clase(curso)
            anotar_temas_y_subtemas(curso, fechas_clase)

            # Obtener asistencias del profesor
            registros = TeacherAttendance.objects.filter(
                teacher=teacher, course_group=curso
            )
            asistencia_por_fecha = {r.login_time.date(): r for r in registros}

            asistidas = 0
            total = 0

            for item in fechas_clase:
                fecha = item["fecha"]
                
                # FILTRO PARA MOSTRAR SOLO CLASES HASTA LA FECHA DE HOY
                if fecha > date.today():
                    continue

                total += 1

                asistencia = asistencia_por_fecha.get(fecha)

                fechas_info.append({
                    "fecha_mostrar": f"{DIAS_CORTOS[fecha.weekday()]} {fecha.strftime('%d/%m/%Y')}",
                    "tema": item.get("tema", ""),
                    "subtema": item.get("subtema", ""),
                    "asistio": bool(asistencia),
                    "ip": asistencia.ip_address if asistencia else "—",
                })

                if asistencia:
                    asistidas += 1

            porcentaje = round((asistidas / total) * 100, 1) if total > 0 else 0
            total_clases = total 

        return render(request, self.template_name, {
            "profesores": profesores,
            "cursos": cursos,
            "fechas_info": fechas_info,
            "porcentaje": porcentaje,
            "total_clases": total_clases, 
        })