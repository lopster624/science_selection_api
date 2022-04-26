import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('django.server')


class IncorrectActivationLinkException(Exception):
    """404 ошибка, если ссылка активации не корректна"""
    pass


class ActivationFailedException(Exception):
    """403 ошибка, если активация не была пройдена"""
    pass


class MasterHasNoDirectionsException(Exception):
    """403 ошибка, если у мастера нет направлений"""
    pass


class NoHTTPReferer(Exception):
    """404 ошибка, если нет предыдущей страницы"""
    pass


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    #print(exc)
    # print(response)

    if isinstance(exc, IntegrityError) and not response:
        response = Response(
            {
                'message': 'Кажется, такая запись уже существует.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    return response
