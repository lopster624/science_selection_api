import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from utils import constants as const
from account.models import Member, Affiliation


def validate_draft_year(value: int):
    if value < datetime.date.today().year:
        raise ValidationError(_(f'Год призыва {value} раньше текущего'))


class WorkGroup(models.Model):
    """Рабочая группа, в которую происходит распрежедение забронированных заявок"""
    name = models.CharField(max_length=256, verbose_name='Название рабочей группы')
    affiliation = models.ForeignKey(Affiliation, verbose_name="Принадлежность", related_name='work_group',
                                    on_delete=models.CASCADE)
    description = models.TextField(verbose_name='Описание рабочей группы', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Рабочая группа'
        verbose_name_plural = 'Рабочие группы'


class Application(models.Model):
    """Заявка кандидата в операторы"""
    season = [
        (1, 'Весна'),
        (2, 'Осень')
    ]
    hidden_fields = ['compliance_prior_direction', 'compliance_additional_direction',
                     'postgraduate_additional_direction', 'postgraduate_prior_direction']

    member = models.OneToOneField(Member, on_delete=models.CASCADE, verbose_name='Пользователь',
                                  related_name='application')
    competencies = models.ManyToManyField('Competence', verbose_name='Выбранные компетенции',
                                          through='ApplicationCompetencies', blank=True)
    directions = models.ManyToManyField('Direction', verbose_name='Выбранные направления', blank=True,
                                        related_name='application')
    birth_day = models.DateField(verbose_name='Дата рождения')
    birth_place = models.CharField(max_length=128, verbose_name='Место рождения', help_text='Область, город')
    nationality = models.CharField(max_length=128, verbose_name='Гражданство')
    military_commissariat = models.CharField(max_length=128, verbose_name='Военный комиссариат')
    group_of_health = models.CharField(max_length=32, verbose_name='Группа здоровья')
    draft_year = models.IntegerField(verbose_name='Год призыва', validators=[validate_draft_year])
    draft_season = models.IntegerField(choices=season, verbose_name='Сезон призыва')
    scientific_achievements = models.TextField(blank=True, verbose_name='Научные достижения',
                                               help_text='Участие в конкурсах, олимпиадах, издательской деятельности, '
                                                         'научно-практические конференции, наличие патентов на изобретения, '
                                                         'свидетельств о регистрации программ, свидетельств о рационализаторских предложениях и т.п.')
    scholarships = models.TextField(blank=True, verbose_name='Стипендии',
                                    help_text='Наличие грантов, именных премий, именных стипендий и т.п.')
    ready_to_secret = models.BooleanField(default=False, verbose_name='Готовность к секретности',
                                          help_text='Готовность гражданина к оформлению допуска к сведениям, содержащим государственную тайну, по 3 форме')
    candidate_exams = models.TextField(blank=True, verbose_name='Кандидатские экзамены',
                                       help_text='Наличие оформленного соискательства ученой степени и сданных экзаменов кандидатского минимума')
    sporting_achievements = models.TextField(blank=True, verbose_name='Спортивные достижения',
                                             help_text='Наличие спортивных достижений и разрядов')
    hobby = models.TextField(blank=True, verbose_name='Хобби', help_text='Увлечения и хобби')
    other_information = models.TextField(blank=True, verbose_name='Дополнительная информация')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    fullness = models.IntegerField(default=0, verbose_name='Процент заполненности')
    final_score = models.FloatField(default=0, verbose_name='Итоговая оценка заявки')
    is_final = models.BooleanField(default=False, verbose_name='Законченность анкеты')
    work_group = models.ForeignKey(WorkGroup, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Рабочая группа",
                                   related_name='application')
    # дальше идут новые поля для калькулятора
    international_articles = models.BooleanField(default=False,
                                                 verbose_name="Наличие опубликованных научных статей в международных изданиях")
    patents = models.BooleanField(default=False, verbose_name="Наличие патентов на изобретения и полезные модели")
    vac_articles = models.BooleanField(default=False,
                                       verbose_name="Наличие опубликованных научных статей в научных изданиях, рекомендуемых ВАК")
    innovation_proposals = models.BooleanField(default=False,
                                               verbose_name="Наличие свидетельств нарационализаторские предложения")
    rinc_articles = models.BooleanField(default=False,
                                        verbose_name="Наличие опубликованных научных статей в изданиях РИНЦ")
    evm_register = models.BooleanField(default=False,
                                       verbose_name="Наличие свидетельств о регистрации баз данных и программ для ЭВМ")
    international_olympics = models.BooleanField(default=False,
                                                 verbose_name="Наличие призовых мест на международных олимпиадах")
    president_scholarship = models.BooleanField(default=False,
                                                verbose_name="Стипендиат государственных стипендий Президента Российской Федерации")
    country_olympics = models.BooleanField(default=False,
                                           verbose_name="Наличие призовых мест на олимпиадах всероссийского уровня")
    government_scholarship = models.BooleanField(default=False,
                                                 verbose_name="Стипендиат государственных стипендий Правительства Российской Федерации")
    military_grants = models.BooleanField(default=False,
                                          verbose_name="Обладательгрантов по научным работам, имеющим прикладное значение для Минобороны России, которые подтверждены органами военного управления")
    region_olympics = models.BooleanField(default=False,
                                          verbose_name="Наличие призовых мест на олимпиадах областного уровня")
    city_olympics = models.BooleanField(default=False,
                                        verbose_name="Наличие призовых мест на олимпиадах на уровне города")
    commercial_experience = models.BooleanField(default=False,
                                                verbose_name="Наличие опыта работы по специальности в коммерческих предприятиях (не менее 1 года)")
    opk_experience = models.BooleanField(default=False,
                                         verbose_name="Наличие опыта работы по специальности на предприятиях ОПК (не менее 1 года)")
    science_experience = models.BooleanField(default=False,
                                             verbose_name="Наличие опыта работы по специальности в научных организациях (подразделениях) на должностях научных сотрудников (не менее 1 года)")
    military_sport_achievements = models.BooleanField(default=False,
                                                      verbose_name="Наличие спортивных достижений по военно-прикладным видам спорта, в том числе выполнение нормативов ГТО")

    sport_achievements = models.BooleanField(default=False,
                                             verbose_name="Наличие спортивных достижений по иным видам спорта")

    # поля только для мастера
    compliance_prior_direction = models.BooleanField(default=False,
                                                     verbose_name="Соответствие приоритетному направлению высшего образования")
    compliance_additional_direction = models.BooleanField(default=False,
                                                          verbose_name="Соответствие дополнительному направлению высшего образования")
    postgraduate_additional_direction = models.BooleanField(default=False,
                                                            verbose_name="Наличие ученой степени по специальности, не соответствующей профилю научных исследований научной роты")
    postgraduate_prior_direction = models.BooleanField(default=False,
                                                       verbose_name="Наличие ученой степени по специальности, соответствующей профилю научных исследований научной роты")

    class Meta:
        ordering = ['create_date']
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def get_filed_blocks(self):
        return {
            'Основные данные': True,
            'Образование': self.education.all().exists(),
            'Направления': self.directions.all().exists(),
            'Компетенции': self.competencies.all().exists(),
            'Загруженные файлы': File.objects.filter(member=self.member).exists(),
        }

    def get_last_education(self):
        """
        Получение последнего образования
        :return: объект Education
        """
        return self.education.all().order_by('-end_year').first()

    def calculate_fullness(self) -> int:
        """
        Подсчет заполненности анкеты
        :return: значение заполненности в %
        """
        filed_blocks = self.get_filed_blocks()
        fullness = [v for k, v in filed_blocks.items() if v]
        return int(len(fullness) / len(filed_blocks) * 100)

    def calculate_final_score(self) -> float:
        """
        Подсчет рейтингового балла заявки оператора по формуле
        :return: рассчитание значение
        """
        self.scores.a1 = round(int(self.international_articles) * const.INTERNATIONAL_ARTICLES_SCORE + int(
            self.patents) * const.PATENTS_SCORE + int(self.vac_articles) * const.VAC_ARTICLES_SCORE + int(
            self.innovation_proposals) * const.INNOVATION_PROPOSALS_SCORE + int(
            self.rinc_articles) * const.RINC_ARTICLES_SCORE + int(self.evm_register) * const.EVM_REGISTER_SCORE, 2)
        last_education = self.get_last_education()
        if last_education:
            if last_education.education_type == 'b':
                score = round(last_education.avg_score * const.BACHELOR_COEF, 2)
            else:
                score = round(last_education.avg_score * const.SPECIAL_AND_MORE_COEF, 2)
            self.scores.a2 = score
        self.scores.a3 = round(int(self.compliance_prior_direction) * const.COMPLIANCE_PRIOR_DIRECTION_SCORE + int(
            self.compliance_additional_direction) * const.COMPLIANCE_ADDITIONAL_DIRECTION_SCORE, 2)
        self.scores.a4 = round(int(self.international_olympics) * const.INTERNATIONAL_OLYMPICS_SCORE + int(
            self.president_scholarship) * const.PRESIDENT_SCHOLARSHIP_SCORE + int(
            self.country_olympics) * const.COUNTRY_OLYMPICS_SCORE + int(
            self.government_scholarship) * const.GOVERNMENT_SCHOLARSHIP_SCORE + int(
            self.military_grants) * const.MILITARY_GRANTS_SCORE + int(
            self.region_olympics) * const.REGION_OLYMPICS_SCORE + int(self.city_olympics) * const.CITY_OLYMPICS_SCORE,
                               2)
        if self.education.filter(education_type=Education.education_program[2][0], is_ended=True).exists():
            self.scores.a5 = round(const.POSTGRADUATE_ENDED_SCORE + int(
                self.postgraduate_prior_direction) * const.POSTGRADUATE_PRIOR_DIRECTION_SCORE + int(
                self.compliance_additional_direction) * const.POSTGRADUATE_ADDITIONAL_DIRECTION_SCORE, 2)
        self.scores.a6 = round(int(self.science_experience) * const.SCIENCE_EXPERIENCE_SCORE + int(
            self.opk_experience) * const.OPK_EXPERIENCE_SCORE + int(
            self.commercial_experience) * const.COMMERCIAL_EXPERIENCE_SCORE, 2)
        self.scores.a7 = round(int(self.military_sport_achievements) * const.MILITARY_SPORT_ACHIEVEMENTS_SCORE + int(
            self.sport_achievements) * const.SPORT_ACHIEVEMENTS_SCORE, 2)
        self.scores.save()
        return round(self.scores.a1 * const.MEANING_COEFFICIENTS['k1'] + self.scores.a2 * const.MEANING_COEFFICIENTS[
            'k2'] + self.scores.a3 * const.MEANING_COEFFICIENTS['k3'] + self.scores.a4 * const.MEANING_COEFFICIENTS[
                         'k4'] + self.scores.a5 * const.MEANING_COEFFICIENTS['k5'] + self.scores.a6 * \
                     const.MEANING_COEFFICIENTS['k6'] + self.scores.a7 * const.MEANING_COEFFICIENTS['k7'], 2)

    def get_draft_time(self):
        return f'{self.season[self.draft_season - 1][1]} {self.draft_year}'

    def update_scores(self, *args, **kwargs):
        self.fullness = self.calculate_fullness()
        if not ApplicationScores.objects.filter(application=self).exists():
            ApplicationScores(application=self).save()
        self.final_score = self.calculate_final_score()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.member.user.first_name} {self.member.user.last_name}'


