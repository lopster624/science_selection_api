from django.http import FileResponse
from django.utils.encoding import escape_uri_path
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Booking
from application.mixins import PermissionPolicyMixin
from application.models import Application, Direction, Education, ApplicationCompetencies, Competence, WorkGroup
from application.permissions import IsMasterPermission, IsApplicationOwnerPermission, IsSlavePermission, \
    ApplicationIsNotFinalPermission, IsBookedOnMasterDirectionPermission
from application.serializers import ChooseDirectionSerializer, \
    ApplicationListSerializer, DirectionDetailSerializer, DirectionListSerializer, ApplicationSlaveDetailSerializer, \
    ApplicationMasterDetailSerializer, EducationDetailSerializer, ApplicationWorkGroupSerializer, \
    ApplicationSlaveCreateSerializer, ApplicationCompetenciesCreateSerializer, \
    ApplicationCompetenciesSerializer, CompetenceDetailSerializer, \
    BookingSerializer, BookingCreateSerializer, WorkGroupSerializer, ApplicationIsFinalSerializer
from application.utils import check_role, get_booked_type, get_in_wishlist_type, get_master_affiliations_id, \
    get_application_as_word, get_service_file, update_user_application_scores, set_work_group, set_is_final
from utils import constants as const

"""
todo: не реализован функционал: загрузка/удаление файлов пользователями, тестирование, 
добавление компетенций в направление, удаление компетенций из направлений, список выбранных/не выбранных компетенций на 
направление, добавление, удаление и изменение заметок, блокирование анкеты, рабочий список, установка ограничений 
по ролям, is_final и направлениям, пагинации, фильтры, поиски,
"""


class DirectionsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод всех направлений или конкретного"""
    queryset = Direction.objects.all()
    serializers = {
        'list': DirectionListSerializer
    }
    default_serializer_class = DirectionDetailSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer_class)


class ApplicationViewSet(PermissionPolicyMixin, viewsets.ModelViewSet):
    """
    Главный список заявок
    Также дополнительные вложенные эндпоинты для получения и сохранения компетенций, направлений, рабочих групп.
    Доступ:
        лист заявок - master
        заявка - master или хозяин заявки
        создание заявки - slave
        редактирование заявки - хозяин заявки и master, если заявка не is_final, мастер,
                                если заявка отобрана на его направление

        удаление заявки - админ
        список направлений - master или хозяин заявки
        установка направления - хозяин заявки, если заявка не is_final
        скачать анкету word - master
        просмотр и установка рабочей группы - мастер, если заявка отобрана на его направление
        просмотр списка компетенций - master или хозяин заявки
        установка компетенций - хозяин заявки, если заявка не is_final
        установка is_final - мастер, если заявка отобрана на его направление
    """
    # todo: добавить доп. поля в анкету, фильтрацию, пагинацию
    queryset = Application.objects.all()
    master_serializers = {
        'get_chosen_direction_list': DirectionDetailSerializer,
        'set_chosen_direction_list': ChooseDirectionSerializer,
        'get_work_group': ApplicationWorkGroupSerializer,
        'set_work_group': ApplicationWorkGroupSerializer,
        'set_is_final': ApplicationIsFinalSerializer,
        'list': ApplicationListSerializer,
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
    permission_classes_per_method = {
        'list': [IsMasterPermission, ],  # проверено
        'retrieve': [IsMasterPermission | IsApplicationOwnerPermission],  # проверено
        'create': [IsSlavePermission, ],  # проверено
        'update': [((IsApplicationOwnerPermission | IsMasterPermission) & ApplicationIsNotFinalPermission) |
                   IsBookedOnMasterDirectionPermission],  # проверено
        'destroy': [IsAdminUser, ],  # проверено
        'set_is_final': [IsBookedOnMasterDirectionPermission, ],  # проверено
        'get_chosen_direction_list': [IsApplicationOwnerPermission | IsMasterPermission],  # проверено
        'set_chosen_direction_list': [ApplicationIsNotFinalPermission, IsApplicationOwnerPermission],  # проверено
        'download_application_as_word': [IsMasterPermission, ],  # проверено
        'get_work_group': [IsBookedOnMasterDirectionPermission, ],  # проверено
        'set_work_group': [IsBookedOnMasterDirectionPermission, ],  # проверено
        'get_competences_list': [IsMasterPermission | IsApplicationOwnerPermission],
        'set_competences_list': [ApplicationIsNotFinalPermission, IsApplicationOwnerPermission],
    }

    def get_serializer_class(self):
        if check_role(self.request.user, const.SLAVE_ROLE_NAME):
            return self.slave_serializers.get(self.action, self.default_slave_serializer_class)
        elif self.request.user.is_superuser or check_role(self.request.user, const.MASTER_ROLE_NAME):
            return self.master_serializers.get(self.action, self.default_master_serializer_class)
        return self.default_slave_serializer_class  # раньше вызывал ошибку

    def perform_create(self, serializer):
        application = serializer.save(member=self.request.user.member)
        update_user_application_scores(pk=application.pk)

    def perform_update(self, serializer):
        serializer.save()
        update_user_application_scores(pk=self.kwargs['pk'])

    @action(detail=True, methods=['get'], url_path='directions')
    def get_chosen_direction_list(self, request, pk=None):
        """Отдает список всех выбранных направлений пользователя с анкетой pk=pk"""
        queryset = Direction.objects.filter(application=self.get_object())
        serializer = DirectionDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_chosen_direction_list.mapping.post
    def set_chosen_direction_list(self, request, pk=None):
        """Сохраняет список всех выбранных направлений пользователя с анкетой pk=pk"""
        serializer = ChooseDirectionSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            user_app = serializer.save(user_app=self.get_object())
            return Response(user_app, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='download')
    def download_application_as_word(self, request, pk=None):
        """Генерирует word файл анкеты и позволяет скачать его """
        user_docx = get_application_as_word(request, pk)
        response = FileResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(
            f"Анкета_{self.get_object().member.user.last_name}.docx") + '"'
        return response

    @action(detail=True, methods=['get'], url_path='work_group')
    def get_work_group(self, request, pk=None):
        """Отдает выбранную рабочую группу пользователя с анкетой pk=pk"""
        serializer = ApplicationWorkGroupSerializer(self.get_object())
        return Response(serializer.data)

    @get_work_group.mapping.patch
    def set_work_group(self, request, pk=None):
        """Сохраняет выбранную рабочую группу пользователя с анкетой pk=pk"""
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

    @action(detail=True, methods=['patch'], url_path='blocking')
    def set_is_final(self, request, pk=None):
        """Меняет статус заблокированности анкеты для редактирования"""
        serializer = ApplicationIsFinalSerializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class EducationViewSet(viewsets.ModelViewSet):
    """
    Список образований или добавление новых.
    Доступ:
        лист - master, хозяин заявки
        образование - master или хозяин заявки
        создание - master, хозяин заявки, если заявка не is_final, мастер, если заявка отобрана на его направление
        редактирование - хозяин заявки и master, если заявка не is_final, мастер, если заявка отобрана на его направление
        удаление - хозяин заявки и master, если заявка не is_final, мастер, если заявка отобрана на его направление
    """
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
    """
    Список компетенций в иерархии или создание новой.
    Доступ:
        список - any
        компетенция - any
        создание - мастер
    """
    serializer_class = CompetenceDetailSerializer
    queryset = Competence.objects.all()
    http_method_names = ['get', 'post', 'head', 'options', 'trace']


class BookingViewSet(viewsets.ModelViewSet):
    """
    Список бронирований данной анкеты, создание или удаление бронирования.
    Доступ:
        список - any
        бронирование - any
        создание - master
        удаление - master, если заявка отобрана на его направление
    """
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
            set_work_group(instance.slave.application, None)
        # Разблокирует анкету, если она заблокирована
        if instance.slave.application.is_final:
            set_is_final(instance.slave.application, False)
        instance.delete()


class WishlistViewSet(viewsets.ModelViewSet):
    """
    Список добавлений в список избранных данной анкеты, создание или удаление.
    Доступ:
        список - master
        в вишлисте - master
        создание - master
        удаление - master, если эта запись в его принадлежности
    """
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
    """
    Рабочие группы
    Доступ: master
    """
    serializer_class = WorkGroupSerializer

    def get_queryset(self):
        return WorkGroup.objects.filter(affiliation__in=get_master_affiliations_id(self.request.user.member))

    def perform_create(self, serializer):
        """ Сохраняет рабочую группу, передав юзера для проверки принадлежности """
        serializer.save(user=self.request.user)


class DownloadServiceDocuments(APIView):
    """
    Генерация и загрузка документов по отбору
    Доступ: master
    """

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
