from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User, Comment
from django.core.cache import cache
from http import HTTPStatus


class PostsFormsTests(TestCase):
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

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostsFormsTests.user)
        cache.clear()

    def test_posts_create_post(self):
        """Форма создает запись в Posts."""
        TEST_POST = 'Тестовый пост'
        posts_count = Post.objects.count()
        form_data = {
            'text': TEST_POST,
            'group': self.group.pk,
        }
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=TEST_POST,
                group=self.group,
                author=self.user,
            ).exists()
        )

    def test_posts_edit_post(self):
        """Форма изменяет запись в Posts."""
        TEST_POST_EDIT = 'Тестовый пост изменен'
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='Тестовая группа',
            slug='group_list',
            description='Новое тестовое описание',
        )
        form_data = {
            'text': TEST_POST_EDIT,
            'group': new_group.pk,
        }
        post = Post.objects.get(id=self.group.pk)
        self.auth_client.get(f'/posts/{post.pk}/edit/')
        form_data = {
            'text': 'Тестовый пост изменен',
            'group': new_group.pk,
        }
        self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('id')
        response = Post.objects.get(pk=self.post.pk)
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.text, TEST_POST_EDIT)
        self.assertEqual(response.author, self.user)
        old_group_response = self.auth_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count,
            0,
            'В старой группе есть посты',
        )

    def test_add_comments_by_authorized_client(self):
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария',
        }
        response = self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        last_comment = response.context['post']
        comment = last_comment.comments.last()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