def validate_avg_score(value: float):
    if value < const.MINIMUM_SCORE or value > const.MAX_SCORE:
        raise ValidationError(_(f'Некорректный средний балл: {value}'))


class Education(models.Model):
    """Образование, указанное в заявке кандидата"""
    education_program = [
        ('b', 'Бакалавриат'),
        ('m', 'Магистратура'),
        ('a', 'Аспирантура'),
        ('s', 'Специалитет'),
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Заявка',
                                    related_name='education')
    education_type = models.CharField(choices=education_program, max_length=1, verbose_name='Программа')
    university = models.CharField(max_length=256, verbose_name='Университет')
    specialization = models.CharField(max_length=256, verbose_name='Специальность')
    avg_score = models.FloatField(verbose_name='Средний балл', validators=[validate_avg_score])
    end_year = models.IntegerField(verbose_name='Год окончания')
    is_ended = models.BooleanField(default=False, verbose_name='Окончено')
    name_of_education_doc = models.CharField(max_length=256, verbose_name='Наименование документа об образовании',
                                             blank=True)
    theme_of_diploma = models.CharField(max_length=128, verbose_name='Тема диплома')

    def __str__(self):
        return f'{self.application.member.user.first_name} {self.application.member.user.last_name}: {self.get_education_type_display()}'

    def check_name_uni(self):
        return True if Universities.objects.filter(name=self.university) else False

    def get_education_type_display(self):
        return next(name for ed_type, name in self.education_program if ed_type == self.education_type)

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"
        ordering = ['-end_year']


