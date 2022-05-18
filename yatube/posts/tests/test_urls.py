from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='SomeName')
        cls.user_2 = User.objects.create_user(username='SomeName_2')
        cls.group = Group.objects.create(
            title='SomeGroup',
            slug='2',
            description='Тестовая группа'
        )
        cls.post = Post.objects.create(
            text='Некоторый текст',
            created='05.05.05',
            author=cls.user,
            group=cls.group
        )
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_2)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
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
                'posts/create.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        url_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': '2'}),
            reverse('posts:profile', kwargs={'username': 'SomeName'}),
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'})
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location(self):
        """Страница '/create/' доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_url_exists_at_desired_location(self):
        """Страница '/follow/' доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_client_redirect(self):
        """Неавторизированный пользователь
        перенаправляется со страниц create, follow, post_edit."""
        urls = (reverse('posts:post_create'),
                reverse('posts:follow_index'),
                reverse('posts:post_edit',
                        kwargs={'post_id': f'{self.post.id}'}))
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_access(self):
        """Страница '/edit/' доступна  автору поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_not_access(self):
        """Страница '/edit/' не доступна не автору поста."""
        response = self.authorized_client_2.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.post.id}'}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_comment_access_auth_user(self):
        """Авторизованный пользователь может комментировать посты"""
        response = self.authorized_client_2.get(reverse(
            'posts:add_comment', kwargs={'post_id': f'{self.post.id}'}))
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': f'{self.post.id}'}))

    def test_guest_user_can_not_comment(self):
        """Неавторизованный пользователь не может комментировать посты"""
        response = self.guest_client.get(reverse(
            'posts:add_comment', kwargs={'post_id': f'{self.post.id}'}))
        self.assertRedirects(response,
                             (f'/auth/login/?next=/posts/{self.post.id}'
                              f'/comment/'))

    def test_auth_user_can_follow(self):
        """Авторизованный пользователь может подписываться
         на других пользователей и удалять их из подписок """
        names = ('posts:profile_follow', 'posts:profile_unfollow')
        for name in names:
            with self.subTest(name=name):
                response = self.authorized_client_2.get(
                    reverse(name, kwargs={'username': 'SomeName'})
                )
                self.assertRedirects(response, reverse(
                    'posts:profile', kwargs={'username': 'SomeName'}))

    def test_guest_user_cannot_follow(self):
        """Неавторизованный пользователь не может подписываться
         на других пользователей и удалять их из подписок """
        names = ('follow', 'unfollow')
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(
                    reverse(f'posts:profile_{name}',
                            kwargs={'username': 'SomeName'})
                )
                self.assertRedirects(
                    response,
                    f'/auth/login/?next=/profile/{self.user.username}/{name}/'
                )
