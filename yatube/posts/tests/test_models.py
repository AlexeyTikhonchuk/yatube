from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.group = Group.objects.create(
            title='Название тестовой группы',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Некоторый текст длиннее 15 символов',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий, йоу'
        )
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        models_str = {
            post: 'Некоторый текст',
            group: 'Название тестовой группы',
        }
        for value, expected in models_str.items():
            with self.subTest(value=value):
                self.assertEqual(
                    str(value), expected
                )

    def test_post_verbose_names(self):
        """verbose_name в полях модели post совпадает с ожидаемым."""
        post = self.post
        field_verboses = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_group_verbose_names(self):
        """verbose_name в полях модели group совпадает с ожидаемым."""
        group = self.group
        field_verboses = {
            'title': 'Название группы',
            'description': 'Описание группы',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_comment_verbose_names(self):
        """verbose_name в полях модели comment совпадает с ожидаемым."""
        comment = self.comment
        field_verboses = {
            'text': 'Текст комментария',
            'author': 'Автор',
            'post': 'Пост',
            'created': 'Дата создания',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)

    def test_follow_verbose_names(self):
        """verbose_name в полях модели follow совпадает с ожидаемым."""
        follow = self.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)

    def test_post_help_text(self):
        """help_text в полях post совпадает с ожидаемым."""
        post = self.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_group_help_text(self):
        """help_text в полях group совпадает с ожидаемым."""
        group = self.group
        field_help_texts = {
            'title': 'Придумайте название группе',
            'description': 'Опишите группу',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)

    def test_comment_help_text(self):
        """help_text в полях comment совпадает с ожидаемым."""
        comment = self.comment
        self.assertEqual(
            comment._meta.get_field('text').help_text,
            'Введите текст комментария')
