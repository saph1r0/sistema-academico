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

@register.filter
def dict_keys(value):
    """Obtiene las keys de un diccionario como lista"""
    return list(value.keys())

@register.filter
def dict_values(value):
    """Obtiene los values de un diccionario como lista"""
    return list(value.values())
@register.filter
def to_list(value):
    """Convierte un iterable a lista"""
    return list(value)

@register.filter
def dict_items(value):
    """Convierte dict.items() a lista de tuplas"""
    return list(value.items())