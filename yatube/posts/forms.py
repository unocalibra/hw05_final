from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """
    Класс формы нового поста.
    """
    class Meta:
        model = Post
        labels = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        help_texts = {'group': 'Выберите группу',
                      'text': 'Введите сообщение'}
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """
    Класс формы нового коммента.
    """
    class Meta:
        model = Comment
        labels = {
            'text': 'Текст поста',
        }
        help_texts = {'text': 'Введите комментарий'}
        fields = ('text',)
