from django.contrib import admin
from .models import UserRoomStatus, Room, Message


class UserRoomStatusInline(admin.StackedInline):
    model = UserRoomStatus
    extra = 0
    readonly_fields = ['user', 'last_view']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    inlines = [UserRoomStatusInline]


@admin.register(UserRoomStatus)
class UserRoomStatusAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'last_view', 'block']
    search_fields = ['room', 'user']
    readonly_fields = ['room', 'user', 'last_view']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'created', 'content']
    search_fields = ['room', 'user']
    readonly_fields = ['room', 'user']
