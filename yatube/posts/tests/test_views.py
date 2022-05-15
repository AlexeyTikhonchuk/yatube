import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='SomeName')
        cls.group_1 = Group.objects.create(
            title='SomeGroup1',
            slug='1',
            description='Тестовая группа 1'
        )
        cls.group = Group.objects.create(
            title='SomeGroup2',
            slug='2',
            description='Тестовая группа 2'
        )
        small_gif = (
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
        )
        cls.post = Post.objects.create(
            text='Некоторый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Страницы используют верные шаблоны"""
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': '2'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'SomeName'}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create.html',
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}):
                'posts/create.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def post_check(self, response):
        self.assertIn('page_obj', response.context)
        post = response.context['page_obj'][0]

        self.assertEqual(post.author, self.user)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_index_page_context_is_correct(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.client.get(reverse('posts:index'))
        self.post_check(response)

    def test_group_page_context_is_correct(self):
        """Шаблон group сформирован с правильным контекстом"""
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': '2'}))
        group = response.context['group']
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.post_check(response)

    def test_profile_page_context_is_correct(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'SomeName'}))
        user = response.context['author']
        self.assertEqual(user.username, self.user.username)
        self.post_check(response)

    def test_post_detail_page_contains_one_right_post(self):
        """Страница поста содержит соответсвующий пост"""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(response.context['post'],
                         self.post)

    def test_post_detail_page_contains_image(self):
        """Страница поста содержит картинку"""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(response.context['post'].image,
                         'posts/small.gif')

    def test_pages_show_correct_context(self):
        """Шаблоны create и post_edit сформированы с правильным контекстом."""
        urls = (reverse('posts:post_create'),
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': f'{self.post.id}'})
                )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField
        }
        for url in urls:
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_in_lists(self):
        """Новый пост появляется на всех необходимых страницах"""
        cache.clear()
        pages_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': '2'}),
            reverse('posts:profile', kwargs={'username': 'SomeName'})
        )
        self.post = Post.objects.create(
            text='Некоторый новый текст',
            author=self.user,
            group=self.group
        )
        for page in pages_names:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertContains(response, self.post)

    def test_post_not_in_other_group_lists(self):
        """Новый пост не появляется на странице не своей группы"""
        self.post = Post.objects.create(
            text='Некоторый новый текст',
            author=self.user,
            group=self.group
        )
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': '1'}))
        self.assertNotContains(response, self.post)

    def test_cache_index_page(self):
        """Кэширование страницы index работает"""
        response_1 = self.authorized_client.get(reverse('posts:index'))
        Post.objects.get(id=self.post.id).delete()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_1.content, response_2.content)

    def test_new_post_in_follow(self):
        """Новая запись пользователя появляется в ленте тех,
         кто на него подписан и не появляется в ленте тех, кто не подписан """
        user_2 = User.objects.create_user(username='SomeName_2')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(user_2)
        user_3 = User.objects.create_user(username='SomeName_3')
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(user_3)
        self.post = Post.objects.create(
            text='Некоторый новый текст',
            author=self.user,
            group=self.group
        )
        self.authorized_client_2.get(reverse('posts:profile_follow',
                                             kwargs={'username': 'SomeName'})
                                     )
        response = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        self.assertContains(response, self.post)
        response = self.authorized_client_3.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response, self.post)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='SomeName')
        cls.group = Group.objects.create(
            title='SomeGroup2',
            slug='2',
            description='Тестовая группа 2'
        )
        cls.amount_of_posts = 13
        cls.post = Post.objects.bulk_create(
            [Post(
                text=f'Текст {i}',
                author=cls.user,
                group=cls.group
            ) for i in range(1, cls.amount_of_posts + 1)]
        )

    def test_paginator(self):
        """Проверяем работу пагинатора"""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': '2'}),
            reverse('posts:profile', kwargs={'username': 'SomeName'})
        )
        rest = self.amount_of_posts - settings.POSTS_ON_PAGE
        for url in urls:
            pages = (
                (1, settings.POSTS_ON_PAGE),
                (2, rest)
            )
            for page, amount in pages:
                with self.subTest(page=page):
                    response = self.client.get(url, {'page': page})
                    self.assertEqual(len(response.context['page_obj']),
                                     amount)
