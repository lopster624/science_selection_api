from uuid import uuid4
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.dispatch import receiver

from utils.constants import ACTIVATION_LINK, MASTER_ROLE_NAME, SLAVE_ROLE_NAME


class Role(models.Model):
    role_name = models.CharField(max_length=32, verbose_name="Название роли")

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return f'{self.role_name}'


class Affiliation(models.Model):
    direction = models.ForeignKey('application.Direction', verbose_name="Направление", on_delete=models.CASCADE,
                                  related_name='affiliation')
    company = models.IntegerField(verbose_name="Номер роты")
    platoon = models.IntegerField(verbose_name="Номер взвода")

    class Meta:
        verbose_name = "Принадлежность"
        verbose_name_plural = "Принадлежности"
        ordering = ('company', 'platoon')

    def __str__(self):
        return f'{self.company} рота, {self.platoon} взвод'


class Member(models.Model):
    class Validator:
        phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                     message="Введите корректный номер телефона формата: +79998887766")

    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, verbose_name="Роль", null=True, blank=True, on_delete=models.SET_NULL)
    father_name = models.CharField(max_length=32, verbose_name="Отчество", null=True, blank=True)
    phone = models.CharField(validators=[Validator.phone_regex], verbose_name="Телефон", max_length=17)
    affiliations = models.ManyToManyField(Affiliation, verbose_name="Принадлежность", blank=True)

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self):
        return f'{self.user.last_name} {self.user.first_name} {self.father_name}'

    def is_slave(self):
        return self.role.role_name == SLAVE_ROLE_NAME

    def is_master(self):
        return self.role.role_name == MASTER_ROLE_NAME


def create_activation_link(user):
    token = uuid4()
    ActivationLink.objects.create(user=user, token=token)
    return f'{ACTIVATION_LINK}{token}'


# @receiver(models.signals.post_save, sender=User)
# def send_link_to_mail(sender, instance, created, **kwargs):
#     """
#     Отправка письма после регистрации на почту для активации пользователя
#     """
#     if created:
#         token = uuid4()
#         ActivationLink.objects.create(user=instance, token=token)
#         # send_verification_email(instance.pk, token)  # когда будет Celery + Redis
#         send_mail('Проверка', f'{ACTIVATION_LINK}{token}', DEFAULT_FROM_EMAIL, [instance.email])


class BookingType(models.Model):
    name = models.CharField(max_length=32, verbose_name="Название бронирования")

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name = "Тип бронирования"
        verbose_name_plural = "Типы бронирования"


class Booking(models.Model):
    booking_type = models.ForeignKey(BookingType, verbose_name="Тип бронирования", on_delete=models.SET_NULL, null=True)
    master = models.ForeignKey(Member, verbose_name="Ведущий отбор", on_delete=models.CASCADE)
    slave = models.ForeignKey(Member, verbose_name="Кандидат", on_delete=models.CASCADE, related_name='candidate')
    affiliation = models.ForeignKey(Affiliation, verbose_name="Принадлежность", null=True, related_name='booking',
                                    on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"

    def __str__(self):
        return f'{self.booking_type.name} кто: {self.slave} кем: {self.master} в {self.affiliation}'


class ActivationLink(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    token = models.CharField(verbose_name="Токен", max_length=64)

    class Meta:
        verbose_name = "Ссылка активации"
        verbose_name_plural = "Ссылки активации"

    def __str__(self):
        return f'{self.user}'
