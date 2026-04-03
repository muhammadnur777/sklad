from django import template

register = template.Library()


@register.filter
def space_number(value):
    try:
        num = int(value)
        formatted = f'{num:,}'.replace(',', ' ')
        return formatted
    except (ValueError, TypeError):
        return value