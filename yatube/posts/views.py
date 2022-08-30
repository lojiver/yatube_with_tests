from django.shortcuts import render, get_object_or_404, redirect
from .models import Follow, Post, Group, User
from .forms import CommentForm, PostForm
from django.contrib.auth.decorators import login_required
from .utils import paginate_page


def is_author(func):
    def check_user(request, *args, **kwargs):
        if Post.author == request.user:
            return func(request, *args, **kwargs)
        return redirect('/auth/login')
    return check_user


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginate_page(request, posts)
    context: dict = {
        'page_obj': page_obj
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')
    page_obj = paginate_page(request, posts)
    context: dict = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    user_posts = user.posts.select_related('author', 'group')
    page_obj = paginate_page(request, user_posts)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=user.id
    ).exists()
    context: dict = {
        'author': user,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    context: dict = {
        'post': post,
        'form': CommentForm(request.POST or None),
        'page_obj': paginate_page(
            request, post.comments.select_related('author', 'post')
        ),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)
    return render(request, template, {'form': form, 'is_edit': False})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    is_edit = True
    post = get_object_or_404(Post,
                             pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context={
        'form': form,
        'post': post,
        'is_edit': is_edit
    })


@login_required
def add_comment(request, post_id):
    template = 'posts/add_comment.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context={'form': form, 'post': post})


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    user = request.user
    followed_posts = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = paginate_page(request, followed_posts)
    context = {
        'page_obj': page_obj,
        'user': user,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
