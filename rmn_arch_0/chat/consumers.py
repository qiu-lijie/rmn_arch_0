from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Room, Message, UserRoomStatus
from rmn_arch_0.users.models import User


FROM = 'from'
TO = 'to'
TYPE = 'type'
BODY = 'body'


class ChatConsumer(AsyncJsonWebsocketConsumer):
    BASE_CHANNEL = 'root'
    CHAT_NEW = 'chat_new'
    CHAT_MSG = 'chat_message'
    CHAT_READ = 'chat_read'

    @database_sync_to_async
    def get_rooms(self):
        return list(Room.objects.get_user_rooms(self.user))

    async def connect(self):
        """
        Handles websocket connection
        Reject unauthenticated user
        otherwise add user to BASE_CHANNEL and any of their current rooms
        """
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            return  # reject unauthenticated user
        await self.channel_layer.group_add(self.BASE_CHANNEL, self.channel_name)
        self.rooms = {}
        rooms = await self.get_rooms()
        for room in rooms:
            self.rooms[room.name] = room.id
            await self.channel_layer.group_add(room.name, self.channel_name)
        await self.accept()
        return

    async def disconnect(self, close_code):
        """
        Handles websocket disconnect, discard current user from their groups
        """
        await self.channel_layer.group_discard(self.BASE_CHANNEL, self.channel_name)
        for room in self.rooms:
            await self.channel_layer.group_discard(room, self.channel_name)
        return

    @database_sync_to_async
    def handle_chat_new(self, content):
        """
        Get or create new room for user, then create the new chat message
        """
        try:
            room = Room.objects.get(name=content[TO])
        except Room.DoesNotExist:
            room = Room.objects.create_by_name(self.user, content[TO])
        Message.objects.create(
            user = self.user,
            room = room,
            content = content[BODY],
        )
        return

    @database_sync_to_async
    def handle_chat_msg(self, content):
        """
        Create the new chat message
        """
        Message.objects.create(
            user = self.user,
            room_id = self.rooms[content[TO]],
            content = content[BODY],
        )
        return

    @database_sync_to_async
    def handle_chat_read(self, content):
        """
        Update self.user's last view status for the given room
        """
        if content[TO] in self.rooms:
            stat = UserRoomStatus.objects.get(
                user = self.user,
                room_id = self.rooms[content[TO]]
            )
            stat.update_last_view()
        return

    async def receive_json(self, content):
        """
        Receive new websocket message and dispatch accordingly
        """
        user = content.get(FROM)
        room_name = content.get(TO)
        type = content.get(TYPE)
        body = content.get(BODY)
        if not type or not room_name or not body or not user:
            return
        elif type == self.CHAT_NEW:
            await self.handle_chat_new(content)
        elif type == self.CHAT_MSG:
            await self.handle_chat_msg(content)
        elif type == self.CHAT_READ:
            await self.handle_chat_read(content)
            return

        await self.channel_layer.group_send(
            self.BASE_CHANNEL if type == self.CHAT_NEW else room_name,
            content,
        )
        return

    @database_sync_to_async
    def get_user_info(self, username):
        user = User.objects.get(username=username)
        return {
            'username': user.username,
            'name': user.name,
            'img_url': user.profile_image_url,
        }

    async def chat_new(self, event):
        """
        Add user to new group if not blocking, then forward event to client
        """
        if self.user.username in event[TO].split('-'):
            room = await database_sync_to_async(Room.objects.get)(name=event[TO])
            stat = await database_sync_to_async(room.get_user_stat)(self.user)
            if stat.block:
                return  # reject if self.user is blocking new msg
            self.rooms[room.name] = room.id
            await self.channel_layer.group_add(room.name, self.channel_name)
            event['user_info'] = await self.get_user_info(event[FROM])
            await self.send_json(event)
        return

    async def chat_message(self, event):
        """
        Forward event to client
        """
        await self.send_json(event)
        return
