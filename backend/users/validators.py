import re

from django.core.exceptions import ValidationError


def validate_username(value):
    forbidden_characters = re.sub(r'^[\w.@+-]+\Z', '', value)
    if not forbidden_characters == '':
        raise ValidationError(
            f'Использование символов {forbidden_characters} запрещено.'
        )
    return value
