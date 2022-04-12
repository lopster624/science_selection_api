from django.http import FileResponse
from django.utils.encoding import escape_uri_path
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Booking
from application.mixins import PermissionPolicyMixin, DataApplicationMixin
from application.models import Application, Direction, Education, ApplicationCompetencies, Competence, WorkGroup, \
    ApplicationNote
from application.permissions import IsMasterPermission, IsApplicationOwnerPermission, IsSlavePermission, \
    ApplicationIsNotFinalPermission, IsBookedOnMasterDirectionPermission, IsNestedApplicationOwnerPermission, \
    IsNotFinalNestedApplicationPermission, IsNestedApplicationBookedOnMasterDirectionPermission, \
    IsApplicationBookedByCurrentMasterPermission, DoesMasterHaveDirectionPermission
from application.serializers import ChooseDirectionSerializer, \
    ApplicationListSerializer, DirectionDetailSerializer, DirectionListSerializer, ApplicationSlaveDetailSerializer, \
    ApplicationMasterDetailSerializer, EducationDetailSerializer, ApplicationWorkGroupSerializer, \
    ApplicationSlaveCreateSerializer, ApplicationCompetenciesCreateSerializer, \
    ApplicationCompetenciesSerializer, CompetenceDetailSerializer, \
    BookingSerializer, BookingCreateSerializer, WorkGroupSerializer, ApplicationIsFinalSerializer, \
    WorkGroupDetailSerializer, CompetenceSerializer, ApplicationNoteSerializer
from application.utils import check_role, get_booked_type, get_in_wishlist_type, get_master_affiliations_id, \
    get_application_as_word, get_service_file, update_user_application_scores, set_work_group, set_is_final, \
    has_affiliation, get_competence_list, parse_str_to_bool, remove_direction_from_competence_list, \
    add_direction_to_competence_list
from utils import constants as const

