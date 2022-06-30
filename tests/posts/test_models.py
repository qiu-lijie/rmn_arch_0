from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.test import TestCase
from django.urls.base import reverse

from random import randrange

from rmn_arch_0.posts.models import (
    AnonymousUserMixIn,
    Post,
    PostImage,
    Rating,
    Comment,
    Report,
    )
from rmn_arch_0.users.models import User, Profile, Settings


class UserPostTestCase(TestCase):
    """
    Setup a user and post for later use
    """
    def setUp(self):
        super().setUp()
        self.user = User()
        self.user.save()
        self.settings = Settings.objects.create(user=self.user)
        self.post = Post(user=self.user)
        self.post.save()
        return


class TestAnonymousUserMixIn(UserPostTestCase):
    def test_anonymous_user_display_name(self):
        name = 'testUser'
        Profile.objects.create(user=self.user, name=name)
        self.assertEqual(self.post.user_display_name, name)
        self.post.anonymous = True
        self.assertEqual(self.post.user_display_name, Post.ANONYMOUS_USER)
        return

    def test_anonymous_profile_image_url(self):
        profile = Profile.objects.create(user=self.user)
        image_path = 'random/image.jpg'
        profile.image = image_path
        profile.save()
        self.assertEqual(self.post.user_display_image_url, f'/media/{image_path}')
        self.post.anonymous = True
        self.assertEqual(self.post.user_display_image_url, AnonymousUserMixIn.ANONYMOUS_IMAGE)
        return
    
    def test_anonymous_profile_image_url_user_no_img(self):
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(self.post.user_display_image_url, AnonymousUserMixIn.ANONYMOUS_IMAGE)
        self.post.anonymous = True
        self.assertEqual(self.post.user_display_image_url, AnonymousUserMixIn.ANONYMOUS_IMAGE)
        return


