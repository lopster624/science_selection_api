import json
import logging
from datetime import datetime
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from application.tests.factories import UserFactory, RoleFactory, DirectionFactory, MemberFactory, AffiliationFactory, \
    ApplicationFactory
from utils import constants as const

logging.disable(logging.FATAL)


def create_uniq_application(slave_role, directions):
    """
    Создает уникальную заявку с user и member
    :param slave_role: роль slave
    :param directions: список направлений
    :return: объект созданной заявки
    """
    user = UserFactory.create()
    member = MemberFactory.create(role=slave_role, user=user)
    return ApplicationFactory.create(member=member, directions=directions)


class ApplicationsTest(APITestCase):
    def setUp(self) -> None:
        # создаем мастера
        self.master_user = UserFactory.create()
        master_role = RoleFactory.create(role_name=const.MASTER_ROLE_NAME)

        direction1 = DirectionFactory.create()
        affiliation = AffiliationFactory.create(direction=direction1)
        self.master_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role, user=self.master_user)

        # создаем заявки
        slave_role = RoleFactory.create(role_name=const.SLAVE_ROLE_NAME)
        for i in range(4):
            create_uniq_application(slave_role, directions=DirectionFactory.create_batch(3))
        self.slave_application = create_uniq_application(slave_role, directions=DirectionFactory.create_batch(3))
        self.slave_application_main = create_uniq_application(slave_role, directions=DirectionFactory.create_batch(3))

        self.slave_user_without_app = UserFactory.create()
        slave_member = MemberFactory.create(role=slave_role, user=self.slave_user_without_app)
        self.correct_application_data = {
            "birth_day": "2000-02-12",
            "birth_place": "Ульяновск",
            "nationality": "Русский",
            "military_commissariat": "Московский",
            "group_of_health": "А1",
            "draft_year": datetime.now().year + 2,
            "draft_season": 1,
            "ready_to_secret": True
        }

    def test_application_list_by_master(self):
        """Получение списка заявок мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_application_list_by_unauthorized_user(self):
        """Получение списка заявок неавторизованным пользователем"""
        response = self.client.get(reverse('application-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_application_list_by_slave(self):
        """Получение списка заявок кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('application-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_application_detail_by_master(self):
        """Получение заявки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_application_detail_by_incorrect_slave(self):
        """Получение заявки не создателем заявки"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_application_detail_by_correct_slave(self):
        """Получение списка заявок создателем заявки"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_application_detail_by_unauthorized_user(self):
        """Получение списка заявок неавторизованным пользователем"""
        response = self.client.get(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_application_by_master(self):
        """ Создание заявку мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('application-list'), data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_application_by_correct_slave(self):
        """ Создание заявку кандидатом без заявки"""
        self.client.force_login(user=self.slave_user_without_app)
        response = self.client.post(reverse('application-list'), data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_application_by_incorrect_slave(self):
        """ Создание заявку кандидатом с заявкой"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('application-list'), data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_application_by_unauthorized_user(self):
        """Создание заявки неавторизованным пользователем"""
        response = self.client.post(reverse('application-list'), data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
