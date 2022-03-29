import logging
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from account.models import Booking
from application.models import WorkGroup, Application
from application.tests.factories import UserFactory, RoleFactory, DirectionFactory, AffiliationFactory, MemberFactory, \
    create_uniq_application, BookingTypeFactory, BookingFactory, WorkGroupFactory, create_uniq_member
from utils import constants as const

logging.disable(logging.FATAL)


class WorkGroupViewTest(APITestCase):
    def setUp(self) -> None:
        # создаем мастера
        self.master_user = UserFactory.create()
        self.master_second_user = UserFactory.create()
        self.master_role = master_role = RoleFactory.create(role_name=const.MASTER_ROLE_NAME)

        direction1 = DirectionFactory.create()
        self.main_affiliation = affiliation = AffiliationFactory.create(direction=direction1)
        self.master_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role, user=self.master_user)
        self.master_second_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role,
                                                         user=self.master_second_user)
        self.main_work_group = WorkGroupFactory(affiliation=affiliation)
        WorkGroupFactory.create_batch(3)
        self.correct_data = {'affiliation': self.main_affiliation.id,
                             'name': 'rand_group',
                             'description': 'some description'}
        slave_role = RoleFactory.create(role_name=const.SLAVE_ROLE_NAME)
        self.slave_application_main = create_uniq_application(slave_role, directions=[direction1])

    def test_work_group_list_by_correct_slave(self):
        """ Получение списка рабочих групп кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('work-groups-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_work_group_list_by_unauthorized_user(self):
        """ Получение списка рабочих групп неавторизованным пользователем"""
        response = self.client.get(reverse('work-groups-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_work_group_list_by_master(self):
        """ Получение списка рабочих групп мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('work-groups-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 1)

    def test_retrieve_work_group_by_master(self):
        """ Получение рабочей группы мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_work_group_by_unauthorized_user(self):
        """ Получение рабочей группы неавторизованным пользователем"""
        response = self.client.get(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_work_group_by_slave(self):
        """ Получение рабочей группы кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_work_group_by_unauthorized_user(self):
        """ Создание рабочей группы неавторизованным пользователем"""
        response = self.client.post(reverse('work-groups-list'), data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_work_group_by_slave(self):
        """ Создание рабочей группы неавторизованным пользователем"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('work-groups-list'), data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_work_group_by_correct_master(self):
        """ Создание рабочей группы корректным мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('work-groups-list'), data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_work_group_by_master_from_wrong_affiliation(self):
        """ Создание рабочей группы мастером с чужой принадлежностью"""
        self.client.force_login(user=self.master_user)
        another_affiliation = AffiliationFactory.create()
        response = self.client.post(reverse('work-groups-list'),
                                    data={'affiliation': another_affiliation.id, 'name': 'some_name',
                                          'description': 'some description'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_work_group_by_slave(self):
        """ Удаление рабочей группы кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.delete(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_work_group_by_unauthorized_user(self):
        """ Удаление рабочей группы неавторизованным пользователем"""
        response = self.client.delete(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_work_group_by_correct_master(self):
        """ Удаление рабочей группы корректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.delete(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_work_group_by_incorrect_master(self):
        """ Удаление рабочей группы некорректным мастером"""
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.delete(reverse('work-groups-detail', args=(self.main_work_group.id,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_work_group_by_correct_master(self):
        """ Обновление рабочей группы корректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.put(reverse('work-groups-detail', args=(self.main_work_group.id,)),
                                   data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_work_group_by_incorrect_master(self):
        """ Обновление рабочей группы некорректным мастером"""
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.put(reverse('work-groups-detail', args=(self.main_work_group.id,)),
                                   data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_work_group_by_unauthorized_user(self):
        """ Обновление рабочей группы неавторизованным пользователем"""
        response = self.client.put(reverse('work-groups-detail', args=(self.main_work_group.id,)),
                                   data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_work_group_by_slave(self):
        """ Обновление рабочей группы неавторизованным пользователем"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.put(reverse('work-groups-detail', args=(self.main_work_group.id,)),
                                   data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DownloadServiceDocumentsTest(APITestCase):
    def setUp(self) -> None:
        # создаем мастера
        self.master_user = UserFactory.create()
        self.master_second_user = UserFactory.create()
        self.master_role = master_role = RoleFactory.create(role_name=const.MASTER_ROLE_NAME)

        direction1 = DirectionFactory.create()
        self.main_affiliation = affiliation = AffiliationFactory.create(direction=direction1)
        self.master_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role, user=self.master_user)
        self.master_second_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role,
                                                         user=self.master_second_user)
        slave_role = RoleFactory.create(role_name=const.SLAVE_ROLE_NAME)
        for _ in range(10):
            create_uniq_application(slave_role, directions=[direction1])
        self.slave_application_main = create_uniq_application(slave_role, directions=[direction1])

    def test_download_service_doc_by_slave(self):
        """ Получение сервисного файла кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'candidates', 'directions': False}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_service_doc_candidates_by_master(self):
        """ Получение сервисного файла мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'candidates', 'directions': False}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_service_doc_rating_by_master(self):
        """ Получение сервисного файла мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'candidates', 'directions': False}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_service_doc_evaluation_statement_by_master(self):
        """ Получение сервисного файла мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'evaluation-statement', 'directions': False}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_service_doc_evaluation_statement_without_apps_by_master(self):
        """ Получение сервисного файла мастером при отсутствии анкет"""
        for app in Application.objects.all():
            app.delete()
        self.client.force_login(user=self.master_user)
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'evaluation-statement', 'directions': True}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_service_doc_evaluation_statement_on_all_directions_by_master(self):
        """ Получение сервисного файла мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'evaluation-statement', 'directions': True}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_service_doc_by_unauthorized_user(self):
        """ Получение сервисного файла неавторизованным пользователем"""
        response = self.client.get(
            reverse('download-file') + '?' + urlencode({'doc': 'candidates', 'directions': False}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
