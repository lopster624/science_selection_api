# Generated by Django 4.0.2 on 2022-04-13 08:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_initial'),
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ViewedApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='viewed', to='application.application', verbose_name='Заявка')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Просмотренная заявка пользователем',
                'verbose_name_plural': 'Просмотренные заявки пользователями',
            },
        ),
    ]
