from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from account.models import Member, Booking, Affiliation
from utils import constants as const
from .models import Application, Direction, Education, Competence, ApplicationCompetencies, WorkGroup
from .utils import has_affiliation


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name',)


class EducationListSerializer(serializers.ModelSerializer):
    education_type = serializers.CharField(source='get_education_type_display')

    class Meta:
        model = Education
        fields = ('education_type', 'university',)


class EducationDetailSerializer(serializers.ModelSerializer):
    education_type_display = serializers.CharField(source='get_education_type_display', read_only=True)

    class Meta:
        model = Education
        fields = '__all__'


class MemberListSerialiser(serializers.ModelSerializer):
    user = UserListSerializer()

    class Meta:
        model = Member
        fields = ('user', 'father_name',)


class MemberDetailSerialiser(serializers.ModelSerializer):
    user = UserListSerializer()

    class Meta:
        model = Member
        fields = ('user', 'father_name', 'phone')


class DirectionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = '__all__'


class DirectionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ('id', 'name')


class ApplicationListSerializer(serializers.ModelSerializer):
    member = MemberListSerialiser(read_only=True)
    education = EducationListSerializer(many=True)
    draft_season = serializers.CharField(source='get_draft_season_display')
    directions = DirectionListSerializer(many=True)

    class Meta:
        model = Application
        fields = (
            'id', 'directions', 'draft_season', 'birth_day', 'birth_place', 'draft_year', 'fullness', 'final_score',
            'member', 'education'
        )


class ApplicationSlaveCreateSerializer(serializers.ModelSerializer):
    """ Создание анкеты кандидатом"""

    class Meta:
        model = Application
        exclude = (
            'directions', 'compliance_prior_direction', 'compliance_additional_direction',
            'postgraduate_additional_direction', 'postgraduate_prior_direction', 'competencies', 'fullness',
            'final_score', 'is_final', 'work_group', 'member',
        )


class ApplicationSlaveDetailSerializer(serializers.ModelSerializer):
    """ Подробная анкета только для кандидата """
    draft_season = serializers.CharField(source='get_draft_season_display', read_only=True)
    is_final = serializers.BooleanField(read_only=True)
    member = MemberListSerialiser(read_only=True)
    education = EducationDetailSerializer(many=True, read_only=True)
    directions = DirectionDetailSerializer(read_only=True, many=True)

    class Meta:
        model = Application
        exclude = ('compliance_prior_direction', 'compliance_additional_direction',
                   'postgraduate_additional_direction', 'postgraduate_prior_direction', 'competencies', 'fullness',
                   'final_score', 'work_group', 'create_date', 'update_date')


class ApplicationMasterDetailSerializer(serializers.ModelSerializer):
    """ Подробная анкета только для мастера"""
    member = MemberListSerialiser(read_only=True)
    draft_season_display = serializers.CharField(source='get_draft_season_display', read_only=True)
    education = EducationDetailSerializer(many=True, read_only=True)
    directions = DirectionDetailSerializer(read_only=True, many=True)

    class Meta:
        model = Application
        exclude = ('competencies', 'create_date', 'update_date')
        extra_kwargs = {'final_score': {'read_only': True}, 'fullness': {'read_only': True}}
        # Todo: проверять, что is_final и work_group мастер может прожать только после брони.


class ApplicationWorkGroupSerializer(serializers.ModelSerializer):
    """ Рабочая группа заявки """

    class Meta:
        model = Application
        fields = ('work_group',)


class ChooseDirectionListSerializer(serializers.ListSerializer):
    """ Установка списка направлений для заявки """

    def save(self, pk=None):
        """
        Сохраняет список полученных направлений в заявку с pk. Обновляет итоговый балл заявки.
        :param pk: идентификатор заявки
        :return: None
        """
        user_app = get_object_or_404(Application, pk=pk)
        directions_ids = [item.pop('id') for item in self.validated_data]
        if directions_ids:
            directions = Direction.objects.filter(pk__in=directions_ids)
            user_app.directions.set(list(directions))
        else:
            user_app.directions.clear()
        user_app.update_scores(update_fields=['fullness', 'final_score'])

    def validate(self, data):
        """
        Проверяет, что выбрано допустимое количество направлений
        """
        if len(data) > const.MAX_APP_DIRECTIONS:
            raise serializers.ValidationError(f"Нельзя выбрать больше {const.MAX_APP_DIRECTIONS} направлений.")
        return data


