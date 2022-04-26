from datetime import datetime

import factory
from django.contrib.auth.models import User
from factory import post_generation
from factory.django import DjangoModelFactory

from account.models import Member, Role, Affiliation, BookingType, Booking
from application.models import Application, Direction, WorkGroup, Competence, ApplicationCompetencies, Education, \
    ApplicationNote, File
from utils.constants import BOOKED


def create_uniq_application(slave_role, directions):
    """
    Создает уникальную заявку с user и member
    :param slave_role: роль slave
    :param directions: список направлений
    :return: объект созданной заявки
    """
    user = UserFactory.create()
    member = MemberFactory.create(role=slave_role, user=user)
    return ApplicationFactory.create(member=member, directions=directions)


def create_uniq_member(role):
    """
    создает уникального member'а
    :param role: объект роли
    :return: экземляр Member
    """
    affiliation = AffiliationFactory.create(direction=DirectionFactory.create())
    return MemberFactory.create(affiliations=[affiliation, ], role=role,
                                user=UserFactory.create())


def create_batch_competences_scores(count, application, directions=None, parent=None):
    """
    Создает несколько уникальных компетенций и оценок компетенций
    :param count: количество создаваемых компетенций
    :param application: экземпляр заявки
    :param directions: список направлений компетенций
    :param parent: компетенция-родитель
    :return: список созданных компетенций
    """
    competences = []
    for _ in range(count):
        competence = CompetenceFactory.create(parent_node=parent,
                                              directions=directions or DirectionFactory.create_batch(3))
        competences.append(competence)
        ApplicationCompetenciesFactory.create(application=application, competence=competence)
    return competences


class RoleFactory(DjangoModelFactory):
    class Meta:
        model = Role

    role_name = factory.Faker('first_name')


class DirectionFactory(DjangoModelFactory):
    class Meta:
        model = Direction

    name = factory.Faker('word')
    description = factory.Faker('sentence')


class AffiliationFactory(DjangoModelFactory):
    class Meta:
        model = Affiliation

    direction = factory.SubFactory(DirectionFactory)
    company = factory.Faker('random_int')
    platoon = factory.Faker('random_int')


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    password = factory.Faker('password')


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = Member

    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)
    father_name = factory.Faker('first_name')
    phone = factory.Faker('phone_number')

    @post_generation
    def affiliations(self, create, value, **kwargs):
        if not create:
            return
        if value:
            self.affiliations.set(value)


class WorkGroupFactory(DjangoModelFactory):
    class Meta:
        model = WorkGroup

    name = factory.Faker('word')
    affiliation = factory.SubFactory(AffiliationFactory)
    description = factory.Faker('sentence')


class BookingTypeFactory(DjangoModelFactory):
    class Meta:
        model = BookingType

    name = BOOKED


class BookingFactory(DjangoModelFactory):
    class Meta:
        model = Booking

    booking_type = factory.SubFactory(BookingTypeFactory)
    master = factory.SubFactory(MemberFactory)
    slave = factory.SubFactory(MemberFactory)
    affiliation = factory.SubFactory(AffiliationFactory)


class ApplicationFactory(DjangoModelFactory):
    class Meta:
        model = Application

    member = factory.SubFactory(MemberFactory)
    # competencies = models.ManyToManyField
    birth_day = factory.Faker('date_of_birth')
    birth_place = factory.Faker('city')
    nationality = factory.Faker('country')
    military_commissariat = factory.Faker('city')
    group_of_health = factory.Faker('word')
    draft_year = factory.Faker('pyint', min_value=datetime.now().year + 1, max_value=datetime.now().year + 10)
    draft_season = factory.Faker('pyint', min_value=1, max_value=2)
    scientific_achievements = factory.Faker('sentence')
    scholarships = factory.Faker('sentence')
    ready_to_secret = factory.Faker('boolean')
    candidate_exams = factory.Faker('sentence')
    sporting_achievements = factory.Faker('sentence')
    hobby = factory.Faker('sentence')
    other_information = factory.Faker('sentence')
    is_final = False
    international_articles = factory.Faker('boolean')
    patents = factory.Faker('boolean')
    vac_articles = factory.Faker('boolean')
    innovation_proposals = factory.Faker('boolean')
    rinc_articles = factory.Faker('boolean')
    evm_register = factory.Faker('boolean')
    international_olympics = factory.Faker('boolean')
    president_scholarship = factory.Faker('boolean')
    country_olympics = factory.Faker('boolean')
    government_scholarship = factory.Faker('boolean')
    military_grants = factory.Faker('boolean')
    region_olympics = factory.Faker('boolean')
    city_olympics = factory.Faker('boolean')
    commercial_experience = factory.Faker('boolean')
    opk_experience = factory.Faker('boolean')
    science_experience = factory.Faker('boolean')
    military_sport_achievements = factory.Faker('boolean')
    sport_achievements = factory.Faker('boolean')
    work_group = factory.SubFactory(WorkGroupFactory)

    @post_generation
    def directions(self, create, value, **kwargs):
        if not create:
            return
        if value:
            self.directions.set(value)


class CompetenceFactory(DjangoModelFactory):
    class Meta:
        model = Competence

    parent_node = factory.SubFactory('application.tests.factories.CompetenceFactory')
    name = factory.Faker('word')
    is_estimated = factory.Faker('boolean')

    @post_generation
    def directions(self, create, value, **kwargs):
        if not create:
            return
        if value:
            self.directions.set(value)


class ApplicationCompetenciesFactory(DjangoModelFactory):
    class Meta:
        model = ApplicationCompetencies

    application = factory.SubFactory(ApplicationFactory)
    competence = factory.SubFactory(CompetenceFactory)
    level = factory.Faker('pyint', min_value=0, max_value=3)


class EducationFactory(DjangoModelFactory):
    class Meta:
        model = Education

    application = factory.SubFactory(ApplicationFactory)
    education_type = factory.Faker('random_element', elements=['b', 'm', 'a', 's'])
    university = factory.Faker('word')
    specialization = factory.Faker('sentence')
    avg_score = factory.Faker('pyfloat', min_value=1.0, max_value=5.0)
    end_year = factory.Faker('year')
    is_ended = factory.Faker('boolean')
    name_of_education_doc = factory.Faker('sentence')
    theme_of_diploma = factory.Faker('sentence')


class ApplicationNoteFactory(DjangoModelFactory):
    class Meta:
        model = ApplicationNote

    application = factory.SubFactory(ApplicationFactory)
    author = factory.SubFactory(MemberFactory)
    text = factory.Faker('sentence')

    @post_generation
    def affiliations(self, create, value, **kwargs):
        if not create:
            return
        if value:
            self.affiliations.set(value)


class FileFactory(DjangoModelFactory):
    class Meta:
        model = File
    member = factory.SubFactory(MemberFactory)
    file_path = factory.django.FileField(filename='the_file.dat')
    file_name = factory.Faker('word')
    is_template = factory.Faker('boolean')
