import logging
import os
import random
import sys
import uuid
from faker import Faker
from mando import command, main
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(BASE_DIR.as_posix())

import django
django.setup()

from tests._tools.utils import create_user
from rmn_arch_0.users.models import User
from rmn_arch_0.posts.models import Post, PostImage, Rating, Comment


FK = Faker()
SAMPLE_IMAGE_PATH = './media/'

@command
def create_users(cnt=5):
    for i in range(cnt):
        user = create_user(username=f'faker{i}_{str(uuid.uuid4())[:5]}')
        logging.info(f'Successfuly created {user}')
    return


@command
def create_posts(cnt=10):
    """
    Create given number of posts for the latest users
    """
    users = list(User.objects.all())
    for _ in range(cnt):
        user = random.choice(users)
        post = Post.objects.create(
            user = user,
            anonymous = (True if random.random() < 0.5 else False),
        )
        post.anonymous = True if random.random() < 0.5 else False
        post.save()
        imgs = [f for f in os.listdir(SAMPLE_IMAGE_PATH) if os.path.isfile(SAMPLE_IMAGE_PATH + f)]
        random.shuffle(imgs)
        for __ in range(random.randrange(1, 4)):
            PostImage.objects.create(post=post, image=imgs.pop())
        logging.info(
            f'Successfuly created {post} with {post.image_count} image(s) for {user}')
    return


@command
def create_ratings(cnt=10):
    users = list(User.objects.all())
    for post in Post._base_manager.order_by('-id')[:cnt]:
        for _ in range(random.randrange(2, 6)):
            user = random.choice(users)
            try:
                Rating.objects.create(
                    post=post, user=user, rate=random.randrange(1, 6),
                    anonymous = (True if random.random() < 0.5 else False),
                )
            except: pass
        logging.info(f'Successfuly created rating for {post}')
    return


@command
def create_comments(cnt=25, last_n=3):
    users = list(User.objects.all())
    for post in Post._base_manager.order_by('-id')[:last_n]:
        for _ in range(cnt):
            user = random.choice(users)
            Comment.objects.create(
                post=post, user=user, description=FK.text()[:100],
                anonymous = (True if random.random() < 0.5 else False),
            )
        logging.info(f'Successfuly created {cnt} comments for {post}')
    return


@command
def create_content(cnt=5):
    create_users(cnt)
    create_posts(cnt*2)
    create_ratings(cnt*2)
    return


if __name__ == "__main__":
    main()
