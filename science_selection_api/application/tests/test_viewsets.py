import logging
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from application.models import Application, Competence
from application.tests.factories import UserFactory, RoleFactory, DirectionFactory, AffiliationFactory, MemberFactory, \
    create_uniq_application, WorkGroupFactory, create_uniq_member, CompetenceFactory, ApplicationNoteFactory
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


class DirectionsCompetencesTest(APITestCase):
    def setUp(self) -> None:
        # создаем мастера
        self.master_user = UserFactory.create()
        self.master_second_user = UserFactory.create()
        self.master_role = master_role = RoleFactory.create(role_name=const.MASTER_ROLE_NAME)
        self.main_direction = direction1 = DirectionFactory.create()
        self.main_affiliation = affiliation = AffiliationFactory.create(direction=direction1)
        self.master_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role, user=self.master_user)
        self.master_second_member = MemberFactory.create(affiliations=[AffiliationFactory.create(), ], role=master_role,
                                                         user=self.master_second_user)
        slave_role = RoleFactory.create(role_name=const.SLAVE_ROLE_NAME)
        self.slave_application_main = create_uniq_application(slave_role, directions=[direction1])
        CompetenceFactory.create_batch(10, parent_node__parent_node__parent_node__parent_node=None,
                                       directions=[direction1, ])
        self.correct_data = {'competences': [i.id for i in Competence.objects.all()][:5]}

    def test_get_competence_list_by_correct_master(self):
        """ Получение списка компетенций корректным мастером """
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

    def test_get_competence_list_by_incorrect_master(self):
        """ Получение списка компетенций некорректным мастером """
        self.client.force_login(user=self.master_second_user)
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_competence_list_by_slave(self):
        """ Получение списка компетенций кандидатом """
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_competence_list_by_unauthorized_user(self):
        """ Получение списка компетенций неавторизованным пользователем """
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_unpicked_competence_list_by_correct_master(self):
        """ Получение списка невыбранных компетенций корректным мастером """
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)) + '?' + urlencode(
            {'picked': False}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 30)

    def test_set_competence_list_by_correct_master(self):
        """ Установка списка компетенций корректным мастером """
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('direction-competences', args=(self.main_direction.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(len(response.data), 5)

    def test_set_competence_list_by_slave(self):
        """ Установка списка компетенций кандидатом """
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('direction-competences', args=(self.main_direction.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_competence_list_by_unauthorized_user(self):
        """ Установка списка компетенций кандидатом """
        response = self.client.post(reverse('direction-competences', args=(self.main_direction.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_competence_list_by_incorrect_master(self):
        """ Установка списка компетенций некорректным мастером """
        self.client.force_login(user=self.master_second_user)
        response = self.client.post(reverse('direction-competences', args=(self.main_direction.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_set_competence_list_without_data(self):
        """ Установка списка компетенций без данных"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_competence_list_with_wrong_data(self):
        """ Установка списка компетенций с неверными id"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('direction-competences', args=(self.main_direction.id,)),
                                    data={'competences': [6436346, 4234234, 321, 3123, 543]})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(reverse('direction-competences', args=(self.main_direction.id,)))
        self.assertEqual(len(response.data), 0)


class ApplicationNoteViewSetTest(APITestCase):
    def setUp(self) -> None:
        # создаем мастера
        self.master_user = UserFactory.create()
        self.master_second_user = UserFactory.create()
        self.master_role = master_role = RoleFactory.create(role_name=const.MASTER_ROLE_NAME)
        self.main_direction = direction1 = DirectionFactory.create()
        self.main_affiliation = affiliation = AffiliationFactory.create(direction=direction1)
        self.master_member = MemberFactory.create(affiliations=[affiliation, ], role=master_role,
                                                  user=self.master_user)
        second_affiliation = AffiliationFactory.create()
        self.master_second_member = MemberFactory.create(affiliations=[second_affiliation, ],
                                                         role=master_role,
                                                         user=self.master_second_user)
        slave_role = RoleFactory.create(role_name=const.SLAVE_ROLE_NAME)
        self.slave_application_main = create_uniq_application(slave_role, directions=[direction1])
        ApplicationNoteFactory.create_batch(3,
                                            application=self.slave_application_main,
                                            author=self.master_second_member,
                                            affiliations=[second_affiliation, ])
        self.app_note = ApplicationNoteFactory.create(application=self.slave_application_main,
                                                      author=self.master_member,
                                                      affiliations=[affiliation, ])
        self.correct_data = {'text': 'some_text', 'affiliations': [affiliation.id, ]}
        self.correct_update_data = {'text': 'some_new_text', 'affiliations': [affiliation.id, ]}

    def test_note_list_by_master(self):
        """Получение списка заметок мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.get(reverse('notes-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_note_list_by_slave(self):
        """Получение заметок кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('notes-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_note_list_by_unauthorized_user(self):
        """Получение списка заметок неавторизованным пользователем"""
        response = self.client.get(reverse('notes-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_note_by_correct_master(self):
        """Получение заметки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_note_by_incorrect_master(self):
        """Получение заметки некорректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.get(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_note_by_slave(self):
        """Получение заметки кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_note_by_unauthorized_user(self):
        """Получение заметки неавторизованным пользователем"""
        response = self.client.get(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note_by_master_on_incorrect_affiliation(self):
        """Создание заметки мастером на направление, не принадлежащее мастеру"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.post(reverse('notes-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_by_master_without_affiliation(self):
        """Создание заметки без направления"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.post(reverse('notes-list', args=(self.slave_application_main.id,)),
                                    data={'text': 'some_text'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_note_by_master_without_text(self):
        """Создание заметки без текста"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('notes-list', args=(self.slave_application_main.id,)),
                                    data={'affiliations': [self.main_affiliation.id, ]})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_note_by_master(self):
        """Создание заметки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('notes-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_note_by_slave(self):
        """Создание заметки кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('notes-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note_by_unauthorized_user(self):
        """Создание заметки неавторизованным пользователем"""
        response = self.client.post(reverse('notes-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_note_by_correct_master(self):
        """Обновление заметки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.put(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)),
                                   data=self.correct_update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_note_by_incorrect_master(self):
        """Обновление заметки некорректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.put(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)),
                                   data=self.correct_update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_note_for_incorrect_affiliation(self):
        """Обновление заметки с принадлежностями, не пренадлежащими мастеру"""
        self.client.force_login(user=self.master_user)
        response = self.client.put(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)),
                                   data={'text': 'text_xtexas',
                                         'affiliations': [aff.id for aff in AffiliationFactory.create_batch(3)]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_note_without_affiliation(self):
        """Обновление заметки без принадлежностей"""
        self.client.force_login(user=self.master_user)
        response = self.client.put(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)),
                                   data={'text': 'text_xtexas',
                                         'affiliations': []})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_note_by_slave(self):
        """Обновление заметки кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.put(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)),
                                   data=self.correct_update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_note_by_unauthorized_user(self):
        """Обновление заметки неавторизованным пользователем"""
        response = self.client.put(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)),
                                   data=self.correct_update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_note_by_correct_master(self):
        """Удаление заметки мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.delete(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_note_by_incorrect_master(self):
        """Удаление заметки некорректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.delete(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_destroy_note_by_slave(self):
        """Удаление заметки кандидата"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.delete(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_note_by_unauthorized_user(self):
        """Удаление заметки неавторизованным пользователем"""
        response = self.client.delete(reverse('notes-detail', args=(self.slave_application_main.id, self.app_note.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
