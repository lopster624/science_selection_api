import os

from django.db.models import Q, Prefetch
from django.http import FileResponse
from django.utils.encoding import escape_uri_path
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, serializers, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from account.models import Booking
from application.mixins import PermissionPolicyMixin, DataApplicationMixin
from application.models import Application, Direction, Education, ApplicationCompetencies, Competence, WorkGroup, \
    ApplicationNote, File
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
    WorkGroupDetailSerializer, CompetenceSerializer, ApplicationNoteSerializer, ViewedApplicationSerializer, \
    FileSerializer, ApplicationMasterListSerializer, BookingDetailSerializer, WorkingListSerializer
from application.utils import get_booked_type, get_in_wishlist_type, get_master_affiliations_id, \
    get_application_as_word, get_service_file, update_user_application_scores, set_work_group, set_is_final, \
    has_affiliation, get_competence_list, parse_str_to_bool, remove_direction_from_competence_list, \
    add_direction_to_competence_list, has_application_viewed, PaginationApplication, ApplicationFilter, \
    CustomOrderingFilter, ApplicationExporter, get_applications_by_master, get_applications_by_slave, is_master, \
    is_slave, WorkingListFilter, get_chosen_affiliation_id
from utils import constants as const

"""
todo: не реализован функционал: рабочий список, дополнительные поля заявки(возможно)
"""


class DirectionsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод всех направлений или конкретного."""
    queryset = Direction.objects.all()
    serializers = {
        'list': DirectionListSerializer
    }
    default_serializer_class = DirectionDetailSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer_class)


class ApplicationViewSet(PermissionPolicyMixin, DataApplicationMixin, viewsets.ModelViewSet):
    """
    Главный список заявок
    Также дополнительные вложенные эндпоинты для получения и сохранения компетенций, направлений, рабочих групп.
    """
    pagination_class = PaginationApplication
    filter_backends = [DjangoFilterBackend, CustomOrderingFilter, SearchFilter]
    filterset_class = ApplicationFilter
    ordering_fields = ['member__user__last_name', 'birth_place', 'subject', 'final_score', 'fullness']
    ordering = ['-our_direction']
    search_fields = ['member__user__first_name', 'member__user__last_name', 'member__father_name',
                     'education__university', 'subject', 'education__specialization', 'birth_place']

    master_serializers = {
        'get_chosen_direction_list': DirectionDetailSerializer,
        'set_chosen_direction_list': ChooseDirectionSerializer,
        'get_work_group': ApplicationWorkGroupSerializer,
        'set_work_group': ApplicationWorkGroupSerializer,
        'set_is_final': ApplicationIsFinalSerializer,
        'list': ApplicationMasterListSerializer,
        'get_competences_list': ApplicationCompetenciesSerializer,
        'view_application': ViewedApplicationSerializer,
        'export_applications_list': ApplicationMasterListSerializer
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
        'view_application': [IsMasterPermission, ],
        'export_applications_list': [IsMasterPermission, ],
    }

    def get_queryset(self):
        """Возвращает разные queryset для разных ролей."""
        if is_master(self.request.user):
            apps = get_applications_by_master(self.request.user, self.get_master_affiliations(),
                                              self.get_master_directions(), self.get_master_directions_id())
        elif is_slave(self.request.user) or self.request.user.is_superuser:
            apps = get_applications_by_slave()
        else:
            apps = Application.objects.all()
        return apps

    def get_serializer_class(self):
        if is_slave(self.request.user):
            return self.slave_serializers.get(self.action, self.default_slave_serializer_class)
        elif self.request.user.is_superuser or is_master(self.request.user):
            return self.master_serializers.get(self.action, self.default_master_serializer_class)
        return self.default_slave_serializer_class

    def perform_create(self, serializer):
        application = serializer.save(member=self.request.user.member)
        update_user_application_scores(pk=application.pk)

    def perform_update(self, serializer):
        serializer.save()
        update_user_application_scores(pk=self.kwargs['pk'])

    @action(detail=False, methods=['get'], url_path='export')
    def export_applications_list(self, request):
        """Сохраняет список заявок в exel файл и возвращает его."""
        # queryset = self.filter_queryset(self.get_queryset())
        queryset = self.get_queryset()
        excel_from_apps = ApplicationExporter(queryset)
        excel_file = excel_from_apps.add_applications_to_sheet()
        response = FileResponse(excel_file, content_type='application/xlsx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path('Список заявок.xlsx') + '"'
        return response

    @action(detail=True, methods=['get'], url_path='directions')
    def get_chosen_direction_list(self, request, pk=None):
        """Отдает список всех выбранных направлений пользователя с анкетой pk=pk."""
        queryset = Direction.objects.filter(application=self.get_object())
        serializer = DirectionDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_chosen_direction_list.mapping.post
    def set_chosen_direction_list(self, request, pk=None):
        """Сохраняет список всех выбранных направлений пользователя с анкетой pk=pk."""
        serializer = ChooseDirectionSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            user_app = serializer.save(user_app=self.get_object())
            return Response(user_app, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='download')
    def download_application_as_word(self, request, pk=None):
        """Генерирует word файл анкеты и позволяет скачать его."""
        user_docx = get_application_as_word(request, pk)
        response = FileResponse(user_docx, content_type='application/docx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path(
            f"Анкета_{self.get_object().member.user.last_name}.docx") + '"'
        return response

    @action(detail=True, methods=['get'], url_path='work_group')
    def get_work_group(self, request, pk=None):
        """Отдает выбранную рабочую группу пользователя с анкетой pk=pk."""
        serializer = ApplicationWorkGroupSerializer(self.get_object())
        return Response(serializer.data)

    @get_work_group.mapping.patch
    def set_work_group(self, request, pk=None):
        """Сохраняет выбранную рабочую группу пользователя с анкетой pk=pk."""
        serializer = ApplicationWorkGroupSerializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='competences')
    def get_competences_list(self, request, pk=None):
        """Отдает список всех оцененных компетенций пользователя с анкетой pk=pk."""
        queryset = ApplicationCompetencies.objects.filter(application=self.get_object())
        serializer = ApplicationCompetenciesSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_competences_list.mapping.post
    def set_competences_list(self, request, pk=None):
        """Сохраняет выбранные компетенции пользователя с анкетой pk=pk."""
        self.get_object()  # нужен для работы permissions
        serializer = ApplicationCompetenciesCreateSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='blocking')
    def set_is_final(self, request, pk=None):
        """Меняет статус заблокированности анкеты для редактирования."""
        serializer = ApplicationIsFinalSerializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='view')
    def view_application(self, request, pk=None):
        """Помечает заявку как просмотренную мастером."""
        application = self.get_object()
        serializer = ViewedApplicationSerializer(data={'application': application.id, 'member': request.user.member.id})
        if serializer.is_valid(raise_exception=True) and not has_application_viewed(application,
                                                                                    request.user.member.id):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


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
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Education.objects.none()
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
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return ApplicationNote.objects.none()
        return ApplicationNote.objects.filter(application=self.kwargs['application_pk'],
                                              affiliations__in=self.get_master_affiliations_id()) \
            .select_related('author__user').prefetch_related('affiliations').distinct()

    def perform_destroy(self, instance):
        """Удаляет заметку, если ее пытается удалить ее автор."""
        if instance.author != self.request.user.member:
            raise PermissionDenied('Удалять заметку может только ее автор')
        instance.delete()

    def perform_create(self, serializer):
        """Сохраняет запись, установив автора и заявку."""
        application = get_object_or_404(Application, pk=self.kwargs['application_pk'])
        serializer.save(author=self.request.user.member, application=application)

    def perform_update(self, serializer):
        """Обновляет запись, установив автора и заявку."""
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
    queryset = Competence.objects.all().prefetch_related('child__child__child')
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
    default_master_serializer_class = BookingDetailSerializer
    permission_classes_per_method = {
        'list': [IsMasterPermission | IsNestedApplicationOwnerPermission],
        'retrieve': [IsMasterPermission | IsNestedApplicationOwnerPermission],
        'create': [IsMasterPermission, ],
        'destroy': [IsMasterPermission, IsApplicationBookedByCurrentMasterPermission],
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_master_serializer_class)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Booking.objects.none()
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
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return Booking.objects.none()
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
        return WorkGroup.objects.filter(
            affiliation__in=get_master_affiliations_id(self.request.user.member)).select_related('affiliation')

    def perform_create(self, serializer):
        """Сохраняет рабочую группу, передав юзера для проверки принадлежности"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Сохраняет рабочую группу, передав юзера для проверки принадлежности"""
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not has_affiliation(request.user.member, instance.affiliation):
            raise serializers.ValidationError(
                f"Вы не можете удалить данную запись! Вы не относитесь к <{instance.affiliation}>")
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FileViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    """
    Файл
    """
    serializer_class = FileSerializer
    permission_classes = [IsMasterPermission | IsSlavePermission]

    def get_queryset(self):
        """
        Отдает список шаблонов(если запрос от master) или загруженных файлов (если запрос от slave).
        query params:
            template: true/false - нужно возвращать шаблоны документов
            member_id: id участника, загрузившего документ

        Для slave query-параметр member_id игнорируется. Если template=True, то возвращаются шаблоны документов,
        иначе - загруженные slave'ом документы.

        Для master query-параметр template игнорируется. Если передан member_id - возвращает загруженные документы
        member'ом, иначе - шаблонны документов.
        """
        member_id = self.request.user.member.id if self.request.user.member.is_slave() else self.request.GET.get(
            'member_id', None)

        is_template = not member_id if self.request.user.member.is_master() else parse_str_to_bool(
            self.request.GET.get('template', False))

        return File.objects.filter(Q(is_template=True) if is_template else Q(member__id=member_id, is_template=False))

    def perform_create(self, serializer):
        """Сохраняет файл, передав доп. информацию."""
        serializer.save(member=self.request.user.member,
                        file_name=os.path.basename(serializer.validated_data.get('file_path').name),
                        is_template=self.request.user.member.is_master())

    def perform_destroy(self, instance):
        """Удаляет файл, если его пытается удалить его создатель."""
        if instance.member != self.request.user.member:
            raise PermissionDenied('Удалять файл может только его создатель.')
        instance.delete()


