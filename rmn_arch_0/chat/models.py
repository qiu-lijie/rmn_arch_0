from django.core.exceptions import ValidationError
from django.db import models, connection
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from rmn_arch_0.users.models import User, Settings


class RoomManager(models.Manager):
    def create(self, user0, user1, *args, **kwargs):
        """
        Overide default create to
            limit room size, only direct message for now
            cannot chat with yourself
            create and add UserRoomStatus, respecting user1's setting
        @param  user0: User that initiated the request
        @param  name: str   target room name
        @return created Room instance
        """
        if user0 == user1:
            raise ValidationError('Users cannot be the same')

        name = Room.get_room_name(user0, user1)
        room = super().create(name=name, *args, **kwargs)
        UserRoomStatus.objects.create(user=user0, room=room)
        if (user1.settings.rec_new_msg == Settings.BLOCK
            or (user1.settings.rec_new_msg == Settings.FOLLOW
                and user0 not in user1.relations.follows.all())):
            UserRoomStatus.objects.create(user=user1, room=room, block=True)
        else:
            UserRoomStatus.objects.create(user=user1, room=room)
        return room

    def create_by_name(self, user0, name):
        """
        Create a room by room name and a user
        @param  user0: User that initiated the request
        @param  name: str   target room name
        @return created Room instance
        """
        username_list = name.split('-')
        username_list.remove(user0.username)
        user1_name = username_list[0]
        user1 = User.objects.get(username=user1_name)
        return self.create(user0, user1)

    ROOM_AND_MSG_QUERY = """
        SELECT
            DISTINCT ON (m.room_id)
            r.*,
            m.id AS last_msg,
            m.content AS last_msg_content,
            CASE 
                WHEN (m.user_id <> %s AND m.created >= s.last_view) THEN true
                ELSE false
            END AS unread
        FROM chat_message m
            INNER JOIN chat_room r ON m.room_id = r.id
            INNER JOIN chat_userroomstatus s ON r.id = s.room_id AND s.user_id = %s
        WHERE
            s.block = false
        ORDER BY m.room_id, m.id desc
    """

    def get_user_rooms(self, user):
        """
        Returns all non-block rooms for given user order by last message sent
        with the following additional field attached
            last_msg            int, id of the last message
            last_msg_content    str, content of the last message
            unread              bool, whether the message has been read
        NOTE implementation will only return rooms that has at least one message
        """
        return self.raw(
            f"""
            SELECT sub_query.* FROM (
                {self.ROOM_AND_MSG_QUERY}
            ) as sub_query
            ORDER BY last_msg desc;
            """,
            (user.id, user.id)
        )

    def has_new_message(self, user):
        """
        Return True if given user has new unread message, False otherwise
        """
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT 1 FROM (
                    {self.ROOM_AND_MSG_QUERY}
                ) as sub_query
                WHERE sub_query.unread = true
                LIMIT 1;
                """,
                (user.id, user.id)
            )
            res = cursor.fetchone()
        return True if res else False


class Room(models.Model):
    """
    Individual Chat Room
    """
    name = models.CharField(max_length=64, unique=True)

    objects = RoomManager()

    def __str__(self):
        return f'Room {self.name}'

    @staticmethod
    def get_room_name(user0, user1):
        """
        Return a string of the two usernames sorted, join by a '-' as room name
        """
        return '-'.join(sorted([user0.username, user1.username]))

    def get_user_stat(self, user):
        """
        Return the UserRoomStatus for a particualr user in the room
        """
        return self.userroomstatus_set.get(user=user)

    def get_other_user_stat(self, user):
        """
        Return the other UserRoomStatus for a particualr user in the room
        """
        return self.userroomstatus_set.exclude(user=user)[0]


class UserRoomStatus(models.Model):
    """
    Status of individual users in a particular chat room
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    last_view = models.DateTimeField(auto_now_add=True)
    block = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'User room statuses'

    def __str__(self):
        return f'UserRoomStatus for {self.room}'

    def update_last_view(self):
        """
        Updates when the user view the room
        """
        self.last_view = timezone.now()
        self.save()
        return

    def set_block(self, block):
        """
        Set the user blocking status
        """
        self.block = block
        self.save()
        return


class Message(models.Model):
    """
    Message sent by a user in a chat room
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message for {self.room} by {self.user}'
