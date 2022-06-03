import logging

from django.urls import reverse
from rest_framework import status

from application.tests.factories import UserFactory, RoleFactory, DirectionFactory, AffiliationFactory, MemberFactory, \
    create_uniq_application, CompetenceFactory
from rest_framework.test import APITestCase
from utils import constants as const

logging.disable(logging.FATAL)


class CompetenceTest(APITestCase):
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

        # создаем заявки
        slave_role = RoleFactory.create(role_name=const.SLAVE_ROLE_NAME)
        for i in range(4):
            create_uniq_application(slave_role, directions=DirectionFactory.create_batch(3))
        self.slave_application = create_uniq_application(slave_role, directions=DirectionFactory.create_batch(3))
        self.slave_application_main = create_uniq_application(slave_role, directions=[direction1])

        self.slave_user_without_app = UserFactory.create()
        MemberFactory.create(role=slave_role, user=self.slave_user_without_app)
        # создание компетенций
        self.competence = CompetenceFactory.create(parent_node=None,
                                                   directions=DirectionFactory.create_batch(3))
        CompetenceFactory.create_batch(6, parent_node=self.competence,
                                       directions=DirectionFactory.create_batch(3))
        self.correct_competence_data = {
            'parent_node': None,
            'directions': [direction1.id, ],
            'name': 'Программирование',
            'is_estimated': True,
        }
        self.incorrect_competence_data = {
            'parent_node': None,
            'directions': [direction.id for direction in DirectionFactory.create_batch(3)],
            'name': 'Программирование',
            'is_estimated': True,
        }

    def test_create_competence_by_unauthorized_user(self):
        """Создание компетенции неавторизованным пользователем"""
        response = self.client.post(reverse('competence-list'), data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_competence_by_slave(self):
        """Создание компетенции неавторизованным пользователем"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('competence-list'), data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_competence_by_master(self):
        """Создание компетенции неавторизованным пользователем"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('competence-list'), data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_competence_with_incorrect_directions_by_master(self):
        """Создание компетенции неавторизованным пользователем"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('competence-list'), data=self.incorrect_competence_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_competence_by_unauthorized_user(self):
        """Просмотр списка компетенций неавторизованным пользователем"""
        response = self.client.get(reverse('competence-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_competence_by_slave(self):
        """Просмотр списка компетенций неавторизованным пользователем"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('competence-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_competence_by_master(self):
        """Просмотр списка компетенций мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('competence-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_competence_by_unauthorized_user(self):
        """Просмотр списка компетенций неавторизованным пользователем"""
        response = self.client.get(reverse('competence-detail', args=(self.competence.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_competence_by_slave(self):
        """Просмотр компетенции кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('competence-detail', args=(self.competence.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_competence_by_master(self):
        """Просмотр компетенции мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('competence-detail', args=(self.competence.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
