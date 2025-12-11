from repositorio.postgres_repository.models import AcademicPeriod, CourseGroup, Student, Enrollment

PERIOD_NAME = "2025-I"
COURSE_CODE = "1705272"
GROUP_CODE = "A"

CUIS = [
    "20233590",
    "20232284",
    "20230573",
    "20213145",
    "20231537",
    "20233598",
    "20222178",
    "20222145",
    "20222179",
    "20233582",
    "20221737",
    "20230579",
    "20233589",
    "20232279",
    "20200364",
    "20232276",
    "20232282",
    "20233577",
    "20230585",
    "20220724",
    "20232274",
    "20233595",
    "20224274",
    "20230578",
    "20233583",
    "20204428",
    "20232278",
    "20213147",
    "20230580",
    "20231535",
    "20233581",
    "20222143",
    "20210680",
    "20230584",
    "20024030",
    "20231540",
    "20231533",
    "20162924",
    "20230571",
    "20233594",
    "20232285",
    "20223086",
    "20230570",
    "20233593",
    "20212163",
    "20233597",
    "20190224",
    "20224270",
    "20232277",
    "20233585",
    "20210194",
    "20230582",
    "20222142",
]


def run():
    period = AcademicPeriod.objects.get(name=PERIOD_NAME)
    grupo = CourseGroup.objects.get(
        course__code=COURSE_CODE,
        group_code=GROUP_CODE,
        academic_period=period,
    )

    print(f"Usando período: {period.name}")
    print(f"Curso: {grupo.course.code} - {grupo.course.name} (Grupo {grupo.group_code})")
    print(f"Total CUIs a procesar: {len(CUIS)}\n")

    for cui in CUIS:
        try:
            student = Student.objects.get(student_code=cui)
        except Student.DoesNotExist:
            print(f"⚠️ No existe Student con CUI: {cui}")
            continue

        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course_group=grupo,
            academic_period=period,
            defaults={
                "enrollment_type": "regular",
                "status": "active",
            },
        )

        if created:
            print(f"✅ Matriculado: {cui}")
        else:
            print(f"ℹ️ Ya estaba matriculado: {cui}")


# ⚠️ IMPORTANTE: para usar con "python manage.py shell < matricularED.py"
# NO uses if __name__ == "__main__", simplemente llama a run()
run()
