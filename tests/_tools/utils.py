from rmn_arch_0.users.models import User, Profile, Settings, Relations
from rmn_arch_0.posts.models import Post, PostImage

TEST_IMG_PATH = './rmn_arch_0/static/images/default_profile_img.png'

def create_user(username='username', password='password', email=None):
    """
    Returns a newly created user with all proper relational models
    """
    if email == None:
        email = f'{username}@m.com'
    user = User.objects.create(username=username, password=password, email=email)
    Profile.objects.create(user=user)
    Settings.objects.create(user=user)
    Relations.objects.create(user=user)
    return user

def create_posts(user, num=1):
    """
    Returns given num of newly created posts by given user with one blank image each
    """
    res = []
    for _ in range(num):
        post = Post.objects.create(user=user)
        PostImage.objects.create(image='.', post=post)
        res.append(post)
    return res
