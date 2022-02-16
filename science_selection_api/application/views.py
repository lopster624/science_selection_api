from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from application.models import Application, Direction
from application.serializers import ChooseDirectionSerializer, \
    ApplicationListSerializer, DirectionDetailSerializer, DirectionListSerializer, ApplicationSlaveDetailSerializer, \
    ApplicationMasterDetailSerializer
from application.utils import check_role
from utils import constants as const


class DirectionsViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset для вывода всех направлений или конкретного"""
    queryset = Direction.objects.all()
    serializers = {
        'list': DirectionListSerializer
    }
    default_serializer_class = DirectionDetailSerializer

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.default_serializer_class)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()

    master_serializers = {
        'get_chosen_direction_list': DirectionDetailSerializer,
        'set_chosen_direction_list': ChooseDirectionSerializer,
        'list': ApplicationListSerializer,
    }
    default_master_serializer_class = ApplicationMasterDetailSerializer
    slave_serializers = {
        'get_chosen_direction_list': DirectionDetailSerializer,
        'set_chosen_direction_list': ChooseDirectionSerializer,
        'list': ApplicationListSerializer,
    }
    default_slave_serializer_class = ApplicationSlaveDetailSerializer

    @action(detail=True, methods=['get'], url_path='directions')
    def get_chosen_direction_list(self, request, pk=None):
        """Отдает список всех выбранных направлений пользователя с анкетой pk=pk"""
        queryset = Direction.objects.filter(application__pk=pk)
        serializer = DirectionDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @get_chosen_direction_list.mapping.post
    def set_chosen_direction_list(self, request, pk=None):
        """Отдает список всех выбранных направлений пользователя с анкетой pk=pk"""
        serializer = ChooseDirectionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            user_app = serializer.save(pk=pk)
            return Response(user_app, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if check_role(self.request.user, const.SLAVE_ROLE_NAME):
            return self.slave_serializers.get(self.action, self.default_slave_serializer_class)
        elif check_role(self.request.user, const.MASTER_ROLE_NAME):
            return self.master_serializers.get(self.action, self.default_master_serializer_class)
        raise PermissionDenied('Доступ для пользователя без роли запрещен')
