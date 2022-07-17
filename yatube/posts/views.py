from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import page_paginator


def index(request):
    posts = Post.objects.select_related('group', 'author')
    context = {
        'page_obj': page_paginator(posts, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    context = {
        'group': group,
        'page_obj': page_paginator(posts, request)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group', 'author')
    count = posts.count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    profile = author
    context = {
        'page_obj': page_paginator(posts, request),
        'following': following,
        'count': count,
        'author': author,
        'profile': profile,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, {"form": form, "post_edit_flag": True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'includes/comments.html', {'form': form,
                  'post': post})


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    context = {'page': page_paginator(posts, request)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    following = Follow.objects.filter(user=user, author=author)
    if user != author and not following.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=author)
    if following.exists():
        following.delete()
    return redirect('posts:profile', username=author)


def server_error(request):
    return render(request, "core/500.html", status=500)
