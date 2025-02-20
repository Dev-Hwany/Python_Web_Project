from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """딕셔너리에서 key에 해당하는 값을 반환하는 필터"""
    return dictionary.get(key)