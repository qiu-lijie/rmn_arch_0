from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta


def profile_img_path(instance, filename):
    """
    File path for profile images
    """
    return f'uploads/user_{instance.user.username}/profile/{filename}'


class User(AbstractBaseUser, PermissionsMixin):
    """
    Used for AUTH_USER_MODEL
    """
    username = models.CharField(max_length=16, unique=True, validators=[ASCIIUsernameValidator()])
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'email',]
    objects = UserManager()

    def __str__(self):
        return f'User {self.username}'

    def get_absolute_url(self):
        """
        Returns the UserPostsView of the user
        """
        return reverse('posts:user_posts', kwargs={'username':self.username})

    @property
    def name(self):
        return self.profile.name

    @property
    def profile_image_url(self):
        """
        Returns the user's profile image url if available,
        otherwise return the default_profile_img.png url
        """
        if self.profile.image:
            return self.profile.image.url
        else:
            return static('images/default_profile_img.png')

    @property
    def post_count(self):
        return self.post_set.count()

    def pub_post_count(self):
        return self.post_set.filter(anonymous=False, show=True).count()

    def follower_count(self):
        return self.followers.count()

    def following_count(self):
        return self.relations.follows.count()


class Profile(models.Model):
    """
    Profile for individual users
    """
    MALE = 'm'
    FEMALE = 'f'
    OTHER = 'o'
    NA = ''
    GENDERS = [
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (OTHER, 'Other'),
        (NA, 'Prefer not to say'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    gender = models.CharField(max_length=1, blank=True, choices=GENDERS)
    birthday = models.DateField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to=profile_img_path)
    location = models.ForeignKey('cities_light.City', blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return f'Profile for {self.user}'

    @property
    def age(self):
        """
        Return the age of the profile if birthday is set, None otherwise
        """
        if self.birthday is None:
            return None
        else:
            today = timezone.now()
            return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))


class Settings(models.Model):
    """
    Settings for individual users
    """
    ALL = 'all'
    FOLLOW = 'follow'
    BLOCK = 'block'
    MSG_SETTINGS = [
        (ALL, 'Receive all new messages'),
        (FOLLOW, 'Receive new messages only from users I follow'),
        (BLOCK, 'Block all new messages'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rate_anon = models.BooleanField(default=False)
    comment_anon = models.BooleanField(default=False)
    rec_new_msg = models.CharField(max_length=8, choices=MSG_SETTINGS, default=ALL)

    class Meta:
        verbose_name_plural = 'Settings'

    def __str__(self):
        return f'Settings for {self.user}'


class Relations(models.Model):
    """
    Relations for individual users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    follows = models.ManyToManyField(User, related_name='followers')

    class Meta:
        verbose_name_plural = 'Relations'

    def __str__(self):
        return f'Relations for {self.user}'
