import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('django.server')


class MasterHasNoDirectionsException(APIException):
    status_code = 403
    default_detail = 'У вас нет направлений, за которые вы отвечаете.'
    default_code = 'Отсутствуют направления.'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    # print(exc)
    # print(response)

    if isinstance(exc, IntegrityError) and not response:
        response = Response(
            {
                'message': 'Кажется, такая запись уже существует.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    return response
