from django import template
from django.middleware.csrf import get_token
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def htmx_csrf_token(context):
    request = context['request']
    csrf_token = get_token(request)

    return format_html(
        '''hx-headers='{{"X-CSRFToken": "{}"}}' ''',
        csrf_token
    )