from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.test import TestCase
from django.urls.base import reverse
from django.utils import timezone

from datetime import datetime
from random import choice
from string import ascii_letters

from .._tools.utils import TEST_IMG_PATH, create_user, create_posts
from rmn_arch_0.users.models import User, Profile
from rmn_arch_0.posts.models import Post


class TestUser(TestCase):
    def test_post_count(self):
        user = User()
        user.save()
        post_count = 5
        for _ in range(post_count):
            post = Post(user=user)
            post.save()
        self.assertEqual(user.post_count, post_count)

        post = Post(user=user)
        post.save()
        self.assertEqual(user.post_count, post_count+1)
        return

    def test_pub_post_count(self):
        user = create_user()
        p0, p1 = create_posts(user, 2)
        self.assertEqual(user.pub_post_count(), 2)
        p0.anonymous = True
        p0.save()
        self.assertEqual(user.pub_post_count(), 1)
        p1.show = False
        p1.save()
        self.assertEqual(user.pub_post_count(), 0)
        return

    def test_follower_count(self):
        u0 = create_user()
        u1 = create_user(username='u1')
        self.assertEqual(u1.follower_count(), 0)
        u0.relations.follows.add(u1)
        self.assertEqual(u0.follower_count(), 0)
        self.assertEqual(u1.follower_count(), 1)
        return

    def test_following_count(self):
        u0 = create_user()
        u1 = create_user(username='u1')
        self.assertEqual(u0.following_count(), 0)
        u0.relations.follows.add(u1)
        self.assertEqual(u0.following_count(), 1)
        self.assertEqual(u1.following_count(), 0)
        return

    def test_valid_username(self):
        user = User(username=''.join([choice(ascii_letters) for _ in range(5)]),
            email='test@m.com', password='12345Abcdefg')
        user.full_clean()
        user.save()
        user = User(username='@.+-_', email='test1@m.com', password='12345Abcdefg')
        user.full_clean()
        user.save()
        return

    def test_invalid_username(self):
        user = User(username='中文', email='test@m.com', password='12345Abcdefg')
        with self.assertRaisesMessage(ValidationError,
            'Enter a valid username. This value may contain only English letters, numbers, and @/./+/-/_ characters.'):
            user.full_clean()
            user.save()
        for s in '!#$%^&*()`,<>?|\{\}[]/\\':
            user = User(username=s, email='test@m.com', password='12345Abcdefg')
            with self.assertRaisesMessage(ValidationError,
                'Enter a valid username. This value may contain only English letters, numbers, and @/./+/-/_ characters.'):
                user.full_clean()
                user.save()
        return

    def test_profile_image_url(self):
        user = User.objects.create()
        profile = Profile.objects.create(user=user)
        self.assertEqual(user.profile_image_url, static('images/default_profile_img.png'))
        image_path = 'random/image.jpg'
        profile.image = image_path
        profile.save()
        self.assertEqual(user.profile_image_url, f'/media/{image_path}')
        return

    def test_get_absolute_url(self):
        user = User.objects.create(username='test_user')
        self.assertEqual(user.get_absolute_url(),
            reverse('posts:user_posts', kwargs={'username':user.username}))
        return


class TestProfile(TestCase):
    def test_age(self):
        today = timezone.now()
        age = 21
        user = User()
        user.save()
        profile = Profile(user=user, birthday=datetime(year=today.year - age, month=today.month, day=today.day))
        profile.save()
        self.assertEqual(profile.age, age)
        return

    def test_age_none(self):
        user = User()
        user.save()
        profile = Profile(user=user, birthday=None)
        profile.save()
        self.assertEqual(profile.age, None)
        return

# TODO test Settings and Relations, add a few helper to Relations probably
