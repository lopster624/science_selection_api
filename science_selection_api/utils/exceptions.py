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
