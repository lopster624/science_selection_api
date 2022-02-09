from django.test import TestCase
from django.contrib.auth.models import User

from account.forms import RegisterForm


class RegisterFormTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username='test', email='test@test.ru')

    def setUp(self) -> None:
        self.form_data = {
            'phone': '+79998887755',
            'father_name': 'Тестович',
            'username': 'test2',
            'password': 'test2',
            'first_name': 'Тест',
            'last_name': 'Тестовый',
            'email': 'test2@test.ru'
        }

    def test_phone_form_data_valid(self):
        form = RegisterForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        self.form_data['phone'] = '89991112233'
        form = RegisterForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_phone_form_data_invalid(self):
        self.form_data['phone'] = '593875'
        form = RegisterForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_username_form_data_exists(self):
        self.form_data['username'] = 'test'
        form = RegisterForm(data=self.form_data)
        self.assertFalse(form.is_valid())

    def test_email_form_data_exists(self):
        self.form_data['email'] = 'test@test.ru'
        form = RegisterForm(data=self.form_data)
        self.assertFalse(form.is_valid())
