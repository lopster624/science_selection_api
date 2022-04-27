import logging
from datetime import datetime
from random import randint

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from application.models import Application
from application.tests.factories import UserFactory, RoleFactory, DirectionFactory, MemberFactory, AffiliationFactory, \
    BookingTypeFactory, BookingFactory, WorkGroupFactory, CompetenceFactory, create_uniq_application, \
    create_batch_competences_scores, create_uniq_member
from application.utils import set_is_final, has_application_viewed
from utils import constants as const

logging.disable(logging.FATAL)


class ApplicationsTest(APITestCase):
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
        # создаем бронирование
        booked = BookingTypeFactory.create()
        BookingFactory.create(master=self.master_second_member, slave=self.slave_application_main.member,
                              affiliation=self.main_affiliation, booking_type=booked)
        # создаем рабочую группу
        self.main_work_group = WorkGroupFactory.create(affiliation=self.main_affiliation)
        self.another_work_group = WorkGroupFactory.create(
            affiliation=AffiliationFactory.create(direction=DirectionFactory.create()))

        # создаем компетенции с оценками
        main_competence = create_batch_competences_scores(count=3,
                                                          application=self.slave_application_main)
        create_batch_competences_scores(count=10, directions=[direction1], application=self.slave_application_main,
                                        parent=main_competence.pop())
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
        self.correct_competence_data = [
            {'application': self.slave_application_main.id,
             'competence': CompetenceFactory.create(parent_node=None).id,
             'level': randint(0, 3)} for _ in range(5)
        ]

    def test_application_list_by_master(self):
        """Получение списка заявок мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results')), 6)

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

    def test_update_application_by_unauthorized_user(self):
        """Редактирование заявки неавторизованным пользователем"""
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_application_by_master(self):
        """Редактирование незаблокированной заявки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_application_by_correct_slave(self):
        """ Редактирование заявки корректным кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_application_by_incorrect_slave(self):
        """ Редактирование заявки некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_final_application_by_correct_master(self):
        """ Редактирование заблокированной заявки отобравшим мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.master_second_user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_final_application_by_another_correct_master(self):
        """ Редактирование заблокированной заявки мастером с направления, на которое забронирован кандидат"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.master_user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_final_application_by_incorrect_master(self):
        """ Редактирование заблокированной заявки некорректным мастером"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_final_application_by_unauthorized_user(self):
        """ Редактирование заблокированной заявки мастером с направления, на которое забронирован кандидат"""
        set_is_final(self.slave_application_main, True)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_final_application_by_incorrect_slave(self):
        """ Редактирование заблокированной заявки некорректным кандидатом"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_final_application_by_correct_slave(self):
        """ Редактирование заблокированной заявки корректным кандидатом"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.put(reverse('application-detail', args=(self.slave_application_main.id,)),
                                   data=self.correct_application_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_application_by_unauthorized_user(self):
        """Удаление заявки неавторизованным пользователем"""
        response = self.client.delete(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_application_by_master(self):
        """Удаление незаблокированной заявки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.delete(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_application_by_correct_slave(self):
        """ Удаление заявки корректным кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.delete(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_application_by_incorrect_slave(self):
        """ Удаление заявки некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.delete(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_application_by_admin(self):
        """ Удаление заявки администратором"""
        user = User.objects.create_superuser(username='adimn', email='ararfdsf@mail.com', password='dasfhfd34A')
        self.client.force_login(user=user)
        response = self.client.delete(reverse('application-detail', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_set_is_final_by_slave(self):
        """ Блокирование анкеты кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.patch(reverse('application-set-is-final', args=(self.slave_application_main.id,)),
                                     data={'is_final': True})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_is_final_by_incorrect_master(self):
        """ Блокирование анкеты некорректным мастером"""
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.patch(reverse('application-set-is-final', args=(self.slave_application_main.id,)),
                                     data={'is_final': True})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_is_final_by_correct_master(self):
        """ Блокирование анкеты корректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.patch(reverse('application-set-is-final', args=(self.slave_application_main.id,)),
                                     data={'is_final': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_is_final_by_correct_another_master(self):
        """ Блокирование анкеты корректным мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.patch(reverse('application-set-is-final', args=(self.slave_application_main.id,)),
                                     data={'is_final': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_chosen_direction_list_by_correct_slave(self):
        """ Получение списка направлений кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('application-get-chosen-direction-list',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_chosen_direction_list_by_incorrect_slave(self):
        """ Получение списка направлений некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('application-get-chosen-direction-list',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_chosen_direction_list_by_master(self):
        """ Получение списка направлений мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-get-chosen-direction-list',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_chosen_direction_list_by_unauthorized_user(self):
        """ Получение списка направлений неавторизованным пользователем"""
        response = self.client.get(reverse('application-get-chosen-direction-list',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_chosen_direction_list_by_incorrect_slave(self):
        """ Установка списка направлений некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.post(reverse('application-get-chosen-direction-list',
                                            args=(self.slave_application_main.id,)), data=[{'id': 1}, {'id': 2}])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_chosen_direction_list_by_master(self):
        """ Установка списка направлений мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('application-get-chosen-direction-list',
                                            args=(self.slave_application_main.id,)), data=[{'id': 1}, {'id': 2}])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_chosen_direction_list_by_unauthorized_user(self):
        """ Установка списка направлений неавторизованным пользователем"""
        response = self.client.post(reverse('application-get-chosen-direction-list',
                                            args=(self.slave_application_main.id,)), data=[{'id': 1}, {'id': 2}])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_chosen_direction_list_by_correct_slave(self):
        """Установка списка направлений кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('application-get-chosen-direction-list',
                                            args=(self.slave_application_main.id,)), data=[{'id': 1}, {'id': 2}])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_chosen_direction_list_by_correct_slave_with_final_application(self):
        """Установка списка направлений кандидатом"""
        set_is_final(self.slave_application_main, True)
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('application-get-chosen-direction-list',
                                            args=(self.slave_application_main.id,)), data=[{'id': 1}, {'id': 2}])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_application_as_word_by_incorrect_slave(self):
        """Загрузка анкеты некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('application-download-application-as-word',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_application_as_word_by_master(self):
        """Загрузка анкеты мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-download-application-as-word',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_application_as_word_by_unauthorized_user(self):
        """Загрузка анкеты неавторизованным пользователем"""
        response = self.client.get(reverse('application-download-application-as-word',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_application_as_word_by_correct_slave(self):
        """Загрузка анкеты кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('application-download-application-as-word',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_work_group_by_master(self):
        """Получение рабочей группы мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-get-work-group',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_work_group_by_unauthorized_user(self):
        """Получение рабочей группы неавторизованным пользователем"""
        response = self.client.get(reverse('application-get-work-group',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_work_group_as_word_by_slave(self):
        """Получение рабочей группы кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('application-get-work-group',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_work_group_by_another_correct_master(self):
        """Получение рабочей группы мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.get(reverse('application-get-work-group',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_work_group_by_incorrect_master(self):
        """Получение рабочей группы некорректным мастером"""
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.get(reverse('application-get-work-group',
                                           args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_work_group_by_master(self):
        """Установка рабочей группы мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': self.main_work_group.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_work_group_by_unauthorized_user(self):
        """Установка рабочей группы неавторизованным пользователем"""
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': self.main_work_group.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_work_group_as_word_by_slave(self):
        """Установка рабочей группы кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': self.main_work_group.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_work_group_by_another_correct_master(self):
        """Установка рабочей группы мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': self.main_work_group.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_work_group_by_incorrect_master(self):
        """Установка рабочей группы некорректным мастером"""
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': self.main_work_group.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_null_work_group_by_master(self):
        """Установка пустой рабочей группы мастером"""
        self.client.force_login(user=self.master_user)
        self.slave_application_main.work_group = self.main_work_group
        self.slave_application_main.save()
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': None})

        self.assertEqual(Application.objects.get(pk=self.slave_application_main.pk).work_group, None)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_incorrect_work_group_by_master(self):
        """Установка рабочей группы другого направления мастером"""
        self.client.force_login(user=self.master_user)
        self.slave_application_main.work_group = self.main_work_group
        self.slave_application_main.save()
        response = self.client.patch(reverse('application-get-work-group', args=(self.slave_application_main.id,)),
                                     data={'work_group': self.another_work_group.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_competences_list_by_unauthorized_user(self):
        """Получение списка компетенций неавторизованным пользователем """
        response = self.client.get(reverse('application-get-competences-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_competences_list_by_master(self):
        """Получение списка компетенций мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('application-get-competences-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_competences_list_by_correct_slave(self):
        """Получение списка компетенций корректным кандидатом """
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(
            reverse('application-get-competences-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_competences_list_by_incorrect_slave(self):
        """Получение списка компетенций некорректным кандидатом """
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(
            reverse('application-get-competences-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_competences_list_by_unauthorized_user(self):
        """Установка списка компетенций неавторизованным пользователем """
        response = self.client.post(reverse('application-get-competences-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_competences_list_by_master(self):
        """Установка списка компетенций мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('application-get-competences-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_competences_list_by_correct_slave(self):
        """Установка списка компетенций корректным кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(
            reverse('application-get-competences-list', args=(self.slave_application_main.id,)),
            data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_competences_list_by_incorrect_slave(self):
        """Установка списка компетенций некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.post(
            reverse('application-get-competences-list', args=(self.slave_application_main.id,)),
            data=self.correct_competence_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_application_by_master(self):
        """Просмотр заявки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('application-view-application', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(has_application_viewed(self.slave_application_main, self.master_user.member))

    def test_view_application_by_slave(self):
        """Просмотр заявки кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('application-view-application', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(has_application_viewed(self.slave_application_main, self.master_user.member))

    def test_view_application_by_unauthorized_user(self):
        """Просмотр заявки неавторизованным пользователем"""
        response = self.client.post(reverse('application-view-application', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(has_application_viewed(self.slave_application_main, self.master_user.member))
