from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .._tools.utils import TEST_IMG_PATH
from rmn_arch_0.posts.forms import PostForm
from rmn_arch_0.users.models import User


class TestPostForm(TestCase):
    def test_stripping_return_carriage(self):
        user = User.objects.create()
        desc = 'test\r\ntest\r\nend'
        data = {'description': desc}
        with open(TEST_IMG_PATH, 'rb') as img:
            files = {'images': SimpleUploadedFile(img.name, img.read())}
        pf = PostForm(data=data, files=files)
        self.assertTrue(pf.is_valid())
        post = pf.save(commit=False)
        post.user = user
        post.save()
        self.assertEqual(post.description, desc.replace('\r', ''))
        return
