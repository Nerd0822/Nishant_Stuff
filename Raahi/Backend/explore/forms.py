from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'content', 'image', 'location_name')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': "Give your story a title"}),
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
            'location_name': forms.TextInput(attrs={'placeholder': 'Location name (optional)'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': 'Write a comment...'}),
        }