class WorkingListViewSet(DataApplicationMixin, mixins.ListModelMixin, GenericViewSet):
    """Рабочий список."""
    permission_classes = [IsMasterPermission, ]
    serializer_class = WorkingListSerializer

    pagination_class = PaginationApplication
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_class = WorkingListFilter
    ordering_fields = ['member__user__last_name', 'birth_place', 'subject']
    ordering = ['member__user__last_name']
    search_fields = ['member__user__first_name', 'member__user__last_name', 'member__father_name',
                     'education__university', 'subject', 'education__specialization', 'birth_place']

    def get_queryset(self):
        chosen_affiliation_id = get_chosen_affiliation_id(self.request)
        chosen_direction = Direction.objects.get(affiliation__id=chosen_affiliation_id)
        apps = get_applications_by_master(self.request.user, self.get_master_affiliations(),
                                          self.get_master_directions(), self.get_master_directions_id())
        apps = apps.prefetch_related(
            Prefetch(
                "app_competence",
                queryset=ApplicationCompetencies.objects.filter(competence__directions=chosen_direction,
                                                                level__in=[1, 2, 3]).select_related('competence'),
                to_attr='rated_competences'
            ))

        return apps

    @action(detail=False, methods=['get'], url_path='export')
    def export_working_list(self, request):
        """Сохраняет рабочей список заявок в exel файл и возвращает его."""
        queryset = self.filter_queryset(self.get_queryset())
        excel_from_apps = ApplicationExporter(queryset)
        excel_file = excel_from_apps.add_work_list_to_sheet()
        response = FileResponse(excel_file, content_type='application/xlsx')
        response['Content-Disposition'] = 'attachment; filename="' + escape_uri_path('Рабочий лист.xlsx') + '"'
        return response


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
