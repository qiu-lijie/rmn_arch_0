from django.test import TestCase, Client
from django.urls import reverse

import json

from rmn_arch_0.users.models import User, Relations


USERNAME_CHECK = reverse('users:username_check')
USER_FOLLOW = reverse('users:follow')


class TestUsernameCheckAJAXView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.username = 'name'
        User.objects.create(username=cls.username)
        cls.client = Client()
        return

    def test_unique_username(self):
        res = self.client.get(USERNAME_CHECK + f'?q={self.username}_')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['unique'])
        self.assertEqual(len(res.json()['suggestions']), 0)
        return

    def test_nonunique_username(self):
        res = self.client.get(USERNAME_CHECK + f'?q={self.username}')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()['unique'])
        self.assertEqual(len(res.json()['suggestions']), 3)
        return

    def test_nonunique_username_case_insensitive(self):
        res = self.client.get(USERNAME_CHECK + f'?q={self.username.upper()}')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()['unique'])
        self.assertEqual(len(res.json()['suggestions']), 3)
        return


class TestUserFollowAJAXView(TestCase):
    def setUp(self):
        self.username1 = 'username1'
        self.password1 = 'password1'
        self.user1 = User.objects.create(username=self.username1)
        self.user1.set_password(self.password1)
        self.user1.save()
        Relations.objects.create(user=self.user1)
        self.username2 = 'username2'
        self.password2 = 'password2'
        self.user2 = User.objects.create(username=self.username2, email='t1')
        self.user2.set_password(self.password2)
        self.user2.save()
        Relations.objects.create(user=self.user2)
        self.client = Client()
        self.client.login(username=self.username1, password=self.password1)
        return

    def post_user_follow(self, username, follow):
        return self.client.post(USER_FOLLOW, json.dumps({
            'username': username,
            'follow': follow,
        }), content_type='application/json')

    def test_valid_follow(self):
        res = self.post_user_follow(self.username2, True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.user1.relations.follows.filter(id=self.user2.id).count(), 1)
        # follow multiple time should have no effect
        res = self.post_user_follow(self.username2, True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.user1.relations.follows.filter(id=self.user2.id).count(), 1)
        self.client.logout()

        self.client.login(username=self.username2, password=self.password2)
        res = self.post_user_follow(self.username1, True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.user2.relations.follows.filter(id=self.user1.id).count(), 1)
        return

    def test_valid_unfollow(self):
        res = self.post_user_follow(self.username2, True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.user1.relations.follows.filter(id=self.user2.id).count(), 1)
        res = self.post_user_follow(self.username2, False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.user1.relations.follows.filter(id=self.user2.id).count(), 0)
        # unfollow multiple time should have no effect
        res = self.post_user_follow(self.username2, False)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.user1.relations.follows.filter(id=self.user2.id).count(), 0)
        return

    def test_invalid_not_logined(self):
        self.client.logout()
        res = self.post_user_follow(self.username2, True)
        self.assertEqual(res.status_code, 403)
        return

    def test_invalid_not_found(self):
        res = self.post_user_follow(self.username2+'.', True)
        self.assertEqual(res.status_code, 404)
        return

    def test_invalid_follows_self(self):
        res = self.post_user_follow(self.username1, True)
        self.assertEqual(res.status_code, 400)
        res = self.post_user_follow(self.username1, False)
        self.assertEqual(res.status_code, 400)
        return

    def test_invalid_bad_param(self):
        res = self.post_user_follow(None, True)
        self.assertEqual(res.status_code, 400)
        res = self.post_user_follow(self.username2, None)
        self.assertEqual(res.status_code, 400)
        return

    def test_invalid_missing_param(self):
        res = self.client.post(USER_FOLLOW,
            json.dumps({'username': self.username2}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        res = self.client.post(USER_FOLLOW,
            json.dumps({'follow': True}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        return

    def test_method_not_allowed(self):
        res = self.client.get(USER_FOLLOW)
        self.assertEqual(res.status_code, 405)
        return
