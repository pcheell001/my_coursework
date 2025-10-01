from django import template

register = template.Library()

@register.filter
def truncate_chars(value, max_length):
    if len(value) > max_length:
        return value[:max_length] + '...'
    return value

@register.filter
def days_until(due_date):
    from django.utils import timezone
    if due_date:
        delta = due_date - timezone.now()
        return delta.days
    return None

@register.filter
def is_past_due(due_date):
    from django.utils import timezone
    if due_date:
        return due_date < timezone.now()
    return False