import datetime
import re
from io import BytesIO

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from docxtpl import DocxTemplate

from account.models import Member, Affiliation, Booking
from utils.calculations import get_current_draft_year, convert_float
from utils.constants import BOOKED, MEANING_COEFFICIENTS, PATH_TO_RATING_LIST, \
    PATH_TO_CANDIDATES_LIST, PATH_TO_EVALUATION_STATEMENT
from utils.constants import NAME_ADDITIONAL_FIELD_TEMPLATE
from .models import Application, AdditionField, AdditionFieldApp, MilitaryCommissariat


def check_role(user, role_name):
    """ Проверяет, совпадает ли роль пользователя с заданной через параметр role_name """
    member = Member.objects.select_related('role').get(user=user)
    if member.role.role_name == role_name:
        return True
    return False


def check_permission_decorator(role_name=None):
    """ Декоратор, который проверяет роль пользователя с заданной через параметр role_name """

    def decorator(func):
        def wrapper(self, request, pk, *args, **kwargs):
            if request.user.member.role.role_name == role_name:
                return func(self, request, pk, *args, **kwargs)
            member = Member.objects.filter(application__id=pk).first()
            if member != request.user.member:
                raise PermissionDenied('Недостаточно прав для входа на данную страницу.')
            return func(self, request, pk, *args, **kwargs)

        return wrapper

    return decorator


def check_final_decorator(func):
    """Декоратор, который проверяет, что анкету пользователя можно редактировать.
     В противном случае редиректит на предыдущую страницу"""

    def wrapper(self, request, pk, *args, **kwargs):
        user_app = get_object_or_404(Application.objects.only('is_final'), pk=pk)
        if user_app.is_final:
            return redirect(request.path_info)
        return func(self, request, pk, *args, **kwargs)

    return wrapper


class WordTemplate:
    """ Класс для создания шаблона ворд документа по файлу, который через путь - path_to_template """

    def __init__(self, request, path_to_template):
        self.request = request
        self.path = path_to_template

    def create_word_in_buffer(self, context):
        """ Создает ворд документ и добавлет в него данные и сохраняет в буфер """
        template = DocxTemplate(self.path)
        user_docx = BytesIO()
        template.render(context=context)
        template.save(user_docx)
        user_docx.seek(0)
        return user_docx

    def create_context_to_interview_list(self, pk):
        """ Создает контекст для шаблона - 'Лист собеседования' """
        user_app = Application.objects.select_related('member').prefetch_related('education').defer('id').get(pk=pk)
        user_education = user_app.education.order_by('-end_year').values()
        user_education = user_education[0] if user_education else {}
        context = {**user_app.__dict__, **user_education}
        context.update({'father_name': user_app.member.father_name, 'phone': user_app.member.phone})
        context.update({'first_name': user_app.member.user.first_name, 'last_name': user_app.member.user.last_name})
        return context

    def create_context_to_word_files(self, document_type, all_directions=None):
        """ Создает контексты для шаблонов итоговых документов """
        current_year, current_season = get_current_draft_year()
        fixed_directions = self.request.user.member.affiliations.select_related('direction').all() \
            if not all_directions else Affiliation.objects.select_related('direction').all()

        context = {'directions': []}
        for direction in fixed_directions:
            platoon_data = {
                'name': direction.direction.name,
                'company_number': direction.company,
                'members': []
            }
            booked = Booking.objects.select_related('slave').filter(affiliation=direction, booking_type__name=BOOKED)
            booked_slaves = [b.slave for b in booked]
            booked_user_apps = Application.objects.select_related('scores', 'member__user').prefetch_related(
                'education'). \
                filter(member__in=booked_slaves, draft_year=current_year, draft_season=current_season[0]).all()

            for i, user_app in enumerate(booked_user_apps):
                user_last_education = user_app.education.all()[0]
                general_info, additional_info = {'number': i + 1,
                                                 'first_name': user_app.member.user.first_name,
                                                 'last_name': user_app.member.user.last_name,
                                                 'father_name': user_app.member.father_name,
                                                 'final_score': convert_float(user_app.final_score),
                                                 }, {}
                if document_type == PATH_TO_CANDIDATES_LIST:
                    additional_info = self._get_candidates_info(user_app, user_last_education)
                elif document_type == PATH_TO_RATING_LIST:
                    additional_info = self._get_rating_info(user_app, user_last_education)
                elif document_type == PATH_TO_EVALUATION_STATEMENT:
                    additional_info = self._get_evaluation_st_info(user_app)
                platoon_data['members'].append({**additional_info, **general_info})
            if platoon_data['members']:
                context['directions'].append(platoon_data)
        return context

    def create_context_to_psychological_test(self, user_test_result, questions, user_answers):
        """ Создает контекст для шаблона - 'Психологического теста ОПВС - 2' """
        user_app = Application.objects.only('birth_day').get(member=user_test_result.member)
        member = user_test_result.member
        context = {
            'full_name': f'{member.user.last_name} {member.user.first_name} {member.father_name}',
            'b_day': user_app.birth_day.strftime('%d %m %Y'),
            'now': datetime.datetime.now().strftime('%d %m %Y'),
            'position': 'гражданин',
            'questions': []
        }
        for i, question in enumerate(questions, 1):
            context['questions'].append({
                'num': i,
                'answers': [ans.id for ans in question.answer_options.all()],
                'response': user_answers.get(question.id)
            })
        return context

    def _get_evaluation_st_info(self, user_app):
        return {
            **{k: convert_float(v) for k, v in MEANING_COEFFICIENTS.items()},
            **{k: convert_float(v) for k, v in user_app.scores.__dict__.items() if isinstance(v, float)},
        }

    def _get_rating_info(self, user_app, user_last_education):
        return {
            'birth_day': user_app.birth_day,
            'military_commissariat': user_app.military_commissariat,
            'university': user_last_education.university,
            'specialization': user_last_education.specialization,
            'avg_score': convert_float(user_last_education.avg_score),
        }

    def _get_candidates_info(self, user_app, user_last_education):
        commissariat = MilitaryCommissariat.objects.filter(name=user_app.military_commissariat).first()
        return {
            'subject': commissariat.subject if commissariat else '',
            'birth_day': user_app.birth_day.year,
            'avg_score': convert_float(user_last_education.avg_score),
        }


