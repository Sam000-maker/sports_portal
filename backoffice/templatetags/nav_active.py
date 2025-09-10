from django import template
from django.urls import resolve

register = template.Library()

@register.simple_tag(takes_context=True)
def active(context, url_name: str, cls="active"):
    try:
        match = resolve(context.request.path)
        return cls if match.view_name == url_name else ""
    except Exception:
        return ""
