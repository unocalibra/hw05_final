from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='admin1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_2,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.get(username='admin1')
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_unauthorized(self):
        """Страницы / доступны любому пользователю."""
        url_names = (
            '/',
            '/group/test_slug/',
            '/profile/auth/',
            f'/posts/{self.post.id}/',
        )
        for url in url_names:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_for_author(self):
        """Страница edit доступна автору."""
        response = self.post_author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_redirect_anonymous(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/')
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_for_post_author_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.post_author.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_page_404(self):
        """Проверка несуществующей страницы.
        """
        response = self.guest_client.get('/python/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
