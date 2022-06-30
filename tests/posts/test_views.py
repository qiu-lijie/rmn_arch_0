from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.models import Session
from django.test import TestCase, Client
from django.urls import reverse

import json
import os
import random
import shutil
from uuid import uuid4

from .._tools.utils import TEST_IMG_PATH, create_user, create_posts
from rmn_arch_0.posts.models import Post, PostImage, Rating
from rmn_arch_0.users.models import User, Settings


STR_TKN = '6edd5ab3-3f38-41fe-b34c-f93c50853186'
HOME = reverse('posts:home')
POST_CREATE = reverse('posts:post_create_modal')
RATE = reverse('posts:rate')
USER_POSTS = reverse('posts:user_posts', kwargs={'username':STR_TKN})
POST_DETAIL = reverse('posts:post_detail_modal', kwargs={'uuid':STR_TKN})
FOLLOW = reverse('posts:follow')


class BasePostTestCase(TestCase):
    def setUp(self):
        self.username = 'test_username'
        self.password = 'password'
        self.user = User.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.user.save()
        Settings.objects.create(user=self.user)
        res = self.client.login(username=self.username, password=self.password)
        self.assertTrue(res)
        return super().setUp()

    def tearDown(self):
        path = f'{settings.MEDIA_ROOT}/uploads/user_{self.username}'
        if os.path.exists(path):
            shutil.rmtree(path)
        return super().tearDown()


class TestPostCreateModalView(BasePostTestCase):
    def test_valid_post(self):
        desc = 'test\r\ntest\r\nend'
        data = {
            'description': desc,
            'anonymous': True,
            }
        with open(TEST_IMG_PATH, 'rb') as img:
            data['images'] = SimpleUploadedFile(img.name, img.read())
        res = self.client.post(POST_CREATE, data=data)
        self.assertRedirects(res, HOME)

        posts = Post.objects.all()
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.description, desc.replace('\r', ''))
        self.assertTrue(post.anonymous)
        self.assertTrue(post.reportable)
        self.assertTrue(post.show)

        imgs = PostImage.objects.all()
        self.assertEqual(len(imgs), 1)
        img = imgs[0]
        self.assertEqual(img.post, post)
        return

    def test_multiple_imgs(self):
        files = []
        for _ in range(PostImage.MAX_IMAGES):
            with open(TEST_IMG_PATH, 'rb') as img:
                files.append(SimpleUploadedFile(img.name, img.read()))
        data = {'images': files}
        res = self.client.post(POST_CREATE, data=data)
        self.assertRedirects(res, HOME)

        posts = Post.objects.all()
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.description, '')
        self.assertFalse(post.anonymous)
        self.assertTrue(post.reportable)
        self.assertTrue(post.show)

        imgs = PostImage.objects.all()
        self.assertEqual(len(imgs), PostImage.MAX_IMAGES)
        for img in imgs:
            self.assertEqual(img.post, post)
        return

    def test_no_image(self):
        res = self.client.post(POST_CREATE, data={})
        self.assertEqual(res.status_code, 200)
        self.assertFormError(res, 'form', 'images',
            'This field is required.')
        return

    def test_too_many_images(self):
        files = []
        for _ in range(PostImage.MAX_IMAGES + 1):
            with open(TEST_IMG_PATH, 'rb') as img:
                files.append(SimpleUploadedFile(img.name, img.read()))
        data = {'images': files}
        with self.assertRaisesMessage(ValidationError, 'Only 9 images per post allowed'):
            self.client.post(POST_CREATE, data=data)
        return

    def test_long_desc(self):
        desc = '0123456789\n\r'
        self.assertEqual(len(desc.replace('\r', '')), 11)
        desc = desc * 9 + '0'
        self.assertEqual(len(desc.replace('\r', '')), 100)
        data = {
            'description': desc,
            }
        with open(TEST_IMG_PATH, 'rb') as img:
            data['images'] = SimpleUploadedFile(img.name, img.read())
        res = self.client.post(POST_CREATE, data=data)
        self.assertRedirects(res, HOME)

        posts = Post.objects.all()
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.description, desc.replace('\r', ''))
        self.assertFalse(post.anonymous)
        self.assertTrue(post.reportable)
        self.assertTrue(post.show)
        return

    def test_too_long_desc(self):
        desc = '0123456789\n\r'
        self.assertEqual(len(desc.replace('\r', '')), 11)
        desc = desc * 9 + '0'
        self.assertEqual(len(desc.replace('\r', '')), 100)
        desc = desc + 'a'
        self.assertEqual(len(desc.replace('\r', '')), 101)
        data = {
            'description': desc,
            }
        with open(TEST_IMG_PATH, 'rb') as img:
            data['images'] = SimpleUploadedFile(img.name, img.read())
        res = self.client.post(POST_CREATE, data=data)
        self.assertEqual(res.status_code, 200)
        self.assertFormError(res, 'form', 'description',
            'Ensure this value has at most 100 characters (it has 101).')
        return


