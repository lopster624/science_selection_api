import logging

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from account.models import Booking
from application.tests.factories import UserFactory, RoleFactory, DirectionFactory, AffiliationFactory, MemberFactory, \
    create_uniq_application, BookingTypeFactory, BookingFactory, WorkGroupFactory, create_uniq_member
from utils import constants as const

logging.disable(logging.FATAL)


class BookingTest(APITestCase):
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
        self.slave_app_for_booking = create_uniq_application(slave_role, directions=[direction1])
        random_directions = DirectionFactory.create_batch(3)
        self.application_affiliation = AffiliationFactory.create(direction=random_directions[0])
        self.slave_application = create_uniq_application(slave_role, directions=random_directions)
        self.slave_application_main = create_uniq_application(slave_role, directions=[direction1])

        self.slave_user_without_app = UserFactory.create()
        MemberFactory.create(role=slave_role, user=self.slave_user_without_app)
        # создаем бронирование
        booked = BookingTypeFactory.create()
        in_wishlist = BookingTypeFactory.create(name=const.IN_WISHLIST)
        self.wishlist = BookingFactory.create(master=self.master_second_member,
                                              slave=self.slave_application_main.member,
                                              affiliation=self.main_affiliation, booking_type=in_wishlist)
        self.booking = BookingFactory.create(master=self.master_second_member, slave=self.slave_application_main.member,
                                             affiliation=self.main_affiliation, booking_type=booked)
        self.correct_booking_data = {'affiliation': self.main_affiliation.id}

    def test_booking_list_by_correct_slave(self):
        """ Получение списка бронирований корректным кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('booking-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_booking_list_by_incorrect_slave(self):
        """ Получение списка бронирований некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('booking-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_booking_list_by_unauthorized_user(self):
        """ Получение списка бронирований неавторизованным пользователем"""
        response = self.client.get(reverse('booking-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_booking_list_by_master(self):
        """ Получение списка бронирований мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('booking-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 1)

    def test_retrieve_booking_by_master(self):
        """ Получение бронирования мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_booking_by_unauthorized_user(self):
        """ Получение бронирования неавторизованным пользователем"""
        response = self.client.get(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_booking_by_correct_slave(self):
        """ Получение бронирования корректным кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_booking_by_incorrect_slave(self):
        """ Получение бронирования некорректным кандидатом"""
        self.client.force_login(user=self.slave_application.member.user)
        response = self.client.get(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_booking_by_unauthorized_user(self):
        """ Создание бронирования неавторизованным пользователем"""
        response = self.client.post(reverse('booking-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_booking_by_slave(self):
        """ Создание бронирования неавторизованным пользователем"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('booking-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_booking_by_correct_master(self):
        """ Создание бронирования корректным мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('booking-list', args=(self.slave_app_for_booking.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_booking_by_master_from_wrong_affiliation(self):
        """ Создание бронирования мастером, если кандидат не подавал заявку на направления мастера"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('booking-list', args=(self.slave_application.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_booking_by_master_on_wrong_affiliation(self):
        """ Создание бронирования мастером на чужую принадлежность"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('booking-list', args=(self.slave_application.id,)),
                                    data={'affiliation': self.application_affiliation.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_booking_already_booked_application(self):
        """ Создание бронирования уже забронированной заявки"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('booking-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_booking_by_slave(self):
        """ Удаление бронирования кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.delete(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_booking_by_unauthorized_user(self):
        """ Удаление бронирования неавторизованным пользователем"""
        response = self.client.delete(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_booking_by_correct_master(self):
        """ Удаление бронирования корректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.delete(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_booking_by_incorrect_master(self):
        """ Удаление бронирования некорректным мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.delete(reverse('booking-detail', args=(self.slave_application_main.id, self.booking.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # дальше идут тесты для добавление в избранное

    def test_wishlist_by_slave(self):
        """ Получение вишлиста кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('wishlist-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wishlist_by_unauthorized_user(self):
        """ Получение вишлиста неавторизованным пользователем"""
        response = self.client.get(reverse('wishlist-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wishlist_by_master(self):
        """ Получение вишлиста мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('wishlist-list', args=(self.slave_application_main.id,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) == 1)

    def test_retrieve_wishlist_by_master(self):
        """ Получение элемента вишлиста мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.get(reverse('wishlist-detail', args=(self.slave_application_main.id, self.wishlist.id)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_wishlist_by_unauthorized_user(self):
        """ Получение элемента вишлиста неавторизованным пользователем"""
        response = self.client.get(reverse('wishlist-detail', args=(self.slave_application_main.id, self.wishlist.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_wishlist_by_correct_slave(self):
        """ Получение элемента вишлиста кандидатом"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.get(reverse('wishlist-detail', args=(self.slave_application_main.id, self.wishlist.id)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_wishlist_by_unauthorized_user(self):
        """ Создание элемента вишлиста неавторизованным пользователем"""
        response = self.client.post(reverse('wishlist-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_wishlist_by_slave(self):
        """ Создание элемента вишлиста неавторизованным пользователем"""
        self.client.force_login(user=self.slave_application_main.member.user)
        response = self.client.post(reverse('wishlist-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_wishlist_by_correct_master(self):
        """ Создание элемента вишлиста корректным мастером"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('wishlist-list', args=(self.slave_app_for_booking.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_wishlist_by_master_on_wrong_affiliation(self):
        """ Создание элемента вишлиста мастером на чужую принадлежность"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('wishlist-list', args=(self.slave_application.id,)),
                                    data={'affiliation': self.application_affiliation.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_wishlist_already_booked_application(self):
        """ Создание элемента вишлиста повторно заявки"""
        self.client.force_login(user=self.master_user)
        response = self.client.post(reverse('wishlist-list', args=(self.slave_application_main.id,)),
                                    data=self.correct_booking_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_wishlist_by_correct_master(self):
        """ Удаление элемента вишлиста корректным мастером"""
        self.client.force_login(user=self.master_second_user)
        response = self.client.delete(
            reverse('wishlist-detail', args=(self.slave_application_main.id, self.wishlist.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_wishlist_by_second_correct_master(self):
        """ Удаление элемента вишлиста мастером, который не создавал ее, но имеет принадлежность записи"""
        self.client.force_login(user=self.master_user)
        response = self.client.delete(
            reverse('wishlist-detail', args=(self.slave_application_main.id, self.wishlist.id)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_wishlist_by_incorrect_master(self):
        """ Удаление элемента вишлиста некорректным мастером """
        self.client.force_login(user=create_uniq_member(self.master_role).user)
        response = self.client.delete(
            reverse('wishlist-detail', args=(self.slave_application_main.id, self.wishlist.id)))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