class Direction(models.Model):
    """Направление работы"""
    name = models.CharField(max_length=128, verbose_name='Наименование направления')
    description = models.TextField(verbose_name='Описание направления')
    image = models.ImageField(upload_to='images/', blank=True, null=True, verbose_name='Изображения')

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Направление"
        verbose_name_plural = "Направления"


class File(models.Model):
    """Файл, загружаемый пользователем на сервер в качестве вложения"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='Пользователь')
    file_path = models.FileField(upload_to='files/%Y/%m/%d', verbose_name='Путь к файлу')
    file_name = models.CharField(max_length=128, verbose_name='Имя файла', blank=True)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления файла')
    is_template = models.BooleanField(default=False, verbose_name='Шаблон')

    def __str__(self):
        return self.file_name

    class Meta:
        verbose_name = "Вложение"
        verbose_name_plural = "Вложения"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.member.is_slave() and hasattr(self.member, 'application'):
            self.member.application.update_scores(update_fields=['fullness', 'final_score'])


class AdditionField(models.Model):
    """Дополнительное поле, которое необходимо заполнить в заявке"""
    name = models.CharField(max_length=128, verbose_name='Название дополнительного поля')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Кастомное поле"
        verbose_name_plural = "Кастомные поля"
        ordering = ['name']


class AdditionFieldApp(models.Model):
    """Значение заполненного дополнительного поля в заявке"""
    addition_field = models.ForeignKey(AdditionField, on_delete=models.CASCADE, verbose_name='Название доп поля', )
    application = models.ForeignKey(Application, on_delete=models.CASCADE, verbose_name='Заявка')
    value = models.TextField(verbose_name='Значение дополнительного поля')

    class Meta:
        verbose_name = "Значение кастомного поля"
        verbose_name_plural = "Значения кастомных полей"

    def __str__(self):
        return self.addition_field.name


class Competence(models.Model):
    parent_node = models.ForeignKey('self', on_delete=models.CASCADE, verbose_name='Компетенция-родитель', null=True,
                                    blank=True, related_name='child')
    directions = models.ManyToManyField(Direction, verbose_name='Название направления', blank=True)
    name = models.CharField(max_length=128, verbose_name='Название компетенции')
    is_estimated = models.BooleanField(default=False, verbose_name='Есть оценка')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Компетенция"
        verbose_name_plural = "Компетенции"
        ordering = ['name']


class ApplicationCompetencies(models.Model):
    competence_levels = [
        (0, 'не владеете компетенцией'),
        (1, 'уровнень базовых знаний, лабораторных работ вузовского курса'),
        (2, 'уровнень, позволяющий принимать участие в реальных проектах, конкурсах и т.п.'),
        (3,
         'уровнень, позволяющий давать обоснованные рекомендации по совершенствованию компетенции разработчикам данной компетенции')
    ]
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='app_competence')
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='competence_value')
    level = models.IntegerField(choices=competence_levels)

    class Meta:
        verbose_name = "Выбранная компетенция"
        verbose_name_plural = "Выбранные компетенции"

    def __str__(self):
        return f'{self.application.member.user.first_name}: {self.competence.name}'


class Universities(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название университета', )
    rating_place = models.IntegerField(verbose_name='Рейтинговое место', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Университет'
        verbose_name_plural = 'Университеты'


class ApplicationNote(models.Model):
    application = models.ForeignKey(Application, verbose_name='Анкета', on_delete=models.CASCADE, related_name='notes')
    affiliations = models.ManyToManyField(Affiliation, verbose_name="Принадлежность", blank=True)
    author = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name='Автор заметки')
    text = models.TextField(blank=True, verbose_name='Текст заметки')

    class Meta:
        verbose_name = "Заметка об анкете"
        verbose_name_plural = "Заметки об анкетах"

    def __str__(self):
        return f'{self.text}'


class ApplicationScores(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, verbose_name='Заявка',
                                       related_name='scores')
    # поля без форм
    a1 = models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Склонность к научной деятельности"')
    a2 = models.FloatField(default=0.0,
                           verbose_name='Оценка кандидата по критерию "Средний балл диплома о высшем образовании"')
    a3 = models.FloatField(default=0.0,
                           verbose_name='Оценка кандидата по критерию "Соответствие направления подготовки высшего образования кандидата профилю научных исследований,выполняемых соответствующей научной ротой"')
    a4 = models.FloatField(default=0.0,
                           verbose_name='Оценка кандидата по критерию "Результативность образовательной деятельности"')
    a5 = models.FloatField(default=0.0,
                           verbose_name='Оценка кандидата по критерию "Подготовка по программе аспирантуры и наличие ученой степени"')
    a6 = models.FloatField(default=0.0,
                           verbose_name='Оценка кандидата по критерию "Опыт работы по профилю научных исследований, выполняемых соответствующей научной ротой"')
    a7 = models.FloatField(default=0.0, verbose_name='Оценка кандидата по критерию "Мотивация к военной службе"')

    class Meta:
        verbose_name = "Оценки кандидата"
        verbose_name_plural = "Оценки кандидата"

    def __str__(self):
        return f'{self.application}'


class MilitaryCommissariat(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название коммисариата', )
    subject = models.CharField(max_length=128, verbose_name='Субъект', )
    city = models.CharField(max_length=128, verbose_name='Город')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Военный комиссариат'
        verbose_name_plural = 'Военные комиссариаты'


class Specialization(models.Model):
    name = models.CharField(max_length=128, verbose_name='Название специальности', )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'