"""
todo: не реализован функционал: загрузка/удаление файлов пользователями, тестирование, 
добавление, просмотр, удаление и изменение заметок, рабочий список, пагинации, фильтры, поиски
просмотр заявки, получение счетчика непросмотренных заявок,
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
        'list': [IsMasterPermission, ],
        'retrieve': [IsMasterPermission | IsApplicationOwnerPermission],
        'create': [IsSlavePermission, ],
        'update': [((IsApplicationOwnerPermission | IsMasterPermission) & ApplicationIsNotFinalPermission) |
                   IsBookedOnMasterDirectionPermission],
        'destroy': [IsAdminUser, ],
        'set_is_final': [IsBookedOnMasterDirectionPermission, ],
        'get_chosen_direction_list': [IsApplicationOwnerPermission | IsMasterPermission],
        'set_chosen_direction_list': [ApplicationIsNotFinalPermission, IsApplicationOwnerPermission],
        'download_application_as_word': [IsMasterPermission, ],
        'get_work_group': [IsBookedOnMasterDirectionPermission, ],
        'set_work_group': [IsBookedOnMasterDirectionPermission, ],
        'get_competences_list': [IsMasterPermission | IsApplicationOwnerPermission],
        'set_competences_list': [IsApplicationOwnerPermission, ApplicationIsNotFinalPermission],
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
        queryset = ApplicationCompetencies.objects.filter(application=self.get_object())
        serializer = ApplicationCompetenciesSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_competences_list.mapping.post
    def set_competences_list(self, request, pk=None):
        """Сохраняет выбранные компетенции пользователя с анкетой pk=pk"""
        self.get_object()  # нужен для работы permissions
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


class EducationViewSet(PermissionPolicyMixin, viewsets.ModelViewSet):
    """
    Список образований или добавление новых.
    """
    serializer_class = EducationDetailSerializer
    permission_classes_per_method = {
        'list': [IsMasterPermission | IsNestedApplicationOwnerPermission],
        'retrieve': [IsMasterPermission | IsNestedApplicationOwnerPermission],
        'create': [((IsNestedApplicationOwnerPermission | IsMasterPermission) & IsNotFinalNestedApplicationPermission) |
                   IsNestedApplicationBookedOnMasterDirectionPermission],
        'update': [((IsNestedApplicationOwnerPermission | IsMasterPermission) & IsNotFinalNestedApplicationPermission) |
                   IsNestedApplicationBookedOnMasterDirectionPermission],
        'destroy': [
            ((IsNestedApplicationOwnerPermission | IsMasterPermission) & IsNotFinalNestedApplicationPermission) |
            IsNestedApplicationBookedOnMasterDirectionPermission
        ]
    }

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


class ApplicationNoteViewSet(viewsets.ModelViewSet, DataApplicationMixin):
    """
    Заметки об анкетах
    """
    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsMasterPermission]

    def get_queryset(self):
        return ApplicationNote.objects.filter(application=self.kwargs['application_pk'],
                                              affiliations__in=self.get_master_affiliations_id()) \
            .select_related('author__user').prefetch_related('affiliations').distinct()

    def perform_destroy(self, instance):
        """ Удаляет заметку, если ее пытается удалить ее автор. """
        if instance.author != self.request.user.member:
            raise PermissionDenied('Удалять заметку может только ее автор')
        instance.delete()

    def perform_create(self, serializer):
        """ Сохраняет запись, установив автора и заявку """
        application = get_object_or_404(Application, pk=self.kwargs['application_pk'])
        serializer.save(author=self.request.user.member, application=application)

    def perform_update(self, serializer):
        """ Обновляет запись, установив автора и заявку """
        application = get_object_or_404(Application, pk=self.kwargs['application_pk'])
        serializer.save(author=self.request.user.member, application=application)


class CompetenceViewSet(PermissionPolicyMixin, viewsets.ModelViewSet, DataApplicationMixin):
    """
    Список компетенций в иерархии или создание новой.
    """
    permission_classes_per_method = {
        'list': [],
        'retrieve': [],
        'create': [IsMasterPermission, ],
    }
    serializer_class = CompetenceDetailSerializer
    queryset = Competence.objects.all()
    http_method_names = ['get', 'post', 'head', 'options', 'trace']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'master_directions': self.get_master_directions()})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BookingViewSet(PermissionPolicyMixin, viewsets.ModelViewSet):
    """
    Список бронирований данной анкеты, создание или удаление бронирования.
    """
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']

    serializers = {
        'delete': BookingCreateSerializer,
        'create': BookingCreateSerializer,
    }
    default_master_serializer_class = BookingSerializer
    permission_classes_per_method = {
        'list': [IsMasterPermission | IsNestedApplicationOwnerPermission],
        'retrieve': [IsMasterPermission | IsNestedApplicationOwnerPermission],
        'create': [IsMasterPermission, ],
        'destroy': [IsMasterPermission, IsApplicationBookedByCurrentMasterPermission],
    }

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
    """
    http_method_names = ['get', 'post', 'delete', 'head', 'options', 'trace']

    serializers = {
        'delete': BookingCreateSerializer,
        'create': BookingCreateSerializer,
    }
    default_master_serializer_class = BookingSerializer
    permission_classes = [IsMasterPermission]

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_master_serializer_class)

    def get_queryset(self):
        application = Application.objects.get(pk=self.kwargs['application_pk'])
        return Booking.objects.filter(slave=application.member, booking_type=get_in_wishlist_type())

    def perform_create(self, serializer):
        application = Application.objects.get(pk=self.kwargs['application_pk'])
        serializer.save(booking_type=get_in_wishlist_type(), slave=application.member, master=self.request.user.member)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not has_affiliation(request.user.member, instance.affiliation):
            raise serializers.ValidationError(
                f"Вы не можете удалить данную запись! Вы не относитесь к <{instance.affiliation}>")
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkGroupViewSet(viewsets.ModelViewSet):
    """
    Рабочие группы
    """
    serializer_class = WorkGroupSerializer
    permission_classes = [IsMasterPermission]

    serializers = {
        'retrieve': WorkGroupDetailSerializer,
        'list': WorkGroupDetailSerializer,
    }
    default_serializer_class = WorkGroupSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer_class)

    def get_queryset(self):
        return WorkGroup.objects.filter(affiliation__in=get_master_affiliations_id(self.request.user.member))

    def perform_create(self, serializer):
        """ Сохраняет рабочую группу, передав юзера для проверки принадлежности """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """ Сохраняет рабочую группу, передав юзера для проверки принадлежности """
        serializer.save(user=self.request.user)


class DownloadServiceDocuments(APIView):
    """
    Генерация и загрузка документов по отбору
    """
    permission_classes = [IsMasterPermission]

    def get(self, request):
        """
        Генерирует служебные файлы формата docx на основе отобранных анкет
        query params:
            doc: обозначает какой из файлов необходимо сгенерировать
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


class DirectionsCompetences(APIView):
    """ Компетенции направлений """
    permission_classes = [DoesMasterHaveDirectionPermission]

    def get(self, request, direction_id):
        """
        Возвращает список компетенций направления если picked=True|None, иначе возвращает список невыбранных компетенций
        на данное направление
        """
        picked = parse_str_to_bool(request.GET.get('picked', True))
        queryset = get_competence_list(direction_id, picked)
        serializer = CompetenceSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, direction_id):
        """ Устанавливает список компетенций направления с id=direction_id """
        old_competences_set_id = set(get_competence_list(direction_id, True).values_list('id', flat=True))
        try:
            new_competences_set_id = set(request.data.get('competences', None))
        except TypeError:
            raise ParseError('Не были переданы необходимые параметры')
        remove_direction_from_competence_list(direction_id, old_competences_set_id - new_competences_set_id)
        add_direction_to_competence_list(direction_id, new_competences_set_id - old_competences_set_id)
        return Response(status=status.HTTP_201_CREATED)
