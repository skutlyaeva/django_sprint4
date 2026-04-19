from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from blog.models import Post, Category, Comment
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, Http404

def index(request):
    template = 'blog/index.html'
    current_time = timezone.now()
    sorted_posts = Post.objects.select_related(
        'category', 'location', 'author', 
    ).annotate(
        comment_count=Count('comments')
    ).filter(
        Q(is_published=True)
        & Q(category__is_published=True)
        & Q(pub_date__lte=current_time)
    ).order_by('-pub_date')
    paginator = Paginator(sorted_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Лента записей'
    }
    return render(request, template, context)


def post_detail(request, pk):
    template = 'blog/detail.html'
    current_time = timezone.now()

    try:
        # Пытаемся найти опубликованный пост
        post = Post.objects.select_related(
            'category', 'location', 'author'
        ).get(
            id=pk,
            is_published=True,
            pub_date__lte=current_time,
            category__is_published=True
        )
    except Post.DoesNotExist:
        # Если пост не найден в опубликованных, проверяем является ли пользователь автором
        post = get_object_or_404(Post.objects.select_related(
            'category', 'location', 'author'
        ), id=pk)
        
        # Если пользователь не автор - 404
        if post.author != request.user:
            raise Http404("Пост не найден")
    
    form = CommentForm()
    comments = Comment.objects.select_related(
        'post', 'author'
    ).filter(post=post).order_by('pub_date')  # Обычно комментарии сортируются по created_at
    
    context = {
        'post': post,
        'title': post.title,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    current_time = timezone.now()

    category = get_object_or_404(
        Category.objects.filter(is_published=True),
        slug=category_slug
    )

    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).annotate(
        comment_count=Count('comments')
    ).filter(
        category=category,
        is_published=True,
        pub_date__lte=current_time,
    ).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'category': category,
        'title': f'Публикации в категории {category.title}'
    }
    template = 'blog/category.html'
    return render(request, template, context)

def profile(request, slug):
    user = get_object_or_404(User, username=slug)
    current_time = timezone.now()
    is_own_profile = request.user.is_authenticated and request.user == user
    if is_own_profile:
        sorted_posts = Post.objects.select_related(
            'category', 'location', 'author'
        ).annotate(
            comment_count=Count('comments')
        ).filter(
            author=user
        ).order_by('-pub_date')
    else:
        sorted_posts = Post.objects.select_related(
            'category', 'location', 'author'
        ).annotate(
            comment_count=Count('comments')
        ).filter(
            Q(is_published=True)
            & Q(author=user)
            & Q(pub_date__lte=current_time)
        ).order_by('-pub_date')
    paginator = Paginator(sorted_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    template = 'blog/profile.html'
    password_form = None
    if is_own_profile:
        password_form = PasswordChangeForm(request.user)
    context = {
        'profile': user,
        'page_obj': page_obj,
        'is_own_profile': is_own_profile,
        'form': password_form
    }
    return render(request, template, context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', slug=post.author)
    template = 'blog/create.html'
    context = {'form': form}
    return render(request, template, context)


def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    if post.author != request.user:
        return redirect('blog:post_detail', pk=pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    template = 'blog/create.html'
    context = {'form': form}
    return render(request, template, context)

@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Проверка для GET запроса (показ страницы подтверждения)
    if request.method == 'GET':
        # Показываем страницу подтверждения удаления
        return render(request, 'blog/post_confirm_delete.html', {'post': post})
    
    # Обработка POST запроса (фактическое удаление)
    if request.method == 'POST':
        # Проверка авторства
        if post.author != request.user:
            return HttpResponseForbidden("Вы не можете удалить этот пост")
        
        post.delete()
        return redirect('blog:index')


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', pk=pk)

def edit_comment(request, pk, id):
    post = get_object_or_404(Post, pk=pk)
    instance = get_object_or_404(Comment, pk=id, post=post)
    if instance.author != request.user:
        return HttpResponseForbidden("Вы не можете редактировать этот комментарий")
    form = CommentForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
    template = 'blog/comment.html'
    comment = instance
    context = {
        'form': form,
        'post': post,
        'comment': comment
    }
    return render(request, template, context)

def delete_comment(request, pk, id):
    post = get_object_or_404(Post, pk=pk)
    instance = get_object_or_404(Comment, pk=id, post=post)
    form = CommentForm(instance=instance)
    comment = instance
    if comment.author != request.user:
        return HttpResponseForbidden("Вы не можете удалить этот комментарий")
    context = {
        #'form': form,
        'post': post,
        'comment': comment
    }
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', pk=pk)
    template = 'blog/comment.html'
    return render(request, template, context)


