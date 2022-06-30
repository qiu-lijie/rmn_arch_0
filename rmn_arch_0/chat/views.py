from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView

import json

from .models import Room, Message
from rmn_arch_0.users.models import User


class ChatView(LoginRequiredMixin, ListView):
    """
    Base chat view
        optioanlly accepts a user url param to start new chat or open existing chat
    """
    template_name = 'chat/chat.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.get_user_rooms(self.request.user)

    def get_context_data(self, tar_user=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if tar_user != None:
            tar_room_name = Room.get_room_name(user, tar_user)
            # if not self.object_list.filter(name=tar_room_name).exists():
            # TODO temp fix, Room.object_list should be a query set
            room_names = [room.name for room in self.object_list]
            if tar_room_name not in room_names:
                context['new_room_name'] = tar_room_name
                context['tar_user'] = tar_user
        for room in self.object_list:
            room.other_user = room.get_other_user_stat(user).user
            if tar_user == room.other_user:
                room.extra_css_class = ' active'
        return context

    def get(self, request, **kwargs):
        tar_user = request.GET.get('user')
        if tar_user != None:
            tar_user = get_object_or_404(User, username=tar_user)
        self.object_list = self.get_queryset()
        context = self.get_context_data(tar_user, **kwargs)
        return render(request, self.template_name, context)


class ChatContentAJAXView(LoginRequiredMixin, ListView):
    """
    Get given chat room content, TODO paginate by timestamp
    """
    template_name = 'chat/chat_content.html'
    context_object_name = 'msgs'

    def get_queryset(self):
        self.room = get_object_or_404(Room, name=self.kwargs['room_name'])
        return self.room.message_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['id'] = self.room.name
        return context
