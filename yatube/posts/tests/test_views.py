import shutil
import tempfile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from posts.models import Group, Post, User, Follow
from django.core.cache import cache
from http import HTTPStatus
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


TESTPOST = 'Тестовый пост тестового пользователя'
ZERO = 0

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        image = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="test_image.jpg",
            content=image,
            content_type="image/jpg"
        )
        post = []
        for i in range(12):
            post.append(Post(
                author=cls.user,
                group=cls.group2,
                text='Тестовый пост тестового пользователя',
            )
            ),

        Post.objects.bulk_create(post)
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text=TESTPOST,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostsViewsTests.user)
        self.guest_client = Client()
        cache.clear()

    def test_posts_urls_show_correct_context(self):
        """Проверка URL-адресов на правильное использование шаблонов"""
        group = PostsViewsTests.group
        user = PostsViewsTests.user
        post = PostsViewsTests.post
        urls_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post.pk}
            ): 'posts/post_create.html',
        }
        for url, template in urls_templates_names.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)
        cache.clear()

    def test_index_page_show_correct_context(self):
        """Проверка шаблона главной страницы"""
        response = self.auth_client.get(reverse('posts:index'))
        context_post = response.context['page_obj'][ZERO]
        post_author = context_post.author.username
        post_group = context_post.group.title
        post_text = context_post.text
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(post_group, 'Тестовая группа 2')
        self.assertEqual(
            post_text,
            TESTPOST
        )

    def test_group_posts_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        group = PostsViewsTests.group
        response = self.auth_client.get(
            reverse('posts:group_list', kwargs={'slug': group.slug})
        )
        context_post = response.context['page_obj'][ZERO]
        post_author = context_post.author.username
        post_group = context_post.group.title
        post_text = context_post.text
        context_group = response.context['group'].title
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(context_group, 'Тестовая группа')
        self.assertEqual(
            post_text,
            TESTPOST
        )

    def test_profile_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        user = PostsViewsTests.user
        response = self.auth_client.get(
            reverse('posts:profile', kwargs={'username': user.username})
        )
        context_post = response.context['page_obj'][ZERO]
        post_author = context_post.author.username
        post_group = context_post.group.title
        post_text = context_post.text
        context_author = response.context['author'].username
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(context_author, 'test_user')
        self.assertEqual(post_group, 'Тестовая группа 2')
        self.assertEqual(
            post_text,
            TESTPOST
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон редактирования поста create_post сформирован
        с правильным контекстом. """
        post = PostsViewsTests.post
        response = self.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.pk})
        )
        context_post = response.context['post']
        post_author = context_post.author.username
        post_group = context_post.group.title
        post_text = context_post.text
        self.assertEqual(post_author, 'test_user')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(
            post_text,
            TESTPOST
        )

    def test_post_create_show_correct_context(self):
        """Шаблон создания поста create_post сформирован
        с правильным контекстом. """
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.auth_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_pages_correct_paginator_work(self):
        """Проверка корректной работы paginator"""
        group = PostsViewsTests.group2
        user = PostsViewsTests.user
        VERY_MAGIC_NUMBER = 10
        urls_page2posts_names = {
            reverse('posts:index'): 3,
            reverse('posts:group_list', kwargs={'slug': group.slug}): 2,
            reverse('posts:profile', kwargs={'username': user.username}): 3,
        }
        for page, page_2_posts in urls_page2posts_names.items():
            with self.subTest(page=page):
                response_page_1 = self.auth_client.get(page)
                response_page_2 = self.auth_client.get(page + '?page=2')
                self.assertEqual(
                    len(response_page_1.context['page_obj']),
                    VERY_MAGIC_NUMBER
                )
                self.assertEqual(
                    len(response_page_2.context['page_obj']),
                    page_2_posts
                )

    def test_post_correct_exist(self):
        """Созданный пост отобразился на главной, на странице группы,
        в профиле пользователя."""
        group = PostsViewsTests.group
        user = PostsViewsTests.user
        post = PostsViewsTests.post
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': group.slug}),
            reverse('posts:profile', kwargs={'username': user.username}),
        ]
        for page in pages_names:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                context_post = response.context['page_obj'][ZERO]
                self.assertEqual(context_post, post)

    def test_post_correct_not_exist(self):
        """Созданный пост не попал в группу, для которой был предназначен"""
        group2 = PostsViewsTests.group2
        post = PostsViewsTests.post
        page = reverse('posts:group_list', kwargs={'slug': group2.slug})
        response = self.auth_client.get(page)
        context_post = response.context['page_obj'][ZERO]
        self.assertNotEqual(context_post, post)

    def test_post_with_image_added_in_context(self):
        """Проверка работы image в контексте"""
        addresses = {
            reverse("posts:index"): self.post.image,
            reverse("posts:profile",
                    kwargs={"username": self.user.username}): self.post.image,
            reverse("posts:group_list",
                    kwargs={"slug": self.group.slug}): self.post.image,
        }
        for value, expected in addresses.items():
            with self.subTest(value=value):
                response = self.auth_client.get(value)
                first_object = response.context["page_obj"][0]
                self.assertEqual(first_object.image, expected)

    def test_post_with_image_added_in_context_post_detail(self):
        """Проверка работы image в шаблоне"""
        response = self.auth_client.get(
            reverse("posts:post_detail",
                    kwargs={"post_id": self.post.id}))
        post = response.context["post"]
        self.assertEqual(post.image, self.post.image)

    def test_postform_create_with_image_added_form_in_database(self):
        response = self.auth_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
            "image": forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.author = User.objects.create_user(username="author")

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        cache.clear()

    def test_autorized_user_can_follow(self):
        follow_count = Follow.objects.count()
        response = (self.auth_client.get(
            reverse("posts:profile_follow",
                    kwargs={"username": self.author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.author
        ).exists())

    def test_autorized_user_can_unfollow(self):
        author = self.user
        Follow.objects.create(user=self.user, author=author)
        follow_count = Follow.objects.count()
        response = (self.auth_client.
                    get(reverse("posts:profile_unfollow",
                        kwargs={"username": author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=author
        ).exists())

    def test_new_post_appear_on_follower_page(self):
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.author
        )
        Follow.objects.create(author=self.author, user=self.user)
        response = self.auth_client.get(reverse("posts:follow_index"))
        self.assertEqual(response.context["page_obj"][0], self.post)

    def test_new_post_does_not_appear_on_follower_page(self):
        self.post = Post.objects.create(
            text="Тестовый текст", author=self.author
        )
        Follow.objects.create(author=self.author, user=self.user)
        self.second_user = User.objects.create_user(
            username="username",
        )
        self.auth_client.force_login(self.second_user)
        response = self.auth_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