class ChooseDirectionSerializer(serializers.ModelSerializer):
    """ Направления заявки """
    id = serializers.IntegerField()

    class Meta:
        model = Direction
        fields = ('id',)
        list_serializer_class = ChooseDirectionListSerializer


class RecursiveFieldSerializer(serializers.Serializer):
    """ Рекурсивные дочерние компетенции"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class FilteredCompetenceListSerializer(serializers.ListSerializer):
    """ Фильтр только на корневые компетенции"""

    def to_representation(self, data):
        data = data.filter(parent_node=None)
        return super().to_representation(data)


class CompetenceDetailSerializer(serializers.ModelSerializer):
    """ Список компетенций """
    child = RecursiveFieldSerializer(many=True, read_only=True)

    class Meta:
        model = Competence
        fields = ('name', 'is_estimated', 'id', 'child', 'parent_node', 'directions')
        list_serializer_class = FilteredCompetenceListSerializer
        extra_kwargs = {'parent_node': {'write_only': True}, 'directions': {'write_only': True}}


class CompetenceSerializer(serializers.ModelSerializer):
    """ Компетенция без уровня владения """

    class Meta:
        model = Competence
        fields = ('name', 'is_estimated', 'id')


class ApplicationCompetenciesSerializer(serializers.ModelSerializer):
    """ Выводит оцененную компетенцию """
    competence = CompetenceSerializer()

    class Meta:
        model = ApplicationCompetencies
        fields = ('level', 'competence')


class ApplicationCompetenciesCreateSerializer(serializers.ModelSerializer):
    """ Создает оцененные компетенции """

    class Meta:
        model = ApplicationCompetencies
        fields = ('level', 'application', 'competence')

    def create(self, validated_data):
        """Сохраняет или обновляет уровень владения компетенцией"""
        app_competence, _ = ApplicationCompetencies.objects.update_or_create(
            application=validated_data.get('application', None),
            competence=validated_data.get('competence', None),
            defaults={'level': validated_data.get('level', None), }
        )
        return app_competence


class AffiliationSerializer(serializers.ModelSerializer):
    """ Принадлежность """
    direction = DirectionListSerializer()

    class Meta:
        model = Affiliation
        fields = '__all__'


class BookingCreateSerializer(serializers.ModelSerializer):
    """ Создание бронирования и добавления в вишлист """

    class Meta:
        model = Booking
        exclude = ('booking_type', 'slave', 'master')

    def custom_validate(self, **kwargs):
        """
        Проверяет, что мастер успешно может отобрать данного кандидата
        При неверности данных вызывает исключение
        :param kwargs: словарь с экземплярами slave, master, booking type
        :return: True, валидны ли данные
        """
        booking_type = kwargs.get('booking_type')
        slave = kwargs.get('slave')
        affiliation = self.validated_data.get('affiliation')
        master = kwargs.get('master')
        # проверки и на book и на wishlist
        if not has_affiliation(master, affiliation):
            raise serializers.ValidationError("Данное направление вам не принадлежит!")

        if booking_type.name == const.BOOKED:
            if not has_affiliation(slave, affiliation):
                raise serializers.ValidationError("Кандидат не подал заявку на данное направление!")
            if Booking.objects.filter(slave=slave, booking_type=booking_type).exists():
                raise serializers.ValidationError("Данный кандидат уже отобран!")
            return True
        elif booking_type.name == const.IN_WISHLIST:
            if Booking.objects.filter(slave=slave, master=master, affiliation=affiliation,
                                      booking_type=booking_type).exists():
                raise serializers.ValidationError("Данная запись уже существует!")
        return True

    def save(self, **kwargs):
        self.custom_validate(**kwargs)
        super().save(**kwargs)


class BookingSerializer(serializers.ModelSerializer):
    """ Бронирования и добавления в вишлист """
    master = MemberDetailSerialiser()
    affiliation = AffiliationSerializer()

    class Meta:
        model = Booking
        exclude = ('booking_type', 'slave')


class WorkGroupSerializer(serializers.ModelSerializer):
    """ Рабочая группа """

    class Meta:
        model = WorkGroup
        fields = '__all__'

    def save(self, **kwargs):
        """
        Проверяет, что текущий user создает рабочую группу для своего направления
        :param kwargs: словарь с user
        :return:
        """
        if not has_affiliation(kwargs.get('user').member, self.validated_data.get('affiliation')):
            raise serializers.ValidationError("Данное направление вам не принадлежит!")
        super().save(**kwargs)
