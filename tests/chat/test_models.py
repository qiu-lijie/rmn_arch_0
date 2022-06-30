from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from rmn_arch_0.chat.models import UserRoomStatus, Room, Message
from rmn_arch_0.users.models import Settings
from .._tools.utils import create_user


def create_user_room_status(user):
    """
    """
    room = Room(name=user.username)
    room.save()
    return UserRoomStatus.objects.create(user=user, room=room)


class TestUserRoomStatus(TestCase):
    def test_default(self):
        user = create_user()
        bef = timezone.now()
        user_stat = create_user_room_status(user=user)
        aft = timezone.now()
        self.assertFalse(user_stat.block)
        self.assertTrue(bef < user_stat.last_view)
        self.assertTrue(aft > user_stat.last_view)
        return

    def test_update_last_view(self):
        user = create_user()
        user_stat = create_user_room_status(user=user)
        bef = timezone.now()
        user_stat.update_last_view()
        aft = timezone.now()
        self.assertTrue(bef < user_stat.last_view)
        self.assertTrue(aft > user_stat.last_view)
        return

    def test_set_block(self):
        user = create_user()
        user_stat = create_user_room_status(user=user)
        self.assertFalse(user_stat.block)
        user_stat.set_block(True)
        self.assertTrue(user_stat.block)
        return


