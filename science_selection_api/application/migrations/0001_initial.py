# Generated by Django 4.0.2 on 2022-02-09 06:48

import application.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название дополнительного поля')),
            ],
            options={
                'verbose_name': 'Кастомное поле',
                'verbose_name_plural': 'Кастомные поля',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('birth_day', models.DateField(verbose_name='Дата рождения')),
                ('birth_place', models.CharField(help_text='Область, город', max_length=128, verbose_name='Место рождения')),
                ('nationality', models.CharField(max_length=128, verbose_name='Гражданство')),
                ('military_commissariat', models.CharField(max_length=128, verbose_name='Военный комиссариат')),
                ('group_of_health', models.CharField(max_length=32, verbose_name='Группа здоровья')),
                ('draft_year', models.IntegerField(validators=[application.models.validate_draft_year], verbose_name='Год призыва')),
                ('draft_season', models.IntegerField(choices=[(1, 'Весна'), (2, 'Осень')], verbose_name='Сезон призыва')),
                ('scientific_achievements', models.TextField(blank=True, help_text='Участие в конкурсах, олимпиадах, издательской деятельности, научно-практические конференции, наличие патентов на изобретения, свидетельств о регистрации программ, свидетельств о рационализаторских предложениях и т.п.', verbose_name='Научные достижения')),
                ('scholarships', models.TextField(blank=True, help_text='Наличие грантов, именных премий, именных стипендий и т.п.', verbose_name='Стипендии')),
                ('ready_to_secret', models.BooleanField(default=False, help_text='Готовность гражданина к оформлению допуска к сведениям, содержащим государственную тайну, по 3 форме', verbose_name='Готовность к секретности')),
                ('candidate_exams', models.TextField(blank=True, help_text='Наличие оформленного соискательства ученой степени и сданных экзаменов кандидатского минимума', verbose_name='Кандидатские экзамены')),
                ('sporting_achievements', models.TextField(blank=True, help_text='Наличие спортивных достижений и разрядов', verbose_name='Спортивные достижения')),
                ('hobby', models.TextField(blank=True, help_text='Увлечения и хобби', verbose_name='Хобби')),
                ('other_information', models.TextField(blank=True, verbose_name='Дополнительная информация')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('fullness', models.IntegerField(default=0, verbose_name='Процент заполненности')),
                ('final_score', models.FloatField(default=0, verbose_name='Итоговая оценка заявки')),
                ('is_final', models.BooleanField(default=False, verbose_name='Законченность анкеты')),
                ('international_articles', models.BooleanField(default=False, verbose_name='Наличие опубликованных научных статей в международных изданиях')),
                ('patents', models.BooleanField(default=False, verbose_name='Наличие патентов на изобретения и полезные модели')),
                ('vac_articles', models.BooleanField(default=False, verbose_name='Наличие опубликованных научных статей в научных изданиях, рекомендуемых ВАК')),
                ('innovation_proposals', models.BooleanField(default=False, verbose_name='Наличие свидетельств нарационализаторские предложения')),
                ('rinc_articles', models.BooleanField(default=False, verbose_name='Наличие опубликованных научных статей в изданиях РИНЦ')),
                ('evm_register', models.BooleanField(default=False, verbose_name='Наличие свидетельств о регистрации баз данных и программ для ЭВМ')),
                ('international_olympics', models.BooleanField(default=False, verbose_name='Наличие призовых мест на международных олимпиадах')),
                ('president_scholarship', models.BooleanField(default=False, verbose_name='Стипендиат государственных стипендий Президента Российской Федерации')),
                ('country_olympics', models.BooleanField(default=False, verbose_name='Наличие призовых мест на олимпиадах всероссийского уровня')),
                ('government_scholarship', models.BooleanField(default=False, verbose_name='Стипендиат государственных стипендий Правительства Российской Федерации')),
                ('military_grants', models.BooleanField(default=False, verbose_name='Обладательгрантов по научным работам, имеющим прикладное значение для Минобороны России, которые подтверждены органами военного управления')),
                ('region_olympics', models.BooleanField(default=False, verbose_name='Наличие призовых мест на олимпиадах областного уровня')),
                ('city_olympics', models.BooleanField(default=False, verbose_name='Наличие призовых мест на олимпиадах на уровне города')),
                ('commercial_experience', models.BooleanField(default=False, verbose_name='Наличие опыта работы по специальности в коммерческих предприятиях (не менее 1 года)')),
                ('opk_experience', models.BooleanField(default=False, verbose_name='Наличие опыта работы по специальности на предприятиях ОПК (не менее 1 года)')),
                ('science_experience', models.BooleanField(default=False, verbose_name='Наличие опыта работы по специальности в научных организациях (подразделениях) на должностях научных сотрудников (не менее 1 года)')),
                ('military_sport_achievements', models.BooleanField(default=False, verbose_name='Наличие спортивных достижений по военно-прикладным видам спорта, в том числе выполнение нормативов ГТО')),
                ('sport_achievements', models.BooleanField(default=False, verbose_name='Наличие спортивных достижений по иным видам спорта')),
                ('compliance_prior_direction', models.BooleanField(default=False, verbose_name='Соответствие приоритетному направлению высшего образования')),
                ('compliance_additional_direction', models.BooleanField(default=False, verbose_name='Соответствие дополнительному направлению высшего образования')),
                ('postgraduate_additional_direction', models.BooleanField(default=False, verbose_name='Наличие ученой степени по специальности, не соответствующей профилю научных исследований научной роты')),
                ('postgraduate_prior_direction', models.BooleanField(default=False, verbose_name='Наличие ученой степени по специальности, соответствующей профилю научных исследований научной роты')),
            ],
            options={
                'verbose_name': 'Заявка',
                'verbose_name_plural': 'Заявки',
                'ordering': ['create_date'],
            },
        ),
        migrations.CreateModel(
            name='Direction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Наименование направления')),
                ('description', models.TextField(verbose_name='Описание направления')),
                ('image', models.ImageField(blank=True, null=True, upload_to='images/', verbose_name='Изображения')),
            ],
            options={
                'verbose_name': 'Направление',
                'verbose_name_plural': 'Направления',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MilitaryCommissariat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Название коммисариата')),
                ('subject', models.CharField(max_length=128, verbose_name='Субъект')),
                ('city', models.CharField(max_length=128, verbose_name='Город')),
            ],
            options={
                'verbose_name': 'Военный комиссариат',
                'verbose_name_plural': 'Военные комиссариаты',
            },
        ),
        migrations.CreateModel(
            name='Specialization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название специальности')),
            ],
            options={
                'verbose_name': 'Специальность',
                'verbose_name_plural': 'Специальности',
            },
        ),
        migrations.CreateModel(
            name='Universities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Название университета')),
                ('rating_place', models.IntegerField(blank=True, null=True, verbose_name='Рейтинговое место')),
            ],
            options={
                'verbose_name': 'Университет',
                'verbose_name_plural': 'Университеты',
            },
        ),
        migrations.CreateModel(
            name='WorkGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='Название рабочей группы')),
                ('description', models.TextField(blank=True, verbose_name='Описание рабочей группы')),
                ('affiliation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_group', to='account.affiliation', verbose_name='Принадлежность')),
            ],
            options={
                'verbose_name': 'Рабочая группа',
                'verbose_name_plural': 'Рабочие группы',
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.FileField(upload_to='files/%Y/%m/%d', verbose_name='Путь к файлу')),
                ('file_name', models.CharField(blank=True, max_length=128, verbose_name='Имя файла')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления файла')),
                ('is_template', models.BooleanField(default=False, verbose_name='Шаблон')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Вложение',
                'verbose_name_plural': 'Вложения',
            },
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('education_type', models.CharField(choices=[('b', 'Бакалавриат'), ('m', 'Магистратура'), ('a', 'Аспирантура'), ('s', 'Специалитет')], max_length=1, verbose_name='Программа')),
                ('university', models.CharField(max_length=256, verbose_name='Университет')),
                ('specialization', models.CharField(max_length=256, verbose_name='Специальность')),
                ('avg_score', models.FloatField(validators=[application.models.validate_avg_score], verbose_name='Средний балл')),
                ('end_year', models.IntegerField(verbose_name='Год окончания')),
                ('is_ended', models.BooleanField(default=False, verbose_name='Окончено')),
                ('name_of_education_doc', models.CharField(blank=True, max_length=256, verbose_name='Наименование документа об образовании')),
                ('theme_of_diploma', models.CharField(max_length=128, verbose_name='Тема диплома')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='education', to='application.application', verbose_name='Заявка')),
            ],
            options={
                'verbose_name': 'Образование',
                'verbose_name_plural': 'Образование',
                'ordering': ['-end_year'],
            },
        ),
        migrations.CreateModel(
            name='Competence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='Название компетенции')),
                ('is_estimated', models.BooleanField(default=False, verbose_name='Есть оценка')),
                ('directions', models.ManyToManyField(blank=True, to='application.Direction', verbose_name='Название направления')),
                ('parent_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child', to='application.competence', verbose_name='Компетенция-родитель')),
            ],
            options={
                'verbose_name': 'Компетенция',
                'verbose_name_plural': 'Компетенции',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ApplicationScores',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('a1', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Склонность к научной деятельности"')),
                ('a2', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Средний балл диплома о высшем образовании"')),
                ('a3', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Соответствие направления подготовки высшего образования кандидата профилю научных исследований,выполняемых соответствующей научной ротой"')),
                ('a4', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Результативность образовательной деятельности"')),
                ('a5', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Подготовка по программе аспирантуры и наличие ученой степени"')),
                ('a6', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Опыт работы по профилю научных исследований, выполняемых соответствующей научной ротой"')),
                ('a7', models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Мотивация к военной службе"')),
                ('application', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='application.application', verbose_name='Заявка')),
            ],
            options={
                'verbose_name': 'Оценки кандидата',
                'verbose_name_plural': 'Оценки кандидата',
            },
        ),
        migrations.CreateModel(
            name='ApplicationNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(blank=True, verbose_name='Текст заметки')),
                ('affiliations', models.ManyToManyField(blank=True, to='account.Affiliation', verbose_name='Принадлежность')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='application.application', verbose_name='Анкета')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.member', verbose_name='Автор заметки')),
            ],
            options={
                'verbose_name': 'Заметка об анкете',
                'verbose_name_plural': 'Заметки об анкетах',
            },
        ),
        migrations.CreateModel(
            name='ApplicationCompetencies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(choices=[(0, 'не владеете компетенцией'), (1, 'уровнень базовых знаний, лабораторных работ вузовского курса'), (2, 'уровнень, позволяющий принимать участие в реальных проектах, конкурсах и т.п.'), (3, 'уровнень, позволяющий давать обоснованные рекомендации по совершенствованию компетенции разработчикам данной компетенции')])),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='app_competence', to='application.application')),
                ('competence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competence_value', to='application.competence')),
            ],
            options={
                'verbose_name': 'Выбранная компетенция',
                'verbose_name_plural': 'Выбранные компетенции',
            },
        ),
        migrations.AddField(
            model_name='application',
            name='competencies',
            field=models.ManyToManyField(blank=True, through='application.ApplicationCompetencies', to='application.Competence', verbose_name='Выбранные компетенции'),
        ),
        migrations.AddField(
            model_name='application',
            name='directions',
            field=models.ManyToManyField(blank=True, related_name='application', to='application.Direction', verbose_name='Выбранные направления'),
        ),
        migrations.AddField(
            model_name='application',
            name='member',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='application', to='account.member', verbose_name='Пользователь'),
        ),
        migrations.AddField(
            model_name='application',
            name='work_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='application', to='application.workgroup', verbose_name='Рабочая группа'),
        ),
        migrations.CreateModel(
            name='AdditionFieldApp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField(verbose_name='Значение дополнительного поля')),
                ('addition_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.additionfield', verbose_name='Название доп поля')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.application', verbose_name='Заявка')),
            ],
            options={
                'verbose_name': 'Значение кастомного поля',
                'verbose_name_plural': 'Значения кастомных полей',
            },
        ),
    ]
