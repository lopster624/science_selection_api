from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from account.models import Member
from utils import constants as const
from .models import Application, Direction, Education, Competence, ApplicationCompetencies


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


class ApplicationMasterCreateSerializer(serializers.ModelSerializer):
    """ Создание анкеты мастером """

    class Meta:
        model = Application
        exclude = ('directions', 'competencies', 'fullness', 'final_score', 'is_final', 'work_group')


class ApplicationSlaveCreateSerializer(serializers.ModelSerializer):
    """ Создание анкеты кандидатом"""

    class Meta:
        model = Application
        exclude = (
            'directions', 'compliance_prior_direction', 'compliance_additional_direction',
            'postgraduate_additional_direction', 'postgraduate_prior_direction', 'competencies', 'fullness',
            'final_score', 'is_final', 'work_group',
        )


class ApplicationSlaveDetailSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Application
        fields = ('work_group',)


class ChooseDirectionListSerializer(serializers.ListSerializer):
    def save(self, pk=None):
        """Сохраняет список полученных направлений в заявку с pk. Обновляет итоговый балл заявки."""
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
    id = serializers.IntegerField()

    class Meta:
        model = Direction
        fields = ('id',)
        list_serializer_class = ChooseDirectionListSerializer


class RecursiveFieldSerializer(serializers.Serializer):
    """ Рекурсивно выводит дочерние компетенции"""

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class FilteredCompetenceListSerializer(serializers.ListSerializer):
    """ Выводит только корневые компетенции"""

    def to_representation(self, data):
        data = data.filter(parent_node=None)
        return super().to_representation(data)


class FilteredAppCompListSerializer(serializers.ListSerializer):
    """ Выводит только оценки текущего пользователя"""

    def to_representation(self, data):
        data = data.filter(application=self.context.get("app_id"))
        return super().to_representation(data)


class ApplicationCompetenciesSerializer(serializers.ModelSerializer):
    """
    Выводит только список уровней владения компетенцией.
    С помощью FilteredAppCompListSerializer этот список сокращается только до одного уровня.
    """

    class Meta:
        model = ApplicationCompetencies
        fields = ('level',)
        list_serializer_class = FilteredAppCompListSerializer


class CompetenceSerializer(serializers.ModelSerializer):
    """Рекурсивно выводит список компетенций. Необходимо передать id анкеты как app_id."""
    child = RecursiveFieldSerializer(many=True)
    competence_value = ApplicationCompetenciesSerializer(many=True)

    def to_representation(self, instance):
        """
        Если компетенция оценена, то досдает уровень оценки из вложенного списка.
        Если компетенция не оценена, то не выводит ее
        """
        data = super().to_representation(instance)
        if data['competence_value']:
            data.update({'competence_value': data['competence_value'].pop()['level']})
            return data
        return {}

    class Meta:
        model = Competence
        fields = ('name', 'is_estimated', 'competence_value', 'child', 'id')
        list_serializer_class = FilteredCompetenceListSerializer

    # TODO: написать сериализатор добавления списка компетенций


class ApplicationCompetenciesCreateSerializer(serializers.ModelSerializer):
    """
    Создает оцененные компетенции.
    """

    class Meta:
        model = ApplicationCompetencies
        fields = ('level', 'application', 'competence')
