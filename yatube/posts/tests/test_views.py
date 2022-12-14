import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

        cls.user_2 = User.objects.create_user(username='auth1')
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        cls.post_2 = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 2',
            group=cls.group_2,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = User.objects.get(username='auth')
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_pages_for_auth_cl_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_lists', kwargs={'slug': 'test_slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'auth'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_for_post_author_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_page_for_not_post_author_dont_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertTrue(response, 'posts/create_post.html')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))

        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post_2)

    def test_group_lists_pages_show_correct_context(self):
        """Шаблон group_lists сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_lists',
            kwargs={'slug': 'test_slug'})
        )

        first_object = response.context['group']
        self.assertEqual(first_object, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        first_object = response.context['author']
        self.assertEqual(first_object, self.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context['post']
        self.assertEqual(first_object, self.post)

    def test_post_create_show_correct_context(self):
        """Проверка формы post_create."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field = response.context['form']
        self.assertIsInstance(form_field, PostForm)

    def test_post_edit_show_correct_context(self):
        """Проверка формы post_edit."""
        response = self.post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_field = response.context['form']
        self.assertIsInstance(form_field, PostForm)

    def test_post_added_correctly(self):
        """Пост при создании добавлен корректно"""
        post = Post.objects.create(
            text='проверка как добавился',
            author=self.user,
            group=self.group)
        response_index = self.authorized_client.get(
            reverse('posts:index'))
        response_group = self.authorized_client.get(
            reverse('posts:group_lists', kwargs={'slug': 'test_slug'}))
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'auth'}))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']
        self.assertIn(post, index, 'поста нет на главной')
        self.assertIn(post, group, 'поста нет в группе')
        self.assertIn(post, profile, 'поста нет в профиле')

    def test_comment_added_correctly(self):
        """Комментарий при создании добавлен корректно"""
        comment = Comment.objects.create(
            text='Текст комментария',
            post=self.post,
            author=self.user,
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post_detail = response.context['comments']
        self.assertIn(comment, post_detail, 'комментария нет')

    def test_post_in_another_group(self):
        """Пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_lists', kwargs={'slug': 'test_slug2'}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_cache(self):
        """Тестирование Кэша."""
        post = Post.objects.create(
            text='Кээээш',
            author=self.user,
            group=self.group
        )
        content_add = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_afther = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_add, content_afther)
        cache.clear()
        content_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_add, content_clear)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            ))

        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_1_page_contain_ten_posts(self):
        """Десять постов на главной."""
        list = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_lists',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
        }
        for urls in list.keys():
            response = self.guest_client.get(urls)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_2_page_contain_ten_posts(self):
        """Три поста на второй."""
        list = {
            reverse('posts:index') + "?page=2": 'posts/index.html',
            reverse('posts:group_lists',
                    kwargs={'slug': 'test_slug'}) + "?page=2":
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}) + "?page=2":
            'posts/profile.html',
        }
        for urls in list.keys():
            response = self.guest_client.get(urls)
            self.assertEqual(len(response.context['page_obj']), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='author',
        )
        cls.follower = User.objects.create_user(
            username='follower',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author
        )

    def setUp(self):
        cache.clear()
        self.author_client = Client()
        self.author_client.force_login(self.follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.author)

    def test_follow_user(self):
        """Проверка подписки на автора."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.follower.id)
        self.assertEqual(follow.user_id, self.author.id)

    def test_unfollow_user(self):
        """Проверка отписки от автора."""
        Follow.objects.create(
            user=self.author,
            author=self.follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_exist(self):
        """Проверка наличие записи."""
        post = Post.objects.create(
            author=self.author,
            text='Тестовый текст'
        )
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_follow_not_exist(self):
        """Проверка отсутствия записи."""
        post = Post.objects.create(
            author=self.author,
            text='Тестовый текст'
        )
        response = self.author_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)
