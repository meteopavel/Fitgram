import io

from django.http.response import FileResponse
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.response import Response


def create_ingredients_list(ingredients):
    shopping_list = []
    for item in ingredients:
        name = item.get('ingredient__name', 'Не указано')
        measurement_unit = (
            item.get('ingredient__measurement_unit', 'г.'))
        amount = item.get('ingredient_amount', 0)
        shopping_list.append(f'{name} - {amount}{measurement_unit}')
    return '\n'.join(shopping_list)


def get_pdf_shopping_list(items):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    pdfmetrics.registerFont(TTFont('Lobster', 'static/Lobster-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('AmaticSC', 'static/AmaticSC-Regular.ttf'))
    p.setFont('Lobster', 30)
    p.drawCentredString(290, 780, 'Что нужно купить:')
    p.setFont('AmaticSC', 28)
    text_object = p.beginText(2.5 * cm, 27 * cm - 2 * cm)
    for line in create_ingredients_list(items).splitlines(False):
        text_object.textLine(line.rstrip())
    p.drawText(text_object)
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True,
                        filename='shopping_list.pdf')


def create_related_object(pk, request, serializer_class):
    serializer = serializer_class(
        data={'user': request.user.id, 'recipe': pk},
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_related_object(pk, request, model):
    to_delete = model.objects.filter(user=request.user, recipe=pk).delete()
    if not to_delete[0]:
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={'message': 'Объект не найден'})
    return Response(status=status.HTTP_204_NO_CONTENT)
