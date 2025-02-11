from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def get_pagination(queryset, request):
    # Показывать по 10 записей на странице.
    paginator = Paginator(queryset, settings.POSTS_ORDERED_BY)
    # Из URL извлекаем номер запрошенной страницы - это значение параметра page
    page_number = request.GET.get('page')
    # Получаем набор записей для страницы с запрошенным номером
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    post_list = Post.objects.select_related('group', 'author').all()
    context = get_pagination(post_list, request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'post_list': post_list,
    }
    # Дополнить словарь контекст результатом get_pagination()
    context.update(get_pagination(post_list, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    # Здесь код запроса к модели и создание словаря контекста
    author = get_object_or_404(User, username=username)
    # Все посты за авторством user
    post_list = author.posts.all()
    counter = post_list.count()
    following = author.following.all()
    follower = author.follower.all()
    count_follower = follower.count()
    count_following = following.count()
    
    context = {
        'author': author,
        'couter': counter,
        'count_follower': count_follower,
        'count_following': count_following,
    }
    context.update(get_pagination(post_list, request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    username = post.author
    posts_all = username.posts.all().count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'posts_all': posts_all,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    context = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list_follow = Post.objects.filter(
        author__following__user=request.user)
    # paginator = Paginator(post_list_follow, settings.POSTS_ORDERED_BY)
    # page_number = request.GET.get('page')
    # page = paginator.get_page(page_number)
    # return render(request, 'follow.html',
    #               {'page': page, 'paginator': paginator})
    context = get_pagination(post_list_follow, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow = get_object_or_404(User, username=username)
    already_following = Follow.objects.filter(user=request.user, author=follow).exists()

    if request.user.username == username:
        return redirect('posts:profile', username=username)

    if not already_following:
        Follow.objects.get_or_create(user=request.user, author=follow)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(Follow, author=following, user=request.user)
    follower.delete()
    return redirect('posts:profile', username=username)    