class TestRoom(TestCase):
    def setUp(self):
        super().setUp()
        self.u0 = create_user('u0')
        self.u1 = create_user('u1')
        return

    def test_create(self):
        self.assertEqual(UserRoomStatus.objects.count(), 0)
        room = Room.objects.create(self.u0, self.u1)
        self.assertEqual(UserRoomStatus.objects.count(), 2)
        self.assertEqual(room.userroomstatus_set.count(), 2)
        self.assertEqual(room.name, Room.get_room_name(self.u0, self.u1))
        self.assertTrue(room.userroomstatus_set.filter(user=self.u0).exists())
        self.assertTrue(room.userroomstatus_set.filter(user=self.u1).exists())
        return

    def test_create_target_non_block(self):
        room = Room.objects.create(self.u0, self.u1)
        self.assertFalse(room.userroomstatus_set.get(user=self.u0).block)
        self.assertFalse(room.userroomstatus_set.get(user=self.u1).block)
        return

    def test_create_target_block_new_msg(self):
        self.u1.settings.rec_new_msg = Settings.BLOCK
        room = Room.objects.create(self.u0, self.u1)
        self.assertFalse(room.userroomstatus_set.get(user=self.u0).block)
        self.assertTrue(room.userroomstatus_set.get(user=self.u1).block)
        return

    def test_create_target_block_non_following(self):
        self.u1.settings.rec_new_msg = Settings.FOLLOW
        room = Room.objects.create(self.u0, self.u1)
        self.assertFalse(room.userroomstatus_set.get(user=self.u0).block)
        self.assertTrue(room.userroomstatus_set.get(user=self.u1).block)

        room.delete()
        self.u1.relations.follows.add(self.u0)
        room = Room.objects.create(self.u0, self.u1)
        self.assertFalse(room.userroomstatus_set.get(user=self.u0).block)
        self.assertFalse(room.userroomstatus_set.get(user=self.u1).block)
        return

    def create_by_name(self):
        room = Room.objects.create_by_name(self.u0, Room.get_room_name(self.u0, self.u1))
        self.assertTrue(room.userroomstatus_set.filter(user=self.u0).exists())
        self.assertTrue(room.userroomstatus_set.filter(user=self.u1).exists())
        return

    def test_get_room_name(self):
        self.assertEqual('u0-u1', Room.get_room_name(self.u0, self.u1))
        self.assertEqual('u0-u1', Room.get_room_name(self.u1, self.u0))
        return

    def test_unique(self):
        Room.objects.create(self.u0, self.u1)
        with self.assertRaisesMessage(IntegrityError,
            f'Key (name)=({Room.get_room_name(self.u0, self.u1)}) already exists.'):
            Room.objects.create(self.u1, self.u0)
        return

    def test_room_with_duplicate_user(self):
        with self.assertRaisesMessage(ValidationError,
            'Users cannot be the same'):
            Room.objects.create(self.u0, self.u0)
        return

    def test_delete(self):
        self.assertEqual(Room.objects.count(), 0)
        self.assertEqual(UserRoomStatus.objects.count(), 0)
        room = Room.objects.create(self.u0, self.u1)
        self.assertEqual(Room.objects.count(), 1)
        self.assertEqual(UserRoomStatus.objects.count(), 2)
        self.assertEqual(room.userroomstatus_set.count(), 2)
        room.delete()
        self.assertEqual(Room.objects.count(), 0)
        self.assertEqual(UserRoomStatus.objects.count(), 0)
        return

    def test_delete_multi_rooms(self):
        r0 = Room.objects.create(self.u0, self.u1)
        u2 = create_user('u2')
        r1 = Room.objects.create(self.u0, u2)
        self.assertEqual(Room.objects.count(), 2)
        self.assertEqual(UserRoomStatus.objects.count(), 4)
        r2 = Room.objects.create(self.u1, u2)
        self.assertEqual(Room.objects.count(), 3)
        self.assertEqual(UserRoomStatus.objects.count(), 6)

        r0.delete()
        self.assertEqual(Room.objects.count(), 2)
        self.assertEqual(UserRoomStatus.objects.count(), 4)
        return

    def test_get_user_stat(self):
        room = Room.objects.create(self.u0, self.u1)
        self.assertEqual(room.get_user_stat(self.u0), room.userroomstatus_set.get(user=self.u0))
        self.assertEqual(room.get_user_stat(self.u1), room.userroomstatus_set.get(user=self.u1))
        return

    def test_get_other_user_stat(self):
        room = Room.objects.create(self.u0, self.u1)
        self.assertEqual(room.get_other_user_stat(self.u1), room.userroomstatus_set.get(user=self.u0))
        self.assertEqual(room.get_other_user_stat(self.u0), room.userroomstatus_set.get(user=self.u1))
        return

    def test_get_user_rooms(self):
        room = create_room_w_msg(self.u0, self.u1)
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertTrue(room in rooms)
        self.assertEqual(len(rooms), 1)
        u2 = create_user('u2')
        room = create_room_w_msg(self.u0, u2)
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertTrue(room in rooms)
        self.assertEqual(len(rooms), 2)

        rooms = Room.objects.get_user_rooms(u2)
        self.assertEqual(len(rooms), 1)
        room = create_room_w_msg(u2, self.u1)
        rooms = Room.objects.get_user_rooms(u2)
        self.assertTrue(room in rooms)
        self.assertEqual(len(rooms), 2)
        return

    def test_get_user_rooms_blocking(self):
        room = create_room_w_msg(self.u0, self.u1)
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertTrue(room in rooms)
        rooms = Room.objects.get_user_rooms(self.u1)
        self.assertTrue(room in rooms)
        
        u1_stat = UserRoomStatus.objects.get(user=self.u1, room=room)
        u1_stat.set_block(True)
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertTrue(room in rooms)
        rooms = Room.objects.get_user_rooms(self.u1)
        self.assertFalse(room in rooms)
        return

    def test_get_user_rooms_order(self):
        u2 = create_user('u2')
        u3 = create_user('u3')
        r0 = create_room_w_msg(self.u0, self.u1)
        r1 = create_room_w_msg(self.u0, u2)
        r2 = create_room_w_msg(self.u0, u3)

        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertEqual(rooms[0], r2)
        self.assertEqual(rooms[1], r1)
        self.assertEqual(rooms[2], r0)

        Message.objects.create(user=self.u0, room=r1)
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertEqual(rooms[0], r1)
        self.assertEqual(rooms[1], r2)
        self.assertEqual(rooms[2], r0)
        return

    def test_get_user_rooms_unread(self):
        create_room_w_msg(self.u0, self.u1)
        room = Room.objects.get_user_rooms(self.u0)[0]
        self.assertFalse(room.unread)
        room = Room.objects.get_user_rooms(self.u1)[0]
        self.assertTrue(room.unread)
        stat = room.get_user_stat(self.u1)
        stat.update_last_view()
        room = Room.objects.get_user_rooms(self.u1)[0]
        self.assertFalse(room.unread)
        return

    def test_get_user_rooms_no_msg(self):
        room = create_room_w_msg(self.u0, self.u1)
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertTrue(room in rooms)
        Message.objects.all().delete()
        rooms = Room.objects.get_user_rooms(self.u0)
        self.assertFalse(room in rooms)
        return

    def test_has_new_message(self):
        create_room_w_msg(self.u0, self.u1)
        self.assertFalse(Room.objects.has_new_message(self.u0))
        self.assertTrue(Room.objects.has_new_message(self.u1))
        stat = Room.objects.get_user_rooms(self.u1)[0].get_user_stat(self.u1)
        stat.update_last_view()
        self.assertFalse(Room.objects.has_new_message(self.u1))
        return


def create_room_w_msg(u0, u1):
    """
    Returns a room created for u0 u1, with message created for u0
    """
    room = Room.objects.create(u0, u1)
    Message.objects.create(user=u0, room=room, content="")
    return room
