from django import template
from rmn_arch_0.chat.models import Room

register = template.Library()

def has_new_message(user):
    if user.is_authenticated:
        return Room.objects.has_new_message(user)
    else:
        return False

@register.simple_tag
def chat_extra_css(url_name, user):
    """
    Return apporiate css class for chat icon base on the current simple_tag and user
    """
    if url_name == 'messages':
        return ' active'
    elif has_new_message(user):
        return ' new-msg'
    else:
        return ''
