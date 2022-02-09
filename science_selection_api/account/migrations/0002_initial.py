# Generated by Django 4.0.2 on 2022-02-09 06:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='affiliation',
            name='direction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affiliation', to='application.direction', verbose_name='Направление'),
        ),
        migrations.AddField(
            model_name='activationlink',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
    ]