class TestPostRateAJAXView(BasePostTestCase):
    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(user=self.user)
        self.rate = 2
        return

    def post_rate_view(self, uuid, rate):
        return self.client.post(RATE, json.dumps({
            'uuid': str(uuid),
            'rate': rate,
        }), content_type='application/json')

    def test_valid_user_rating(self):
        res = self.post_rate_view(self.post.uuid, self.rate)
        self.assertEqual(res.status_code, 200)
        ratings = Rating.objects.all()
        self.assertEqual(len(ratings), 1)
        rating = ratings[0]
        self.assertEqual(rating.user, self.user)
        self.assertEqual(rating.session_key, None)        
        self.assertEqual(rating.post, self.post)
        self.assertEqual(rating.rate, self.rate)
        return

    def test_valid_session_rating(self):
        self.client.logout()
        res = self.post_rate_view(self.post.uuid, self.rate)
        self.assertEqual(res.status_code, 200)
        ratings = Rating.objects.all()
        self.assertEqual(len(ratings), 1)
        rating = ratings[0]
        self.assertEqual(rating.user, None)
        self.assertEqual(rating.session_key, self.client.session.session_key)        
        self.assertEqual(rating.post, self.post)
        self.assertEqual(rating.rate, self.rate)
        return

    def test_update_rating(self):
        res = self.post_rate_view(self.post.uuid, self.rate)
        self.assertEqual(res.status_code, 200)
        ratings = Rating.objects.all()
        self.assertEqual(len(ratings), 1)
        rating = ratings[0]
        self.assertEqual(rating.rate, self.rate)

        self.rate = 4
        res = self.post_rate_view(self.post.uuid, self.rate)
        self.assertEqual(res.status_code, 200)
        ratings = Rating.objects.all()
        self.assertEqual(len(ratings), 1)
        rating = ratings[0]
        self.assertEqual(rating.rate, self.rate)
        return

    def test_multi_rating(self):
        self.client.logout()
        ratings_num = 10
        for _ in range(ratings_num):
            self.client.session.cycle_key()
            res = self.post_rate_view(self.post.uuid, self.rate)
            self.assertEqual(res.status_code, 200)
        ratings = Rating.objects.all()
        self.assertEqual(len(ratings), ratings_num)
        self.assertEqual(Session.objects.count(), ratings_num + 1)  # +1 from setUp user
        return

    def test_same_session_key(self):
        self.client.logout()
        ratings_num = 10
        for _ in range(ratings_num):
            post = Post.objects.create(user=self.user)
            self.post_rate_view(post.uuid, self.rate)
        
        ratings = Rating.objects.all()
        self.assertEqual(len(ratings), ratings_num)
        init_rating = ratings[0]
        for rating in ratings:
            self.assertTrue(rating.session_key == init_rating.session_key)
            self.assertTrue(rating.session_key == self.client.session.session_key)
        return

    def test_session_then_login(self):
        self.client.logout()
        res = self.post_rate_view(self.post.uuid, self.rate)
        self.assertEqual(Rating.objects.count(), 1)

        self.client.login(username=self.username, password=self.password)
        res = self.post_rate_view(self.post.uuid, self.rate)
        self.assertEqual(res.status_code, 200)
        # currently creates brand new ratings
        self.assertEqual(Rating.objects.count(), 2)
        return

    def test_method_not_allowed(self):
        res = self.client.get(RATE)
        self.assertEqual(res.status_code, 405)
        return

    def test_missing_param(self):
        res = self.client.post(RATE,
            json.dumps({'uuid': str(self.post.uuid)}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        res = self.client.post(RATE,
            json.dumps({'rate': self.rate}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        return

    def test_invalid_uuid(self):
        uuid = uuid4()
        res = self.post_rate_view(uuid, self.rate)
        self.assertEqual(res.status_code, 404)
        return

    def test_invalid_rate(self):
        res = self.post_rate_view(self.post.uuid, Rating.MAX_RATING + 1)
        self.assertEqual(res.status_code, 400)
        return


class TestHomeView(TestCase):
    paginate_by = 20

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_username')
        cls.posts_num = 45
        for _ in range(cls.posts_num):
            post = Post.objects.create(user=cls.user)
            PostImage.objects.create(image='.', post=post)
        return

    def test_base_behaviour(self):
        res = self.client.get(HOME)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['posts']), self.paginate_by)
        posts = Post.objects.order_by('-created')
        for i in range(self.paginate_by):
            self.assertEqual(posts[i].uuid, res.context['posts'][i].uuid)
        return

    def test_subsequent_page(self):
        res = self.client.get(f'{HOME}?page=2')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['posts']), self.paginate_by)
        posts = Post.objects.order_by('-created')
        for i in range(self.paginate_by):
            self.assertEqual(posts[self.paginate_by + i].uuid, res.context['posts'][i].uuid)
        return

    def test_session_user(self):
        posts = Post.objects.order_by('-created')
        rated = {}
        rate_options = list(range(self.paginate_by))
        random.shuffle(rate_options)
        for i in range(5):
            rated[rate_options[i]] = random.randrange(Rating.MIN_RATING, Rating.MAX_RATING+1)
            Rating.objects.create(
                session_key=self.client.session.session_key,
                post=posts[rate_options[i]],
                rate=rated[rate_options[i]],
            )

        res = self.client.get(HOME)
        self.assertEqual(res.status_code, 200)
        for i in range(self.paginate_by):
            if i in rated:
                self.assertEqual(res.context['posts'][i].rate, rated[i])
            else:
                self.assertEqual(res.context['posts'][i].rate, None)
        return

    def test_login_user(self):
        user = User.objects.create(username='new_user', email='new_user')
        user.set_password('password')
        user.save()
        Settings.objects.create(user=user)
        res = self.client.login(username='new_user', password='password')
        self.assertTrue(res)

        posts = Post.objects.order_by('-created')
        rated = {}
        rate_options = list(range(self.paginate_by))
        random.shuffle(rate_options)
        for i in range(5):
            rated[rate_options[i]] = random.randrange(Rating.MIN_RATING, Rating.MAX_RATING+1)
            Rating.objects.create(
                user=user,
                post=posts[rate_options[i]],
                rate=rated[rate_options[i]],
            )

        res = self.client.get(HOME)
        self.assertEqual(res.status_code, 200)
        for i in range(self.paginate_by):
            if i in rated:
                self.assertEqual(res.context['posts'][i].rate, rated[i])
            else:
                self.assertEqual(res.context['posts'][i].rate, None)
        return

    def test_hidden_post(self):
        post = Post.objects.create(user=self.user)
        PostImage.objects.create(image='.', post=post)
        res = self.client.get(HOME)
        self.assertEqual(res.context['posts'][0].uuid, post.uuid)
        post.show = False
        post.save()
        res = self.client.get(HOME)
        self.assertNotEqual(res.context['posts'][0].uuid, post.uuid)
        post.delete()
        return


