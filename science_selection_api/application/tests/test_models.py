from datetime import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from application.models import Direction, File, Competence, Universities, Education, Application, validate_draft_year, \
    ApplicationScores, Specialization, MilitaryCommissariat
from account.models import Member, Role
from utils.constants import DEFAULT_FILED_BLOCKS


class DirectionModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Direction.objects.create(name='ИВТ', description='описание')

    def test_name_max_length(self):
        direction = Direction.objects.get(id=1)
        max_length = direction._meta.get_field('name').max_length
        self.assertEquals(max_length, 128)

    def test_image_url(self):
        direction = Direction.objects.get(id=1)
        self.assertIsNone(direction.image_url)


class FileModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_role = Role.objects.create(role_name='Оператор')
        test_member = Member.objects.create(user=test_user, phone='1110001115', role=test_role)
        File.objects.create(file_name='test.docx', member=test_member)

    def test_file_name_max_length(self):
        file = File.objects.get(id=1)
        max_length = file._meta.get_field('file_name').max_length
        self.assertEquals(max_length, 128)

    def test_file_path_upload_to(self):
        file = File.objects.get(id=1)
        upload_path = file._meta.get_field('file_path').upload_to
        self.assertEquals(upload_path, 'files/%Y/%m/%d')


class CompetenceModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Competence.objects.create(name='Python')

    def test_name_max_length(self):
        competence = Competence.objects.get(id=1)
        max_length = competence._meta.get_field('name').max_length
        self.assertEquals(max_length, 128)


class UniversitiesModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Universities.objects.create(name='МЭИ')

    def test_name_max_length(self):
        uni = Universities.objects.get(id=1)
        max_length = uni._meta.get_field('name').max_length
        self.assertEquals(max_length, 256)


class ApplicationModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_role = Role.objects.create(role_name='Оператор')
        test_member = Member.objects.create(user=test_user, phone='1110001115', role=test_role)
        app = Application.objects.create(member=test_member, birth_day=datetime.strptime('18/09/19', '%d/%m/%y'),
                                         birth_place='Test', nationality='РФ', military_commissariat='Йо',
                                         group_of_health='А1', draft_year=2020, draft_season=1)
        cls.education = Education.objects.create(application=app, education_type='b', university='МЭИ', specialization='ИВТ',
                                                 avg_score=5, end_year=2020, is_ended=True, name_of_education_doc='Высшее',
                                                 theme_of_diploma='Тест')
        ApplicationScores.objects.create(application=app)

    def test_birth_place_max_length(self):
        app = Application.objects.get(id=1)
        max_length = app._meta.get_field('birth_place').max_length
        self.assertEquals(max_length, 128)

    def test_nationality_max_length(self):
        app = Application.objects.get(id=1)
        max_length = app._meta.get_field('nationality').max_length
        self.assertEquals(max_length, 128)

    def test_military_commissariat_max_length(self):
        app = Application.objects.get(id=1)
        max_length = app._meta.get_field('military_commissariat').max_length
        self.assertEquals(max_length, 128)

    def test_group_of_health_max_length(self):
        app = Application.objects.get(id=1)
        max_length = app._meta.get_field('group_of_health').max_length
        self.assertEquals(max_length, 32)

    def test_draft_year_validator(self):
        app = Application.objects.get(id=1)
        validators = app._meta.get_field('draft_year').validators
        self.assertEquals(validators, [validate_draft_year])

    def test_get_filed_blocks(self):
        app = Application.objects.get(id=1)
        filed_blocks = DEFAULT_FILED_BLOCKS
        filed_blocks.update({'Основные данные': True, 'Образование': True})
        self.assertEquals(filed_blocks, app.get_filed_blocks())

    def test_calculate_fullness(self):
        app = Application.objects.get(id=1)
        fullness = app.calculate_fullness()
        self.assertEquals(fullness, 40)

    def test_get_last_education(self):
        app = Application.objects.get(id=1)
        self.assertEquals(app.get_last_education(), ApplicationModelTest.education)

    def test_calculate_final_score(self):
        app = Application.objects.get(id=1)
        self.assertEquals(app.calculate_final_score(), 0.6)

    def test_get_draft_time(self):
        app = Application.objects.get(id=1)
        self.assertEquals(app.get_draft_time(), 'Весна 2020')


class EducationModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user = User.objects.create(username='test')
        test_role = Role.objects.create(role_name='Оператор')
        test_member = Member.objects.create(user=test_user, phone='1110001115', role=test_role)
        app = Application.objects.create(member=test_member, birth_day=datetime.strptime('18/09/19', '%d/%m/%y'),
                                         birth_place='Test', nationality='РФ', military_commissariat='Йо',
                                         group_of_health='А1', draft_year=2020, draft_season=1)
        Education.objects.create(application=app, education_type=Education.education_program[0][0], university='МЭИ',
                                 specialization='ИВТ', avg_score=5, end_year=2020, is_ended=True,
                                 name_of_education_doc='Высшее', theme_of_diploma='Тест')

    def test_university_max_length(self):
        education = Education.objects.get(id=1)
        max_length = education._meta.get_field('university').max_length
        self.assertEquals(max_length, 256)

    def test_specialization_max_length(self):
        education = Education.objects.get(id=1)
        max_length = education._meta.get_field('specialization').max_length
        self.assertEquals(max_length, 256)

    def test_name_of_education_doc_max_length(self):
        education = Education.objects.get(id=1)
        max_length = education._meta.get_field('name_of_education_doc').max_length
        self.assertEquals(max_length, 256)

    def test_theme_of_diploma_max_length(self):
        education = Education.objects.get(id=1)
        max_length = education._meta.get_field('theme_of_diploma').max_length
        self.assertEquals(max_length, 128)

    def test_check_name_uni(self):
        education = Education.objects.get(id=1)
        self.assertFalse(education.check_name_uni())

    def test_get_education_type_display(self):
        education = Education.objects.get(id=1)
        self.assertEquals(education.get_education_type_display(), Education.education_program[0][1])


class SpecializationModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Specialization.objects.create(name='Информатика и вычислительная техника')

    def test_name_max_length(self):
        spec = Specialization.objects.get(id=1)
        max_length = spec._meta.get_field('name').max_length
        self.assertEquals(max_length, 128)


class MilitaryCommissariatModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        MilitaryCommissariat.objects.create(name='Военный комиссариат города Йошкар-Ола Республики Марий Эл',
                                            subject='Республика Марий Эл', city='г.Йошкар-Ола')

    def test_name_max_length(self):
        mc = MilitaryCommissariat.objects.get(id=1)
        max_length = mc._meta.get_field('name').max_length
        self.assertEquals(max_length, 256)

    def test_subject_max_length(self):
        mc = MilitaryCommissariat.objects.get(id=1)
        max_length = mc._meta.get_field('subject').max_length
        self.assertEquals(max_length, 128)

    def test_city_max_length(self):
        mc = MilitaryCommissariat.objects.get(id=1)
        max_length = mc._meta.get_field('city').max_length
        self.assertEquals(max_length, 128)
