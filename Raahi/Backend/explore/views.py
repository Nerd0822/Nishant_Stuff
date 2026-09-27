from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Like, Post


@login_required
def explore_view(request):
    """Show the explore feed with all posts."""
    posts = Post.objects.select_related('user').prefetch_related('comments', 'likes')
    return render(request, 'explore/feed.html', {'posts': posts})


@login_required
def post_detail(request, pk):
    """Show a single post with comments. Open Graph tags make link shares rich."""
    post = get_object_or_404(Post.objects.select_related('user'), pk=pk)
    comment_form = CommentForm()
    return render(request, 'explore/detail.html', {'post': post, 'comment_form': comment_form})


@login_required
def create_post(request):
    """Create a new post."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Your post has been shared!')
            return redirect('explore')
    else:
        form = PostForm()
    return render(request, 'explore/create_post.html', {'form': form})


@login_required
@require_POST
def toggle_like(request, post_id):
    """Like or unlike a post."""
    post = get_object_or_404(Post, pk=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
    return redirect('explore')


@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
    return redirect('post_detail', pk=post.pk)