class TestPost(UserPostTestCase):
    def test_standard_post(self):
        name = 'testUser'
        Profile.objects.create(user=self.user, name=name)
        self.assertEqual(self.post.user_display_name, name)
        return

    def test_image_count(self):
        post_count = 5
        for _ in range(5):
            image = PostImage(post=self.post, image='.')
            image.full_clean()
            image.save()
        self.assertEqual(self.post.image_count, 5)
        return

    def test_rating_count(self):
        rating_count = 5
        for i in range(rating_count):
            rating = Rating(post=self.post, session_key=f'k{i}', rate=3)
            rating.full_clean()
            rating.save()
        self.assertEqual(self.post.rating_count, rating_count)
        return

    def test_comment_count(self):
        comment_count = 5
        for i in range(comment_count):
            user = User(username=f't{i}', email=f't{i}')
            user.save()
            comment = Comment(post=self.post, user=self.user)
            comment.save()
        self.assertEqual(self.post.comment_count, comment_count)
        return

    def test_report_count(self):
        report_count = 5
        for i in range(report_count):
            user = User(username=f't{i}', email=f't{i}')
            user.save()
            report = Report(post=self.post, user=user, reason=f'r{i}', description='test')
            report.save()
        self.assertEqual(self.post.report_count, report_count)
        return

    def test_report_notifiaction(self):
        self.user.email = 'test0@m.com'
        self.user.save()
        self.assertEqual(len(mail.outbox), 0)
        self.post.report_notification()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Your Post {self.post.uuid} Has Been Hidden')
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(mail.outbox[0].to, [self.post.user.email])
        return

    def test_avg_rating(self):
        rating_count = 50
        acc = 0
        for i in range(rating_count):
            rating = randrange(Rating.MIN_RATING, Rating.MAX_RATING+1)
            acc += rating
            rating = Rating(post=self.post, session_key=f'k{i}', rate=rating)
            rating.full_clean()
            rating.save()
        self.assertEqual(self.post.avg_rate, acc / rating_count)
        return

    def test_rank_rating(self):
        rating_count = 50
        acc = 0
        for i in range(rating_count):
            rating = randrange(Rating.MIN_RATING, Rating.MAX_RATING+1)
            acc += rating
            rating = Rating(post=self.post, session_key=f'k{i}', rate=rating)
            rating.full_clean()
            rating.save()
        rank_rating = ((acc + Post.STABLE_RATING * Post.NUM_STABLE_RATING)
            / (rating_count + Post.NUM_STABLE_RATING))
        self.assertEqual(self.post.rank_rate, rank_rating)
        return

    def test_thumbnail_image_url(self):
        for i in range(PostImage.MAX_IMAGES):
            image = PostImage(post=self.post, image=f'image_{i}.jpg')
            image.full_clean()
            image.save()
        self.assertEqual(self.post.thumbnail_image_url, f'/media/image_0.jpg')
        return

    def test_get_absolute_url(self):
        self.user.username = 'testusername'
        self.assertEqual(self.user.get_absolute_url(),
            reverse('posts:user_posts', kwargs={'username':self.user.username}))
        return

    NAME = 'name'
    IMAGE = 'image'

    def test_rating_summary_no_ratings(self):
        summary = self.post.rating_summary()
        self.assertIsNone(summary[self.NAME])
        self.assertIsNone(summary[self.IMAGE])
        return

    def test_rating_summary_session_ratings_only(self):
        Rating.objects.create(session_key=f'sk', post=self.post, rate=3)
        summary = self.post.rating_summary()
        self.assertEqual(summary[self.NAME], Post.ANONYMOUS_USER)
        self.assertEqual(summary[self.IMAGE], Post.ANONYMOUS_IMAGE)
        for i in range(3):
            Rating.objects.create(session_key=f's{i}', post=self.post, rate=3)
        summary = self.post.rating_summary()
        self.assertEqual(summary[self.NAME], Post.ANONYMOUS_USER)
        self.assertEqual(summary[self.IMAGE], Post.ANONYMOUS_IMAGE)
        return

    def test_rating_summary_anon_ratings_only(self):
        Rating.objects.create(user=self.user, anonymous=True, post=self.post, rate=3)
        summary = self.post.rating_summary()
        self.assertEqual(summary[self.NAME], Post.ANONYMOUS_USER)
        self.assertEqual(summary[self.IMAGE], Post.ANONYMOUS_IMAGE)
        for i in range(3):
            user = User.objects.create(username=f'u{i}', email=f'u{i}')
            Settings.objects.create(user=user)
            Rating.objects.create(user=user, anonymous=True, post=self.post, rate=3)
        summary = self.post.rating_summary()
        self.assertEqual(summary[self.NAME], Post.ANONYMOUS_USER)
        self.assertEqual(summary[self.IMAGE], Post.ANONYMOUS_IMAGE)
        return

    def test_rating_summary_named_user(self):
        first_rated_user_name = 'First Rated User'
        first_rated_user_image = 'first_rated_user_image.jpg'
        first_rated_user = User.objects.create(username='xxx', email='xxx')
        Settings.objects.create(user=first_rated_user)
        Profile.objects.create(user=first_rated_user, name=first_rated_user_name, image=first_rated_user_image)
        Rating.objects.create(user=first_rated_user, post=self.post, rate=3)
        summary = self.post.rating_summary()
        self.assertEqual(summary[self.NAME], first_rated_user_name)
        self.assertEqual(summary[self.IMAGE], f'/media/{first_rated_user_image}')

        # add more ratings to make sure the first is still first
        for i in range(3):
            user = User.objects.create(username=f'u{i}', email=f'u{i}')
            Settings.objects.create(user=user)
            Rating.objects.create(user=user, post=self.post, rate=3)
            user = User.objects.create(username=f'ua{i}', email=f'ua{i}')
            Settings.objects.create(user=user)
            Rating.objects.create(user=user, anonymous=True, post=self.post, rate=3)
            Rating.objects.create(session_key=f's{i}', post=self.post, rate=3)
        summary = self.post.rating_summary()
        self.assertEqual(summary[self.NAME], first_rated_user_name)
        self.assertEqual(summary[self.IMAGE], f'/media/{first_rated_user_image}')
        return


class TestPostImage(UserPostTestCase):
    def test_clean_within_limit(self):
        for _ in range(PostImage.MAX_IMAGES):
            image = PostImage(post=self.post, image='.')
            image.full_clean()
            image.save()
        return

    def test_clean_outside_limit(self):
        for _ in range(PostImage.MAX_IMAGES):
            image = PostImage(post=self.post, image='.')
            image.full_clean()
            image.save()
        
        with self.assertRaisesMessage(ValidationError,
            f'Only {PostImage.MAX_IMAGES} images per post allowed'):
            image = PostImage(post=self.post, image='.')
            image.full_clean()
            image.save()
        return

    def test_save_call_full_clean(self):
        for _ in range(PostImage.MAX_IMAGES):
            image = PostImage(post=self.post, image='.')
            image.save()
        
        with self.assertRaisesMessage(ValidationError,
            f'Only {PostImage.MAX_IMAGES} images per post allowed'):
            image = PostImage(post=self.post, image='.')
            image.save()
        return


