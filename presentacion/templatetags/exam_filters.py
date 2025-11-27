from django import template

register = template.Library()

@register.filter
def filter_by_exam(accreditations, exam_number):
    """Filtra acreditaciones por número de parcial."""
    try:
        exam_number = int(exam_number)
    except:
        return []
    return [acc for acc in accreditations if getattr(acc, "exam_number", None) == exam_number]


@register.filter
def mul(value, arg):
    """Multiplica dos valores: {{ value|mul:arg }}"""
    try:
        return int(value) * int(arg)
    except:
        return 0


@register.filter
def unique_courses(accreditations):
    unique = set()

    for acc in accreditations:

        # Diccionario
        if isinstance(acc, dict):
            course = acc.get("course_group") or acc.get("course")
            if isinstance(course, dict):
                key = course.get("id")
            else:
                key = course
        else:
            # Objeto del modelo
            course = getattr(acc, "course_group", None)
            key = getattr(course, "id", None)

        if key:
            unique.add(key)

    return list(unique)

@register.filter
def unique_teachers(accreditations):
    unique = set()

    for acc in accreditations:
        if isinstance(acc, dict):
            teacher = acc.get("teacher")
            if isinstance(teacher, dict):
                key = teacher.get("id")
            else:
                key = teacher
        else:
            teacher = getattr(acc, "teacher", None)
            key = getattr(teacher, "id", None)

        if key:
            unique.add(key)

    return list(unique)


@register.filter
def unique_groups(accreditations):
    """Devuelve grupos de curso únicos."""
    seen = set()
    unique = []
    for acc in accreditations:
        group = getattr(acc, "course_group", None)
        if group and group.id not in seen:
            seen.add(group.id)
            unique.append(group)
    return unique
