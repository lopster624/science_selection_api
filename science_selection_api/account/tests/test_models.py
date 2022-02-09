from django.test import TestCase
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from account.models import Role, Member, BookingType, ActivationLink
from utils.constants import SLAVE_ROLE_NAME, MASTER_ROLE_NAME, BOOKED


class RoleModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Role.objects.create(role_name=SLAVE_ROLE_NAME)

    def test_role_name_max_length(self):
        role = Role.objects.get(id=1)
        max_length = role._meta.get_field('role_name').max_length
        self.assertEquals(max_length, 32)


class MemberModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_master_user = User.objects.create(username='test_master')
        test_role = Role.objects.create(role_name=SLAVE_ROLE_NAME)
        test_master_role = Role.objects.create(role_name=MASTER_ROLE_NAME)
        Member.objects.create(user=test_user, role=test_role, father_name='Тестович', phone='89998887711')
        Member.objects.create(user=test_master_user, role=test_master_role, father_name='Мастерович', phone='85556662200')

    def test_father_name_max_length(self):
        member = Member.objects.get(id=1)
        max_length = member._meta.get_field('father_name').max_length
        self.assertEquals(max_length, 32)

    def test_phone_max_length(self):
        member = Member.objects.get(id=1)
        max_length = member._meta.get_field('phone').max_length
        self.assertEquals(max_length, 17)

    def test_phone_validators(self):
        member = Member.objects.get(id=1)
        validators = member._meta.get_field('phone').validators
        for validator in validators:
            if isinstance(validator, RegexValidator):
                pattern = validator.regex.pattern
                self.assertEquals(pattern, r'^\+?1?\d{9,15}$')

    def test_is_slave(self):
        member = Member.objects.get(id=1)
        self.assertEquals(member.is_slave(), True)

    def test_is_master(self):
        member = Member.objects.get(id=2)
        self.assertEquals(member.is_master(), True)


class BookingTypeModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        BookingType.objects.create(name=BOOKED)

    def test_name_max_length(self):
        booking_type = BookingType.objects.get(id=1)
        max_length = booking_type._meta.get_field('name').max_length
        self.assertEquals(max_length, 32)


class ActivationLinkModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username='test')

    # def test_token_max_length(self):
    #     link = ActivationLink.objects.get(id=1)
    #     max_length = link._meta.get_field('token').max_length
    #     self.assertEquals(max_length, 64)
    #
    # def test_link_to_email(self):
    #     link = ActivationLink.objects.get(id=1)
    #     self.assertIsNotNone(link.token)
