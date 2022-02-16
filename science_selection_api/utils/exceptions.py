from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response = Response(status=response.status_code)
    return response


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
