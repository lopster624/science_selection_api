import logging

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from application.tests.factories import RoleFactory, MemberFactory, AffiliationFactory, DirectionFactory, UserFactory, \
    create_uniq_application, BookingTypeFactory, BookingFactory, EducationFactory, create_uniq_member
from application.utils import set_is_final
from utils import constants as const

logging.disable(logging.FATAL)


class EducationTest(APITestCase):
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

        # создаем бронирование
        BookingFactory.create(master=self.master_second_member, slave=self.slave_application_main.member,
                              affiliation=self.main_affiliation, booking_type=BookingTypeFactory.create())
        # создаем образование
        self.main_education = EducationFactory.create(application=self.slave_application_main)
        EducationFactory.create_batch(2, application=self.slave_application_main)

        self.correct_education_data = {
            'application': self.slave_application_main.pk,
            'education_type': 'b',
            'university': 'УлГТУ',
            'specialization': 'ИВТ',
            'avg_score': 4.6,
            'end_year': 2021,
            'is_ended': True,
            'name_of_education_doc': 'Диплом',
            'theme_of_diploma': 'Разработка системы'
        }

    def test_education_list_by_master(self):
        """Получение списка образований мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('educations-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_education_list_by_correct_slave(self):
        """Получение списка образований корректного кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('educations-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_education_list_by_incorrect_slave(self):
        """Получение списка образований некорректного кандидата"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('educations-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_education_list_by_unauthorized_user(self):
        """Получение списка образований неавторизованным пользователем"""
        response = self.client.get(reverse('educations-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_education_by_master(self):
        """Получение образования мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_education_by_correct_slave(self):
        """Получение образования корректного кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_education_by_incorrect_slave(self):
        """Получение образования некорректного кандидата"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_education_by_unauthorized_user(self):
        """Получение образования неавторизованным пользователем"""
        response = self.client.get(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_education_by_master(self):
        """Создание образования мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_education_with_final_application_by_correct_slave(self):
        """Создание образования для заблокированной заявки корректным кандидатом"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_education_with_final_application_by_correct_master(self):
        """Создание образования для заблокированной заявки корректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.master_second_user)
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_education_with_final_application_by_incorrect_master(self):
        """Создание образования для заблокированной заявки некорректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_education_by_correct_slave(self):
        """Создание образования корректного кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_education_by_incorrect_slave(self):
        """Создание образования некорректного кандидата"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_education_by_unauthorized_user(self):
        """Создание образования неавторизованным пользователем"""
        response = self.client.post(
            reverse('educations-list', args=(self.slave_application_main.id,)), data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_by_master(self):
        """Обновление образования мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_by_correct_slave(self):
        """Обновление образования корректного кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_by_incorrect_slave(self):
        """Обновление образования некорректного кандидата"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_by_unauthorized_user(self):
        """Обновление образования неавторизованным пользователем"""
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_with_final_application_by_correct_slave(self):
        """Обновление образования для заблокированной заявки корректным кандидатом"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_education_with_final_application_by_correct_master(self):
        """Обновление образования для заблокированной заявки корректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.master_second_user)
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_education_with_final_application_by_incorrect_master(self):
        """Обновление образования для заблокированной заявки некорректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.put(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)),
            data=self.correct_education_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_education_by_master(self):
        """Удаление образования мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_education_by_correct_slave(self):
        """Удаление образования корректного кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_education_by_incorrect_slave(self):
        """Удаление образования некорректного кандидата"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_education_by_unauthorized_user(self):
        """Удаление образования неавторизованным пользователем"""
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_education_with_final_application_by_correct_slave(self):
        """Удаление образования для заблокированной заявки корректным кандидатом"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_education_with_final_application_by_correct_master(self):
        """Удаление образования для заблокированной заявки корректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.master_second_user)
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_education_with_final_application_by_incorrect_master(self):
        """Удаление образования для заблокированной заявки некорректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.delete(
            reverse('educations-detail', args=(self.slave_application_main.id, self.main_education.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
