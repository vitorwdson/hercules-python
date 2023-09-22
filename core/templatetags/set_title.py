from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag()
def set_title(title: str):
    return mark_safe(
        f'<script>document.title = "{title} - Hercules";</script>'
    )