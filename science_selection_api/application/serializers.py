from django.contrib.auth.models import User
from rest_framework import serializers

from account.models import Member, Booking, Affiliation
from utils import constants as const
from .models import Application, Direction, Education, Competence, ApplicationCompetencies, WorkGroup, ApplicationNote, \
    ViewedApplication, File
from .utils import has_affiliation, get_booking, get_master_affiliations_id


class UserListSerializer(serializers.ModelSerializer):
    """Список пользователей"""

    class Meta:
        model = User
        fields = ('first_name', 'last_name',)


class EducationListSerializer(serializers.ModelSerializer):
    """Список образований"""
    education_type = serializers.CharField(source='get_education_type_display')

    class Meta:
        model = Education
        fields = ('education_type', 'university', 'specialization')


class EducationDetailSerializer(serializers.ModelSerializer):
    """Образование"""
    education_type_display = serializers.CharField(source='get_education_type_display', read_only=True)

    class Meta:
        model = Education
        fields = '__all__'


class MemberListSerialiser(serializers.ModelSerializer):
    """Список участников"""
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    second_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Member
        fields = ('first_name', 'second_name', 'father_name',)


class MemberDetailSerialiser(serializers.ModelSerializer):
    """Участник"""
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    second_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Member
        fields = ('first_name', 'second_name', 'father_name', 'phone')


class DirectionDetailSerializer(serializers.ModelSerializer):
    """Направление"""

    class Meta:
        model = Direction
        fields = '__all__'


class DirectionListSerializer(serializers.ModelSerializer):
    """Список направлений"""

    class Meta:
        model = Direction
        fields = ('id', 'name')


class AffiliationSerializer(serializers.ModelSerializer):
    """Принадлежность"""

    class Meta:
        model = Affiliation
        exclude = ('direction',)


class AffiliationDetailSerializer(serializers.ModelSerializer):
    """Принадлежность"""
    direction = DirectionListSerializer()

    class Meta:
        model = Affiliation
        fields = '__all__'


class BookingDetailSerializer(serializers.ModelSerializer):
    """Бронирования и добавления в вишлист"""
    master = MemberDetailSerialiser()
    affiliation = AffiliationSerializer()

    class Meta:
        model = Booking
        exclude = ('slave', 'booking_type')


class BookingSerializer(serializers.ModelSerializer):
    """Бронирования и добавления в вишлист"""
    master = MemberListSerialiser()
    affiliation = AffiliationSerializer()

    class Meta:
        model = Booking
        exclude = ('slave', 'booking_type',)


class ApplicationNoteSerializer(serializers.ModelSerializer):
    """Заметка о заявке"""
    author = MemberListSerialiser(read_only=True)

    class Meta:
        model = ApplicationNote
        exclude = ('application',)

    def save(self, **kwargs):
        """ Проверяет, что автор выбрал только свои принадлежности и сохраняет """
        master_affiliations = get_master_affiliations_id(kwargs.get('author'))
        affiliations = self.validated_data.get('affiliations', None)
        if not affiliations:
            raise serializers.ValidationError(f'Не выбран взвод, для которого будет видна заметка!')
        for affiliation in affiliations:
            if affiliation.id not in master_affiliations:
                raise serializers.ValidationError(f'{affiliation} не является вашим!')
        super().save(**kwargs)


class ApplicationMasterListSerializer(serializers.ModelSerializer):
    """Список заявок для мастера"""
    member = MemberListSerialiser(read_only=True)
    education = EducationListSerializer(many=True)
    draft_season = serializers.CharField(source='get_draft_season_display')
    directions = DirectionListSerializer(many=True)

    # Аннотируемые поля
    is_booked = serializers.BooleanField(read_only=True)  # анкета отобрана
    booking = BookingSerializer(many=True, read_only=True,
                                source='member.booking_affiliation')  # экземпляр бронирования
    is_booked_our = serializers.BooleanField(read_only=True)  # отобрана на направление текущего мастера
    can_unbook = serializers.BooleanField(read_only=True)  # мастер может отменить отбор
    wishlist_len = serializers.IntegerField(read_only=True)  # количество добавлений в избранное
    is_in_wishlist = serializers.BooleanField(read_only=True)  # добавлена в вишлист мастера
    our_direction = serializers.BooleanField(read_only=True)  # подана на направление мастера
    subject = serializers.CharField(read_only=True)  # субъект РФ проживания
    available_booking_direction = DirectionListSerializer(read_only=True,
                                                          many=True)  # направлении, доступные для бронирования

    wishlist = BookingSerializer(many=True, read_only=True, source='member.candidate')  # в избранном
    notes = ApplicationNoteSerializer(many=True, read_only=True)  # заметки
    is_viewed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'directions', 'draft_season', 'birth_day', 'birth_place', 'draft_year', 'fullness', 'final_score',
            'member', 'education', 'is_booked', 'is_booked_our', 'can_unbook', 'wishlist_len', 'is_in_wishlist',
            'our_direction', 'subject', 'available_booking_direction', 'booking', 'wishlist', 'notes', 'is_viewed'
        )


class ApplicationListSerializer(serializers.ModelSerializer):
    """Список заявок"""
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
    """Создание анкеты кандидатом"""

    class Meta:
        model = Application
        exclude = (
            'directions', 'compliance_prior_direction', 'compliance_additional_direction',
            'postgraduate_additional_direction', 'postgraduate_prior_direction', 'competencies', 'fullness',
            'final_score', 'is_final', 'work_group', 'member',
        )


