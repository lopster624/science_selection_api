from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from account.models import Affiliation
from application.models import Competence, Direction
from utils.exceptions import MasterHasNoDirectionsException


class PermissionPolicyMixin:
    """ Позволяет вьюсетам устанавливать набор разрешений для каждого метода """

    def check_permissions(self, request):
        try:
            # This line is heavily inspired from `APIView.dispatch`.
            # It returns the method associated with an endpoint.
            handler = getattr(self, request.method.lower())
        except AttributeError:
            handler = None

        if (handler and self.permission_classes_per_method and self.permission_classes_per_method.get(
                handler.__name__)):
            self.permission_classes = self.permission_classes_per_method.get(handler.__name__)
        super().check_permissions(request)


class DataApplicationMixin:
    def get_root_competences(self):
        return Competence.objects.filter(parent_node__isnull=True).prefetch_related('child', 'child__child')

    def get_master_affiliations(self):
        return Affiliation.objects.filter(member=self.request.user.member)

    def get_master_affiliations_id(self):
        return Affiliation.objects.filter(member=self.request.user.member).values_list('id', flat=True)

    def get_all_directions(self):
        return Direction.objects.all()

    def get_master_directions(self):
        return Direction.objects.filter(affiliation__in=self.get_master_affiliations()).distinct()

    def get_master_directions_id(self):
        return self.get_master_affiliations().values_list('direction__id', flat=True)

    def check_master_has_affiliation(self, affiliation_id, error_message):
        """Вызывает ошибку PermissionDenied с текстом error_message,
         если принадлежность с affiliation_id не принадлежит мастеру"""
        if isinstance(affiliation_id, int):
            affiliation_id = [affiliation_id]
        if not set(affiliation_id).issubset(set(self.get_master_affiliations().values_list('id', flat=True))):
            raise PermissionDenied(error_message)

    def get_first_master_direction_or_exception(self):
        master_directions = self.get_master_directions()
        chosen_direction = master_directions.first() if master_directions else None
        if not chosen_direction:
            raise MasterHasNoDirectionsException('У вас нет направлений для отбора.')
        return chosen_direction

    def get_first_master_affiliation_or_exception(self):
        master_affiliations = self.get_master_affiliations()
        chosen_affiliation = master_affiliations.first() if master_affiliations else None
        if not chosen_affiliation:
            raise MasterHasNoDirectionsException('У вас нет направлений для отбора.')
        return chosen_affiliation

    def get_master_direction_affiliations(self, master_affiliations):
        """
        Создает и возвращает словарь, в который помещает в качестве ключей направления, доступные мастеру, а в качестве
        значения - список принадлежностей, привязанные к данным направлениям
        :param master_affiliations: queryset принадлежностей мастера
        :return: словарь {id направления: [список всех принадлежностей данного направления]}
        """
        master_directions_affiliations = {}
        for affiliation in master_affiliations:
            old = master_directions_affiliations.pop(affiliation.direction.id, None)
            item = [*old, affiliation] if old else [affiliation]
            master_directions_affiliations.update({affiliation.direction.id: item})
        return master_directions_affiliations
