from django.test import Client, TestCase
from posts.models import Group, Post, User
from django.core.cache import cache
from django.urls import reverse
from http import HTTPStatus


class PostsURLsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_not_author = User.objects.create_user(
            username='test_user_not_author'
        )
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

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client_not_author = Client()
        self.auth_client.force_login(PostsURLsTests.user)
        self.auth_client_not_author.force_login(PostsURLsTests.user_not_author)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """Проверяем, что страницы доступны любому пользователю."""
        group = PostsURLsTests.group
        user = PostsURLsTests.user
        post = PostsURLsTests.post
        url_names = [
            '/',
            f'/group/{group.slug}/',
            f'/profile/{user.username}/',
            f'/posts/{post.pk}/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                guest_response = self.guest_client.get(address, follow=True)
                auth_response = self.auth_client.get(address)
                self.assertEqual(guest_response.status_code, HTTPStatus.OK)
                self.assertEqual(auth_response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Проверяем, что страницы доступны авторизованному пользователю."""
        post = PostsURLsTests.post
        post_id = self.post.id
        address = reverse('posts:post_edit', kwargs={'post_id': post_id})
        guest_response = self.guest_client.get(address, follow=True)
        auth_response = self.auth_client.get(address)
        self.assertRedirects(
            guest_response,
            f'/auth/login/?next=/posts/{post.pk}/edit/'
        )
        self.assertEqual(auth_response.status_code, HTTPStatus.OK)

    def test_create_post_url_exists_at_desired_location(self):
        """Проверям, что страница /create/ перенаправит пользователя
        на страницу логина."""
        address = reverse(
            "posts:post_create"
        )
        guest_response = self.guest_client.get(address, follow=True)
        auth_response = self.auth_client.get(address)
        self.assertRedirects(
            guest_response,
            f'{"/auth/login/?next=/create/"}'
        )
        self.assertEqual(auth_response.status_code, HTTPStatus.OK)

    def test_404_error_return_for_unexisting_page(self):
        """Проверяем работоспособность запроса к несуществующей странице"""
        address = f'{"/fake_page/"}'
        guest_response = self.guest_client.get(address, follow=True)
        auth_response = self.auth_client.get(address)
        self.assertEqual(guest_response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(auth_response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Проверяем, что URL использует соответствующий шаблон."""
        group = PostsURLsTests.group
        user = PostsURLsTests.user
        post = PostsURLsTests.post
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{group.slug}/': 'posts/group_list.html',
            f'/profile/{user.username}/': 'posts/profile.html',
            f'/posts/{post.pk}/': 'posts/post_detail.html',
            f'/posts/{post.pk}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.auth_client.get(address, follow=True)
                self.assertTemplateUsed(response, template)
