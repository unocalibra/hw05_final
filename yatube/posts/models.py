from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Модель группы."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=50)
    description = models.TextField()

    def __str__(self):
        """Вернет название группы."""
        return self.title


class Post(models.Model):
    """Модель поста."""
    class Meta:
        """
        Сортировка по убыванию
        по дате публикации.
        """
        ordering = ['-pub_date']

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True, null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        """Вернет текст поста."""
        return self.text[:settings.LAST_SYMBOLS]


class Comment(models.Model):
    """Модель комментария."""
    class Meta:
        """
        Сортировка по убыванию
        по дате публикации.
        """
        ordering = ['-created']

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name='Пост'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментания',
        help_text='Введите текст комментания'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )

    def __str__(self):
        """Вернет текст коммента."""
        return self.text[:settings.LAST_SYMBOLS]


class Follow(models.Model):
    """Модель подписчика."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    def __str__(self):
        """Вернет информацию о подписке."""
        return f'{self.user} подписался на {self.author}'
