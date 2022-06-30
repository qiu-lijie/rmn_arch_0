from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.templatetags.static import static
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel
import uuid

from rmn_arch_0.users.models import User


def post_img_path(instance, filename):
    """
    File path for post images
    """
    return f'uploads/posts/{instance.post.uuid}/{filename}'


class AnonymousUserMixIn(models.Model):
    """
    Mixin for allowing user to post anonymously
    """
    ANONYMOUS_USER = 'Anonymous User'
    ANONYMOUS_IMAGE = static('images/default_profile_img.png')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def user_display_name(self):
        """
        Return the user.name if anaymous == false, else self.ANONYMOUS_USER
        """
        return self.ANONYMOUS_USER if self.anonymous else self.user.name
    
    @property
    def user_display_image_url(self):
        """
        Return the user.profile_image_url if anaymous is false, else default_profile_img.png
        """
        return self.ANONYMOUS_IMAGE if self.anonymous else self.user.profile_image_url


class Post(AnonymousUserMixIn, TimeStampedModel):
    """
    Model for posting pictures
    """
    NUM_STABLE_RATING = 100
    STABLE_RATING = 3
    MIN_RATINGS_TO_SHOW = 5

    reportable = models.BooleanField(default=True)
    show = models.BooleanField(default=True)
    description = models.CharField(max_length=100, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f'Post {str(self.uuid)[:8]}'

    @property
    def image_count(self):
        return self.postimage_set.count()

    @property
    def rating_count(self):
        return self.rating_set.count()

    @property
    def comment_count(self):
        return self.comment_set.count()

    @property
    def report_count(self):
        return self.report_set.count()

    @property
    def avg_rate(self):
        """
        Return the average rating as a float
        """
        return self.rating_set.aggregate(models.Avg('rate'))['rate__avg']

    @property
    def rank_rate(self):
        """
        Return the rating used for rankings as a float
        note this should only be used for testing, actual ranking should be done
        with database query
        """
        rate_sum = self.rating_set.aggregate(models.Sum('rate'))['rate__sum']
        stable_sum = self.STABLE_RATING * self.NUM_STABLE_RATING
        return (rate_sum + stable_sum) / (self.rating_count + self.NUM_STABLE_RATING)

    @property
    def thumbnail_image_url(self):
        """
        Return the first image url as thumbnail
        """
        return self.postimage_set.first().image.url

    def get_absolute_url(self):
        """
        Returns the PostDetailView of the post
        """
        return reverse('posts:post_detail', kwargs={'uuid':self.uuid})

    def report_notification(self):
        """
        Notify the user that their Post has been hidden due to reports
        Return 1 if successful, 0 otherwise
        """
        return send_mail(
                f'Your Post {self.uuid} Has Been Hidden',
                f'Your Post {self.uuid} has been hidden due to user reports', #TODO refine
                None,
                [self.user.email],
                fail_silently=True
                )

    def rating_summary(self):
        """
        Return a dict of name and image of the first rated user
            will return first name rated user if available, anoymous name and image otherwise
            both name and image will be none if no rating available
        """
        NAME = 'name'
        IMAGE = 'image'
        res = {IMAGE: None, NAME: None}
        if self.rating_count != 0:
            rating = self.rating_set.filter(user__isnull=False, anonymous=False).first()
            if rating:
                res[IMAGE] = rating.user.profile_image_url
                res[NAME] = rating.user.name
            else:
                res[IMAGE] = self.ANONYMOUS_IMAGE
                res[NAME] = self.ANONYMOUS_USER
        return res


class PostImage(models.Model):
    """
    Model for storing post images
    """
    MAX_IMAGES = 9

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=post_img_path)

    def __str__(self):
        return f'Image {self.image} for {self.post}'

    def clean(self):
        """
        Raise ValidationError if maximun number of image for this post is reached
        """
        if PostImage.objects.filter(post=self.post).count() >= self.MAX_IMAGES:
            raise ValidationError(f'Only {self.MAX_IMAGES} images per post allowed')
        return super().clean()

    def save(self, **kwargs):
        """
        Override save to call full_clean -> clean defined above
        """
        self.full_clean()
        return super().save(**kwargs)


class Rating(AnonymousUserMixIn):
    """
    Model for storing user ratings on Posts
    """
    MIN_RATING = 1
    MAX_RATING = 5

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)   # allows null in db for uniquness
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    rate = models.PositiveSmallIntegerField(validators=[
        MinValueValidator(MIN_RATING),
        MaxValueValidator(MAX_RATING),
    ])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user'),
            models.UniqueConstraint(fields=['session_key', 'post'], name='unique_session_key'),
        ]
    
    def __str__(self):
        return f'Rating {self.rate} by {self.user if self.user else self.session_key}, for {self.post}'
    
    def clean(self):
        """
        Pass if and only if one of user or session_key is set, otherwise riase ValidationError
        """
        if (self.user and self.session_key) or not (self.user or self.session_key):
            raise ValidationError(f'One of user or session_key should be set, not both')
        return super().clean()

    def save(self, **kwargs):
        """
        Override save to call full_clean -> clean defined above
        Respect user anonymity settings if applicable
        """
        self.full_clean()
        if self.user and self.user.settings.rate_anon:
            self.anonymous = True
        return super().save(**kwargs)


class Comment(AnonymousUserMixIn, TimeStampedModel):
    """
    Model for storing user comments on Posts
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)

    def __str__(self):
        return f'Comment by {self.user}, for {self.post}'

    def save(self, **kwargs):
        """
        Respect user anonymity settings if applicable
        """
        if self.user.settings.comment_anon:
            self.anonymous = True
        return super().save(**kwargs)


class Report(TimeStampedModel):
    """
    Model for allowing user to report Posts
    """
    REPORT_THRESHOLD = 20

    R_OTHER = 'r0'
    R_COPYRIGHT = 'r1'
    R_MINOR = 'r2'
    R_HATE = 'r3'
    R_SPAM = 'r4'
    REASONS = [
        (R_COPYRIGHT, 'My images used without concent'),
        (R_MINOR, 'Featuring minors'),
        (R_HATE, 'Hateful content'),
        (R_SPAM, 'Spam or commercial content'),
        (R_OTHER, 'Other reasons'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reason = models.CharField(max_length=2, choices=REASONS, default=R_OTHER)
    description = models.CharField(max_length=500)

    class Meta():
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_user_report'),
        ]

    def __str__(self):
        return f'Report by {self.user}, for {self.post}'

    def save(self, **kwargs):
        """
        Override save to check if given post has been reported excessively
        if the post is reportable and has been reported more than threshold, it will be hidden
        and notification will be sent
        """
        super().save(**kwargs)
        if (self.post.reportable 
            and self.post.show
            and self.post.report_set.count() > self.REPORT_THRESHOLD):
            self.post.show = False
            self.post.save()
            self.post.report_notification()
        return