def check_booking_our_or_exception(pk, user):
    """Проверяет, что пользователь с айди анкеты pk был забронирован на направления пользователя user и
    рейзит ошибку, если не забронирован."""
    if not is_booked_our(pk, user):
        raise PermissionDenied('Данный пользователь не отобран на ваше направление.')


def is_booked_our(pk, user):
    """
    Возвращает True, если пользователь с айди анкеты = pk забронирован на направления user,
    в обратном случае - False
    """
    app = get_object_or_404(Application, pk=pk)
    master_affiliations = Affiliation.objects.filter(member=user.member)
    return Booking.objects.filter(slave=app.member, booking_type__name=BOOKED,
                                  affiliation__in=master_affiliations).exists()


def add_additional_fields(request, user_app):
    additional_fields = [int(re.search('\d+', field).group(0)) for field in request.POST
                         if NAME_ADDITIONAL_FIELD_TEMPLATE in field]
    if additional_fields:
        addition_fields = AdditionField.objects.filter(pk__in=additional_fields)
        for field in addition_fields:
            AdditionFieldApp.objects.update_or_create(addition_field=field, application=user_app,
                                                      defaults={'value': request.POST.get(
                                                          f"{NAME_ADDITIONAL_FIELD_TEMPLATE}{field.id}")})


def get_cleared_query_string_of_page(query_string):
    """Возвращает строку query-параметров без параметра page"""
    if not query_string:
        return ''
    return '&'.join(param for param in query_string.split('&') if 'page=' not in param) + '&'


def get_sorted_queryset(apps, ordering):
    """Возвращает отсортированый queryset по our_direction и ordering(если есть)"""
    if ordering:
        return apps.order_by('-our_direction', ordering)
    return apps.order_by('-our_direction')


def get_form_data(get_dict):
    """Если в словаре get_dict содержится что-то кроме page, то возвращает его. В противном случае возвращает None"""
    orig_dict = dict(get_dict)
    orig_dict.pop('page', None)
    if not orig_dict:
        return None
    return get_dict
