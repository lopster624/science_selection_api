from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'get_fullname', 'phone', 'get_affiliations')
    list_filter = ('role',)

    def get_fullname(self, obj):
        return f'{obj.user.member}'

    def get_affiliations(self, obj):
        return '; '.join([d.__str__() for d in obj.affiliations.all()])

    get_fullname.short_description = 'ФИО'
    get_affiliations.short_description = 'Взводы'


@admin.register(models.Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name',)
    list_filter = ('role_name',)


@admin.register(models.Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('direction', 'company', 'platoon')
    list_filter = ('direction', 'company', 'platoon')


@admin.register(models.Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_type', 'master', 'slave',)
    list_filter = ('booking_type', 'master', 'slave',)


@admin.register(models.BookingType)
class BookingTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.ActivationLink)
class ActivationLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'token')
    list_filter = ('user',)


admin.site.unregister(models.User)


class MemberInlineAdmin(admin.TabularInline):
    model = models.Member


@admin.register(models.User)
class CustomUserAdmin(UserAdmin):
    inlines = [MemberInlineAdmin]
