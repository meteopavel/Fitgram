from rest_framework.exceptions import ValidationError


def validate_empty_fields(validated_data):
    required_fields = ('tags', 'ingredients')
    for field in required_fields:
        if field not in validated_data:
            raise ValidationError(f'Требуется поле {field}')


def validate_list(value, field):
    if not value:
        raise ValidationError(f'Нужно добавить {field}!')
    elif len(set(value)) != len(value):
        raise ValidationError(f'Нельзя дублировать {field}!')
