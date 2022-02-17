import datetime

from application.models import Application
from .constants import MIDDLE_RECRUITING_DATE


def get_current_draft_year():
    """Возвращает кортеж вида: <текущий год,  (номер, Имя сезона)> для текущего сезона"""
    current_date = datetime.date.today()
    middle_date = datetime.date(current_date.year, MIDDLE_RECRUITING_DATE['month'], MIDDLE_RECRUITING_DATE['day'])
    recruiting_season = Application.season[1] if current_date > middle_date else Application.season[0]
    return current_date.year, recruiting_season


def convert_float(value):
    return str(value).replace('.', ',')
