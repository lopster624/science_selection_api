from django.http import FileResponse
from django.utils.encoding import escape_uri_path
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Booking
from application.models import Application, Direction, Education, ApplicationCompetencies, Competence, WorkGroup
from application.serializers import ChooseDirectionSerializer, \
    ApplicationListSerializer, DirectionDetailSerializer, DirectionListSerializer, ApplicationSlaveDetailSerializer, \
    ApplicationMasterDetailSerializer, EducationDetailSerializer, ApplicationWorkGroupSerializer, \
    ApplicationMasterCreateSerializer, ApplicationSlaveCreateSerializer, ApplicationCompetenciesCreateSerializer, \
    ApplicationCompetenciesSerializer, CompetenceDetailSerializer, \
    BookingSerializer, BookingCreateSerializer, WorkGroupSerializer
from application.utils import check_role, get_booked_type, get_in_wishlist_type, get_master_affiliations_id, \
    get_application_as_word, get_service_file, update_user_application_scores
from utils import constants as const


class DirectionsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод всех направлений или конкретного"""
    queryset = Direction.objects.all()
    serializers = {
        'list': DirectionListSerializer
    }
    default_serializer_class = DirectionDetailSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer_class)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    Главный список заявок
    Также дополнительные вложенные эндпоинты для получения и сохранения компетенций, направлений, рабочих групп.
    """
    # todo: добавить доп. поля в анкету
    queryset = Application.objects.all()

    master_serializers = {
        'get_chosen_direction_list': DirectionDetailSerializer,
        'set_chosen_direction_list': ChooseDirectionSerializer,
        'get_work_group': ApplicationWorkGroupSerializer,
        'set_work_group': ApplicationWorkGroupSerializer,
        'list': ApplicationListSerializer,
        'create': ApplicationMasterCreateSerializer,
        'get_competences_list': ApplicationCompetenciesSerializer,

    }
    default_master_serializer_class = ApplicationMasterDetailSerializer
    slave_serializers = {
        'get_chosen_direction_list': DirectionDetailSerializer,
        'create': ApplicationSlaveCreateSerializer,
        'list': ApplicationListSerializer,
        'get_competences_list': ApplicationCompetenciesSerializer,
        'set_competences_list': ApplicationCompetenciesCreateSerializer
    }
    default_slave_serializer_class = ApplicationSlaveDetailSerializer

    def get_serializer_class(self):
        if check_role(self.request.user, const.SLAVE_ROLE_NAME):
            return self.slave_serializers.get(self.action, self.default_slave_serializer_class)
        elif self.request.user.is_superuser or check_role(self.request.user, const.MASTER_ROLE_NAME):
            return self.master_serializers.get(self.action, self.default_master_serializer_class)
        raise PermissionDenied('Доступ для пользователя без роли запрещен')

    def perform_create(self, serializer):
        serializer.save()
        update_user_application_scores(pk=self.kwargs['pk'])

    def perform_destroy(self, instance):
        instance.delete()
        update_user_application_scores(pk=self.kwargs['pk'])

    def perform_update(self, serializer):
        serializer.save()
        update_user_application_scores(pk=self.kwargs['pk'])

    @action(detail=True, methods=['get'], url_path='directions')
    def get_chosen_direction_list(self, request, pk=None):
        """Отдает список всех выбранных направлений пользователя с анкетой pk=pk"""
        queryset = Direction.objects.filter(application__pk=pk)
        serializer = DirectionDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_chosen_direction_list.mapping.post
    def set_chosen_direction_list(self, request, pk=None):
        """Сохраняет список всех выбранных направлений пользователя с анкетой pk=pk"""
        serializer = ChooseDirectionSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            user_app = serializer.save(pk=pk)
            return Response(user_app, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='download')
    def download_application_as_word(self, request, pk=None):
        """Генерирует word файл анкеты и позволяет скачать его """
        user_app = get_object_or_404(Application.objects.only('member'), pk=pk)
        user_docx = get_application_as_word(request, pk)
        response = FileResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(
            f"Анкета_{user_app.member.user.last_name}.docx") + '"'
        return response

    @action(detail=True, methods=['get'], url_path='work_group')
    def get_work_group(self, request, pk=None):
        """Todo: Проверять, что доступ имеет только мастер"""
        """Отдает выбранную рабочую группу пользователя с анкетой pk=pk"""
        queryset = Application.objects.filter(pk=pk)
        serializer = ApplicationWorkGroupSerializer(queryset)
        return Response(serializer.data)

    @get_work_group.mapping.patch
    def set_work_group(self, request, pk=None):
        """Сохраняет выбранную рабочую группу пользователя с анкетой pk=pk"""
        # TODO: Проверять, что заявка забронирована на данное направление и это рабочая группа данного направления.
        serializer = ApplicationWorkGroupSerializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='competences')
    def get_competences_list(self, request, pk=None):
        """Отдает список всех оцененных компетенций пользователя с анкетой pk=pk"""
        queryset = ApplicationCompetencies.objects.filter(application=pk)
        serializer = ApplicationCompetenciesSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_competences_list.mapping.post
    def set_competences_list(self, request, pk=None):
        """
        todo: Проверять, что свои компетенции может менять только владелец анкеты. И только если анкета не заблокирована
        """
        """Сохраняет выбранные компетенции пользователя с анкетой pk=pk"""
        serializer = ApplicationCompetenciesCreateSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class EducationViewSet(viewsets.ModelViewSet):
    """ Список образований или добавление новых."""
    serializer_class = EducationDetailSerializer

    # TODO: Проверять, что slave может изменить application, к которому относится образование
    def get_queryset(self):
        return Education.objects.filter(application=self.kwargs['application_pk'])

    def perform_create(self, serializer):
        serializer.save()
        update_user_application_scores(pk=self.kwargs['application_pk'])

    def perform_destroy(self, instance):
        instance.delete()
        update_user_application_scores(pk=self.kwargs['application_pk'])

    def perform_update(self, serializer):
        serializer.save()
        update_user_application_scores(pk=self.kwargs['application_pk'])


