from django.test import TestCase
from posts.models import Group, Post, User
from django.core.cache import cache


EVERYTHING_MAGIC = 15


class PostsModelsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост тестового пользователя в тестовой группе',
        )

    def setUp(self) -> None:
        super().setUp()
        cache.clear()

    def test_group_object_name(self):
        """Проверяем, что у модели group корректно работает __str__."""
        group = PostsModelsTests.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

    def test_post_object_name(self):
        """Проверяем, что у модели post корректно работает __str__."""
        post = PostsModelsTests.post
        expected_post_str = post.text[:EVERYTHING_MAGIC]
        self.assertEqual(expected_post_str, str(post))

    def test_post_verbose_name(self):
        """Проверяем, что verbose_name в полях совпадает с ожидаемым."""
        post = PostsModelsTests.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_verbose in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_verbose
                )

    def test_post_help_text(self):
        """Проверяем, что help_texts в полях совпадает с ожидаемым."""
        post = PostsModelsTests.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_help_text in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_help_text
                )
