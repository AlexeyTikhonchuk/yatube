import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SomeName')
        cls.group = Group.objects.create(
            title='SomeGroup',
            slug='1',
            description='Тестовая группа'
        )
        '''small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )'''
        cls.post = Post.objects.create(
            text='Что-то тут написано',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_create(self):
        """Новый пост добавляется в БД"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_data = {
            'text': 'Некоторый текст',
            'group': self.group.id,
            'image': uploaded
        }
        posts = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts + 1)
        self.assertTrue(
            Post.objects.filter(
                text=post_data['text'],
                author=self.user,
                group=self.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Изменения поста сохраняются в БД"""
        post_data = {
            'text': 'Некоторый измененный текст',
            'group': {self.group.id}
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=post_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text=post_data['text'],
                author=self.user,
                group=self.group,
            ).exists()
        )

    def test_new_comment_create(self):
        """Добавляется новый комментарий"""
        comments = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': f'{self.post.id}'}),
            data={'text': 'новый комментарий'},
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='новый комментарий',
                author=self.user
            )
        )
