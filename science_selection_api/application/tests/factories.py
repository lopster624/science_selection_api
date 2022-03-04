# todo написать factory
from datetime import datetime

import factory
from django.contrib.auth.models import User
from factory import post_generation
from factory.django import DjangoModelFactory

from account.models import Member, Role, Affiliation
from application.models import Application, Direction, WorkGroup


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
    draft_year = factory.Faker('pyint', min_value=datetime.now().year+1, max_value=datetime.now().year+10)
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