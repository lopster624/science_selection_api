from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from account.models import Member
from utils import constants as const
from .models import Application, Direction, Education


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
    member = MemberListSerialiser()
    education = EducationListSerializer(many=True)
    draft_season = serializers.CharField(source='get_draft_season_display')
    directions = DirectionListSerializer(many=True)

    class Meta:
        model = Application
        fields = (
            'id', 'directions', 'draft_season', 'birth_day', 'birth_place', 'draft_year', 'fullness', 'final_score',
            'member', 'education'
        )


class ApplicationSlaveDetailSerializer(serializers.ModelSerializer):
    draft_season = serializers.CharField(source='get_draft_season_display', read_only=True)
    is_final = serializers.BooleanField(read_only=True)
    member = MemberListSerialiser(read_only=True)
    education = EducationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        exclude = ('compliance_prior_direction', 'compliance_additional_direction', 'postgraduate_additional_direction',
                   'postgraduate_prior_direction', 'directions', 'competencies', 'work_group')


class ApplicationMasterDetailSerializer(serializers.ModelSerializer):
    member = MemberListSerialiser(read_only=True)
    draft_season_display = serializers.CharField(source='get_draft_season_display', read_only=True)
    education = EducationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        exclude = ('directions', 'competencies')
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
