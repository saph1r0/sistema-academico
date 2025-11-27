# presentacion/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Devuelve dictionary.get(key) de forma segura desde templates."""
    try:
        if dictionary is None:
            return None
        # Si es un dict real
        if hasattr(dictionary, "get"):
            return dictionary.get(key)
        # Si es un objeto con atributo
        return getattr(dictionary, key, None)
    except Exception:
        return None

register = template.Library()