class TestUserPostsView(TestCase):
    def test_single_user(self):
        u0 = create_user()
        count = 10
        posts = create_posts(u0, count)
        res = self.client.get(USER_POSTS.replace(STR_TKN, u0.username))
        for i in range(count):
            self.assertEqual(res.context['posts'][i].uuid, posts[count - 1 - i].uuid)
        return

    def test_multiple_users(self):
        u0 = create_user('0')
        u1 = create_user('1')
        count = 10
        for _ in range(count):
            create_posts(u0)
            create_posts(u1)
        res = self.client.get(USER_POSTS.replace(STR_TKN, u0.username))
        posts = u0.post_set.order_by('-id')
        for i in range(count):
            self.assertEqual(res.context['posts'][i].uuid, posts[i].uuid)
        res = self.client.get(USER_POSTS.replace(STR_TKN, u1.username))
        posts = u1.post_set.order_by('-id')
        for i in range(count):
            self.assertEqual(res.context['posts'][i].uuid, posts[i].uuid)
        return

    def test_hidden_post(self):
        u0 = create_user()
        count = 10
        create_posts(u0, count)
        posts = create_posts(u0, count)
        posts[0].show = False
        posts[0].save()
        for i in range(1, count):
            if random.random() > 0.8:
                posts[i].show = False
                posts[i].save()
        posts = u0.post_set.filter(show=True).order_by('-id')
        res = self.client.get(USER_POSTS.replace(STR_TKN, u0.username))
        for i in range(count):
            self.assertEqual(res.context['posts'][i].uuid, posts[i].uuid)
        return


class TestPostDetailModalView(TestCase):
    def test_normal_post(self):
        u0 = create_user()
        post = create_posts(u0, 1)[0]
        res = self.client.get(POST_DETAIL.replace(STR_TKN, str(post.uuid)))
        self.assertEqual(res.context['post'].uuid, post.uuid)
        return

    def test_hidden_post(self):
        u0 = create_user()
        post = create_posts(u0, 1)[0]
        post.show = False
        post.save()
        res = self.client.get(POST_DETAIL.replace(STR_TKN, str(post.uuid)))
        self.assertEqual(res.status_code, 404)
        return


class TestFollowView(TestCase):#TODO test me
    def test_follow_no_user(self):
        return

    def test_follow_single_user(self):
        return

    def test_follow_multiple_user(self):
        return

    def test_follow_with_hidden_post(self):
        return