class TestRating(UserPostTestCase):
    def test_rating_min(self):
        rating = Rating(user=self.user, post=self.post, rate=Rating.MIN_RATING)
        rating.full_clean()
        rating.save()

        post = Post(user=self.user)
        post.save()
        rating = Rating(user=self.user, post=post, rate=Rating.MIN_RATING-1)
        with self.assertRaisesMessage(ValidationError,
            f'Ensure this value is greater than or equal to {Rating.MIN_RATING}'):
            rating.full_clean()
        return

    def test_rating_max(self):
        rating = Rating(user=self.user, post=self.post, rate=Rating.MAX_RATING+1)
        with self.assertRaisesMessage(ValidationError,
            f'Ensure this value is less than or equal to {Rating.MAX_RATING}'):
            rating.full_clean()
        return

    def test_session_uniqueness(self):
        session_key = '5egnljcgzyfrlnjvr953log61nmg5abc'
        rating = Rating(session_key=session_key, post=self.post, rate=3)
        rating.full_clean()
        rating.save()

        rating = Rating(session_key=session_key, post=self.post, rate=3)
        with self.assertRaisesMessage(ValidationError,
            'Rating with this Session key and Post already exists.'):
            rating.full_clean()
        return

    def test_user_uniqueness(self):
        rating = Rating(user=self.user, post=self.post, rate=3)
        rating.full_clean()
        rating.save()

        rating = Rating(user=self.user, post=self.post, rate=3)
        with self.assertRaisesMessage(ValidationError,
            'Rating with this User and Post already exists.'):
            rating.full_clean()
        return

    def test_no_user_and_session(self):
        rating = Rating(post=self.post, rate=3)
        with self.assertRaisesMessage(ValidationError,
            'One of user or session_key should be set, not both'):
            rating.full_clean()
        return
    
    def test_both_user_and_session(self):
        session_key = '5egnljcgzyfrlnjvr953log61nmg5abc'
        rating = Rating(user=self.user, session_key=session_key, post=self.post, rate=3)
        with self.assertRaisesMessage(ValidationError,
            'One of user or session_key should be set, not both'):
            rating.full_clean()
        return


class TestReport(UserPostTestCase):
    def test_uniqueness(self):
        report = Report(user=self.user, post=self.post, reason='r0', description='test')
        report.full_clean()
        report.save()
        report = Report(user=self.user, post=self.post, reason='r0', description='test')
        with self.assertRaisesMessage(ValidationError,
            'Report with this User and Post already exists.'):
            report.full_clean()
        return

    def test_save_auto_hidden(self):
        self.user.email = 'test@m.com'
        self.user.save()

        for i in range(Report.REPORT_THRESHOLD):
            user = User(username=f't{i}', email=f't{i}')
            user.save()
            report = Report(user=user, post=self.post, reason='r0', description='test')
            report.full_clean()
            report.save()

        # test reportable
        self.assertTrue(report.post.reportable)
        self.assertTrue(report.post.show)
        user = User(username='t00', email='t00')
        user.save()
        report = Report(user=user, post=self.post, reason='r0', description='test')
        report.full_clean()
        report.save()
        self.assertTrue(report.post.reportable)
        self.assertFalse(report.post.show)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Your Post {report.post.uuid} Has Been Hidden')
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(mail.outbox[0].to, [self.post.user.email])

        # test non-reportable
        self.post.show = True
        self.post.reportable = False
        self.post.save()
        mail.outbox = []
        self.assertFalse(report.post.reportable)
        self.assertTrue(report.post.show)
        user = User(username='t01', email='t01')
        user.save()
        report = Report(user=user, post=self.post, reason='r0', description='test')
        report.full_clean()
        report.save()
        self.assertFalse(report.post.reportable)
        self.assertTrue(report.post.show)
        self.assertEqual(len(mail.outbox), 0)
        return


class TestSettings(UserPostTestCase):
    def test_rate_anon(self):
        post = Post.objects.create(user=self.user)
        rating = Rating.objects.create(user=self.user, post=post, rate=3)
        self.assertFalse(rating.anonymous)
        self.settings.rate_anon = True
        post = Post.objects.create(user=self.user)
        rating = Rating.objects.create(user=self.user, post=post, rate=3)
        self.assertTrue(rating.anonymous)
        return

    def test_comment_anon(self):
        comment = Comment.objects.create(user=self.user, post=self.post, description='')
        self.assertFalse(comment.anonymous)
        self.settings.comment_anon = True
        comment = Comment.objects.create(user=self.user, post=self.post, description='')
        self.assertTrue(comment.anonymous)
        return
