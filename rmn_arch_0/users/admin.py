from django.contrib import admin
from .models import User, Profile, Settings, Relations


class ProfileInline(admin.StackedInline):
    model = Profile
    autocomplete_fields = ['location',]


class SettingsInline(admin.StackedInline):
    model = Settings


class RelationsInline(admin.StackedInline):
    model = Relations


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_joined'
    list_display = ['username', 'gender', 'post_count','date_joined', 'last_login',]
    list_filter = ['profile__gender', 'is_staff', 'is_superuser',]
    readonly_fields = ['password', 'username', 'email',]
    search_fields = ['username',]
    inlines = [ProfileInline, SettingsInline, RelationsInline,]

    @admin.display(description='Gender')
    def gender(self, obj):
        return obj.profile.get_gender_display()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ['user',]
    autocomplete_fields = ['location',]


@admin.register(Settings)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ['user',]


@admin.register(Relations)
class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ['user',]