class ApplicationSlaveDetailSerializer(serializers.ModelSerializer):
    """Подробная анкета только для кандидата"""
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
    """Подробная анкета только для мастера"""
    member = MemberListSerialiser(read_only=True)
    draft_season_display = serializers.CharField(source='get_draft_season_display', read_only=True)
    education = EducationDetailSerializer(many=True, read_only=True)
    directions = DirectionDetailSerializer(read_only=True, many=True)

    class Meta:
        model = Application
        exclude = ('competencies', 'create_date', 'update_date')
        extra_kwargs = {'final_score': {'read_only': True}, 'is_final': {'read_only': True},
                        'fullness': {'read_only': True}}


def validate_work_group(slave_member, work_group):
    """
    проверяет, что сохраняемая рабочая группа принадлежит направлению, на которое забронирована заявка
    :param slave_member:
    :param work_group:
    :return: True
    """
    booking = get_booking(slave_member)
    if not booking:
        raise serializers.ValidationError('Данный кандидат не был отобран!')
    if work_group and work_group.affiliation != booking.affiliation:
        raise serializers.ValidationError('Данная рабочая группа не соответствует принадлежности заявки!')
    return True


class ApplicationWorkGroupSerializer(serializers.ModelSerializer):
    """Рабочая группа заявки"""

    class Meta:
        model = Application
        fields = ('work_group',)

    def update(self, instance, validated_data):
        # Обновляет заявку после прохожедния валидации
        validate_work_group(instance.member, validated_data.get('work_group', None))
        return super().update(instance, validated_data)


class ApplicationIsFinalSerializer(serializers.ModelSerializer):
    """Рабочая группа заявки"""

    class Meta:
        model = Application
        fields = ('is_final',)


class ChooseDirectionListSerializer(serializers.ListSerializer):
    """Установка списка направлений для заявки"""

    def save(self, user_app=None):
        """
        Сохраняет список полученных направлений в заявку с pk. Обновляет итоговый балл заявки.
        :param user_app: экземпляр заяви
        :return: None
        """
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
    """Направления заявки"""
    id = serializers.IntegerField()

    class Meta:
        model = Direction
        fields = ('id',)
        list_serializer_class = ChooseDirectionListSerializer


class RecursiveFieldSerializer(serializers.Serializer):
    """Рекурсивные дочерние компетенции"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class FilteredCompetenceListSerializer(serializers.ListSerializer):
    """Фильтр только на корневые компетенции"""

    def to_representation(self, data):
        data = data.filter(parent_node=None)
        return super().to_representation(data)


class CompetenceDetailSerializer(serializers.ModelSerializer):
    """Список компетенций"""
    child = RecursiveFieldSerializer(many=True, read_only=True)

    class Meta:
        model = Competence
        fields = ('name', 'is_estimated', 'id', 'child', 'parent_node', 'directions')
        list_serializer_class = FilteredCompetenceListSerializer
        extra_kwargs = {'parent_node': {'write_only': True}, 'directions': {'write_only': True}}

    def validate_directions(self, directions):
        """ Проверяет, что выбранные направления принадлежат мастеру"""
        master_directions = self.context.get('master_directions')
        for direction in directions:
            if direction not in master_directions:
                raise serializers.ValidationError(f'Направление {direction} вам не принадлежит!')
        return directions


class CompetenceSerializer(serializers.ModelSerializer):
    """Компетенция без уровня владения"""

    class Meta:
        model = Competence
        fields = ('name', 'is_estimated', 'id')


class ApplicationCompetenciesSerializer(serializers.ModelSerializer):
    """Выводит оцененную компетенцию"""
    competence = CompetenceSerializer()

    class Meta:
        model = ApplicationCompetencies
        fields = ('level', 'competence')


class ApplicationCompetenciesCreateSerializer(serializers.ModelSerializer):
    """Создает оцененные компетенции"""

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


class BookingCreateSerializer(serializers.ModelSerializer):
    """Создание бронирования и добавления в вишлист"""

    class Meta:
        model = Booking
        exclude = ('booking_type', 'slave', 'master')

    def validate_booking(self, **kwargs):
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
            if Booking.objects.filter(slave=slave, affiliation=affiliation,
                                      booking_type=booking_type).exists():
                raise serializers.ValidationError("Данная запись уже существует!")
        return True

    def save(self, **kwargs):
        self.validate_booking(**kwargs)
        super().save(**kwargs)


class WorkGroupSerializer(serializers.ModelSerializer):
    """Рабочая группа"""

    class Meta:
        model = WorkGroup
        fields = '__all__'

    def save(self, **kwargs):
        """
        Проверяет, что текущий user создает рабочую группу для своего направления
        :param kwargs: словарь с user
        :return:
        """
        if not has_affiliation(kwargs.pop('user').member, self.validated_data.get('affiliation')):
            raise serializers.ValidationError("Данный взвод вам не принадлежит!")
        super().save(**kwargs)


class WorkGroupDetailSerializer(serializers.ModelSerializer):
    """Рабочая группа"""
    affiliation = AffiliationSerializer()

    class Meta:
        model = WorkGroup
        fields = '__all__'


class ViewedApplicationSerializer(serializers.ModelSerializer):
    """Просмотренная заявка"""

    class Meta:
        model = ViewedApplication
        fields = '__all__'


class FileSerializer(serializers.ModelSerializer):
    """Документ"""
    member = MemberListSerialiser(read_only=True)

    class Meta:
        model = File
        fields = '__all__'
        extra_kwargs = {'file_path': {'write_only': True}, 'is_template': {'read_only': True},
                        'file_name': {'read_only': True}}
