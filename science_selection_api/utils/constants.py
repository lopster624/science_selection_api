import os

# диапозон оценок средних баллов
MINIMUM_SCORE = 2
MAX_SCORE = 5

# возможные статусы заявки
BOOKED = 'Отобран'
IN_WISHLIST = 'В избранном'

# роли пользователей в системе
MASTER_ROLE_NAME = 'Отбирающий'
SLAVE_ROLE_NAME = 'Оператор'

# название типа спихологического теста
PSYCHOLOGICAL_TYPE_OF_TEST = 'Психологический'

# Шаблон URL`а для активации учетой записи
ACTIVATION_LINK = os.environ.get("DJANGO_ACTIVATION_LINK", "127.0.0.1:8000/accounts/activation/")

# деление призывов на сезоны
MIDDLE_RECRUITING_DATE = {'day': 15, 'month': 7}

# коэффициенты для расчета итогового  балла оператора
MEANING_COEFFICIENTS = {'k1': float(os.environ.get("DJANGO_VALUE_OF_K1_COEF")),
                        'k2': float(os.environ.get("DJANGO_VALUE_OF_K2_COEF")),
                        'k3': float(os.environ.get("DJANGO_VALUE_OF_K3_COEF")),
                        'k4': float(os.environ.get("DJANGO_VALUE_OF_K4_COEF")),
                        'k5': float(os.environ.get("DJANGO_VALUE_OF_K5_COEF")),
                        'k6': float(os.environ.get("DJANGO_VALUE_OF_K6_COEF")),
                        'k7': float(os.environ.get("DJANGO_VALUE_OF_K7_COEF"))}

# задавать через переменные окружения? для все коэф ниже - или через файл -> в перемен окр
# баллы, начисляемые в критерии a1
INTERNATIONAL_ARTICLES_SCORE = 5
PATENTS_SCORE = 4
VAC_ARTICLES_SCORE = 3
INNOVATION_PROPOSALS_SCORE = 1
RINC_ARTICLES_SCORE = 1
EVM_REGISTER_SCORE = 0.5

# баллы, начисляемые в критерии a2
BACHELOR_COEF = 0.8
SPECIAL_AND_MORE_COEF = 1

# баллы, начисляемые в критерии a3
COMPLIANCE_PRIOR_DIRECTION_SCORE = 3
COMPLIANCE_ADDITIONAL_DIRECTION_SCORE = 1

# баллы, начисляемые в критерии a4
INTERNATIONAL_OLYMPICS_SCORE = 4
PRESIDENT_SCHOLARSHIP_SCORE = 4
COUNTRY_OLYMPICS_SCORE = 3
GOVERNMENT_SCHOLARSHIP_SCORE = 3
MILITARY_GRANTS_SCORE = 3
REGION_OLYMPICS_SCORE = 2
CITY_OLYMPICS_SCORE = 1

# баллы, начисляемые в критерии a5
POSTGRADUATE_ADDITIONAL_DIRECTION_SCORE = 6
POSTGRADUATE_PRIOR_DIRECTION_SCORE = 8
POSTGRADUATE_ENDED_SCORE = 3

# баллы, начисляемые в критерии a6
COMMERCIAL_EXPERIENCE_SCORE = 2
OPK_EXPERIENCE_SCORE = 4
SCIENCE_EXPERIENCE_SCORE = 6

# баллы, начисляемые в критерии a7
MILITARY_SPORT_ACHIEVEMENTS_SCORE = 4
SPORT_ACHIEVEMENTS_SCORE = 2

# шаблон для заполненности заявки
DEFAULT_FILED_BLOCKS = {
    'Основные данные': False,
    'Образование': False,
    'Направления': False,
    'Компетенции': False,
    'Загруженные файлы': False,
}

# пути к шаблоннам файлов word, но основе которых генерируются основные документы
PATH_TO_INTERVIEW_LIST = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_INTERVIEW_LIST"))
PATH_TO_CANDIDATES_LIST = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_CANDIDATES_LIST"))
PATH_TO_RATING_LIST = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_RATING_LIST"))
PATH_TO_EVALUATION_STATEMENT = os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_EVALUATION_STATEMENT"))
PATH_TO_PSYCHOLOGICAL_TESTS = {
    os.environ.get("DJANGO_NAME_OF_FIRST_PSYCHOLOGICAL_TEST"):
        os.path.join(os.path.abspath(os.curdir), os.environ.get("DJANGO_PATH_TO_FIRST_PSYCHOLOGICAL_TEST")),
}

TYPE_SERVICE_DOCUMENT = {
    'candidates': (PATH_TO_CANDIDATES_LIST, "Итоговый список кандидатов.docx"),
    'rating': (PATH_TO_RATING_LIST, "Рейтинговый список призыва.docx"),
    'evaluation-statement': (PATH_TO_EVALUATION_STATEMENT, "Оценочная ведомость.docx"),
}

# Ограничение на максимальное количество выбираемых направлений
MAX_APP_DIRECTIONS = int(os.environ.get("DJANGO_MAX_APP_DIRECTIONS", 4))

# шаблон для именования полей в форме html в тестах пользователей
NAME_ADDITIONAL_FIELD_TEMPLATE = 'additional_field_'