class CompetenceViewSet(viewsets.ModelViewSet):
    """ Список компетенций в иерархии или создание новой."""
    serializer_class = CompetenceDetailSerializer
    queryset = Competence.objects.all()
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    # TODO: ограничение на post только мастер


class BookingViewSet(viewsets.ModelViewSet):
    """ Список бронирований данной анкеты, создание или удаление бронирования."""
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']

    serializers = {
        'delete': BookingCreateSerializer,
        'create': BookingCreateSerializer,
    }
    default_master_serializer_class = BookingSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_master_serializer_class)

    def get_queryset(self):
        application = Application.objects.get(pk=self.kwargs['application_pk'])
        return Booking.objects.filter(slave=application.member, booking_type=get_booked_type())

    def perform_create(self, serializer):
        application = Application.objects.get(pk=self.kwargs['application_pk'])
        serializer.save(booking_type=get_booked_type(), slave=application.member, master=self.request.user.member)

    def perform_destroy(self, instance):
        # Удаляет рабочую группу
        if instance.slave.application.work_group and instance.booking_type == get_booked_type():
            instance.slave.application.work_group = None
            instance.slave.application.save(update_fields=["work_group"])
        instance.delete()


class WishlistViewSet(viewsets.ModelViewSet):
    """ Список добавлений в список избранных данной анкеты, создание или удаление."""
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']

    serializers = {
        'delete': BookingCreateSerializer,
        'create': BookingCreateSerializer,
    }
    default_master_serializer_class = BookingSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_master_serializer_class)

    def get_queryset(self):
        application = Application.objects.get(pk=self.kwargs['application_pk'])
        return Booking.objects.filter(slave=application.member, booking_type=get_in_wishlist_type())

    def perform_create(self, serializer):
        application = Application.objects.get(pk=self.kwargs['application_pk'])
        serializer.save(booking_type=get_in_wishlist_type(), slave=application.member, master=self.request.user.member)


class WorkGroupViewSet(viewsets.ModelViewSet):
    """ Рабочие группы, только для пользователей с ролью Master """
    serializer_class = WorkGroupSerializer

    def get_queryset(self):
        return WorkGroup.objects.filter(affiliation__in=get_master_affiliations_id(self.request.user.member))

    def perform_create(self, serializer):
        """ Сохраняет рабочую группу, передав юзера для проверки принадлежности """
        serializer.save(user=self.request.user)

class DownloadServiceDocuments(APIView):
    """todo: сделать доступ только у мастера"""

    def get(self, request):
        """
        Генерирует служебные файлы формата docx на основе отобранных анкет
        query params:
            doc: string - обозначает какой из файлов необходимо сгенерировать
                candidates - для итогового списка кандидатов
                rating - для рейтингового списка призыва
                evaluation-statement - для итогового списка кандидатов
            directions: True/False - делать выборку по всем направлениям/по направлениям закрепленными за пользователем
        """
        service_document = request.GET.get('doc', '')
        path_to_file, filename = const.TYPE_SERVICE_DOCUMENT.get(service_document, (None, None))
        if path_to_file:
            user_docx = get_service_file(request, path_to_file, bool(request.GET.get('directions', None)))
            response = FileResponse(user_docx, content_type='application/docx')
            response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(filename) + '"'
            return response
        raise ParseError('Плохой query параметр')
