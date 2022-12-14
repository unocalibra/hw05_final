from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()

LAST_POSTS = 10


def index(request):
    """
    Вернет главную страницу с десятью последними постами.
    """
    post = Post.objects.select_related('group')
    paginator = Paginator(post, LAST_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """
    Вернет страницу группы с десятью последними постами.
    """
    group = get_object_or_404(Group, slug=slug)
    paginator = Paginator(group.posts.all(), LAST_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def post_create(request):
    """
    Вернет форму создания поста.
    """
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if not form.is_valid():
            return render(request, 'posts/create_post.html', {'form': form})
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Позволяет редактировать пост."""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'post': post, 'is_edit': True}
    return render(request, 'posts/create_post.html', context)


def profile(request, username):
    """
    Вернет страницу автора поста.
    """
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, LAST_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = request.user.is_authenticated
    if following:
        following = author.following.filter(user=request.user).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """
    Вернет страницу поста автора.
    """
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    author = post.author
    context = {
        'author': author,
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    """
    Добавит комментарий к посту.
    """
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """
    Вернет страницу постов по подписке.
    """
    posts = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(posts, LAST_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """
    Подписка на автора.
    """
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    """
    Отписка от автора.
    """
    user_follower = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    )
    user_follower.delete()
    return redirect('posts:profile', username)
