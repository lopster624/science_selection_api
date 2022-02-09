from django.contrib import admin

from . import models


class CompetenciesInlineAdmin(admin.TabularInline):
    model = models.Application.competencies.through


@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    inlines = [CompetenciesInlineAdmin]
    list_display = ('member', 'draft_year', 'draft_season', 'final_score')
    list_filter = ('draft_year', 'draft_season', 'final_score')


@admin.register(models.Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('application', 'education_type', 'specialization', 'avg_score', 'is_ended')
    list_filter = ('education_type', 'avg_score', 'is_ended')


@admin.register(models.File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('member', 'file_name', 'create_date', 'is_template',)
    list_filter = ('member', 'file_name', 'create_date')


@admin.register(models.Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_directions', 'is_estimated')
    list_filter = ('name', 'is_estimated')

    def get_directions(self, obj):
        return ', '.join([d.name for d in obj.directions.all()])

    get_directions.short_description = 'Направления'


@admin.register(models.Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.ApplicationCompetencies)
class ApplicationCompetenciesAdmin(admin.ModelAdmin):
    list_display = ('application', 'competence', 'level',)
    list_filter = ('application', 'competence', 'level',)


@admin.register(models.ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ('application', 'author', 'text', 'get_affiliations')
    list_filter = ('application', 'author')

    def get_affiliations(self, obj):
        return '; '.join([d.__str__() for d in obj.affiliations.all()])

    get_affiliations.short_description = 'Взводы'


@admin.register(models.Universities)
class UniversitiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rating_place')
    search_fields = ('name',)


@admin.register(models.ApplicationScores)
class ApplicationScoresAdmin(admin.ModelAdmin):
    list_display = ('application', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7')
    list_filter = ('application', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7')


@admin.register(models.AdditionField)
class AdditionFieldAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.AdditionFieldApp)
class AdditionFieldAppAdmin(admin.ModelAdmin):
    list_display = ('addition_field', 'application', 'value')


@admin.register(models.Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.MilitaryCommissariat)
class MilitaryCommissariatAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject',)


class ApplicationInlineAdmin(admin.TabularInline):
    model = models.Application


@admin.register(models.WorkGroup)
class WorkGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'affiliation', 'description', 'get_applications')
    list_filter = ('name', 'affiliation')

    def get_applications(self, obj):
        return '; '.join([d.__str__() for d in obj.application.all()])

    get_applications.short_description = 'Взводы'

    inlines = [ApplicationInlineAdmin]
