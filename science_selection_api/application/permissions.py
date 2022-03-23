from rest_framework import permissions

from account.models import Booking
from application.models import Application
from application.utils import is_booked_by_user


class IsMasterPermission(permissions.BasePermission):
    """ Предоставляет доступ только пользователям с ролью Master"""

    def has_permission(self, request, view):
        try:
            print(request.user.member.is_master(), 'IsMasterPermission')
            return request.user.member.is_master()
        except AttributeError:
            print(False, 'IsMasterPermission')
            return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsSlavePermission(permissions.BasePermission):
    """ Предоставляет доступ только пользователям с ролью Slave"""

    def has_permission(self, request, view):
        try:
            return request.user.member.is_slave()
        except AttributeError:
            return False


class IsApplicationOwnerPermission(permissions.BasePermission):
    """ Предоставляет доступ только хозяину анкеты"""

    def has_object_permission(self, request, view, obj):
        print(obj.member.user == request.user, 'IsApplicationOwnerPermission')
        return obj.member.user == request.user


class IsBookedOnMasterDirectionPermission(permissions.BasePermission):
    """ Предоставляет доступ мастеру, если данная заявка отобрана на его направление"""

    def has_object_permission(self, request, view, obj):
        print(is_booked_by_user(obj.pk, request.user), 'IsBookedOnMasterDirectionPermission')
        return is_booked_by_user(obj.pk, request.user)


class ApplicationIsNotFinalPermission(permissions.BasePermission):
    """ Предоставляет доступ к анкете, если она не заблокирована(is_final) """

    def has_object_permission(self, request, view, obj):
        print(not obj.is_final, 'ApplicationIsNotFinalPermission')
        return not obj.is_final


class IsNestedApplicationOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        obj = Application.objects.get(pk=view.kwargs['application_pk'])
        print(obj.member.user == request.user, 'IsApplicationOwnerPermission')
        return obj.member.user == request.user

    def has_permission(self, request, view):
        obj = Application.objects.get(pk=view.kwargs['application_pk'])
        print(obj.member.user == request.user, 'IsApplicationOwnerPermission')
        return obj.member.user == request.user


class IsNotFinalNestedApplicationPermission(permissions.BasePermission):
    """ Предоставляет доступ к анкете, если она не заблокирована(is_final) """

    def has_object_permission(self, request, view, obj):
        print(not obj.application.is_final, 'IsNotFinalNestedApplicationPermission')
        return not obj.application.is_final

    def has_permission(self, request, view):
        obj = Application.objects.get(pk=view.kwargs['application_pk'])
        print(not obj.is_final, 'IsNotFinalNestedApplicationPermission')
        return not obj.is_final


class IsNestedApplicationBookedOnMasterDirectionPermission(permissions.BasePermission):
    """ Предоставляет доступ мастеру, если данная заявка отобрана на его направление"""

    def has_object_permission(self, request, view, obj):
        print(is_booked_by_user(obj.application.pk, request.user),
              'IsNestedApplicationBookedOnMasterDirectionPermission obj')
        return is_booked_by_user(obj.application.pk, request.user)

    def has_permission(self, request, view):
        obj = Application.objects.get(pk=view.kwargs['application_pk'])
        print(is_booked_by_user(obj.pk, request.user),
              'IsNestedApplicationBookedOnMasterDirectionPermission perm')
        return is_booked_by_user(obj.pk, request.user)


class IsApplicationBookedByCurrentMasterPermission(permissions.BasePermission):
    """ Предоставляет доступ мастеру, если заявка была забронирована им"""

    def has_object_permission(self, request, view, obj):
        return obj.master == request.user.member

