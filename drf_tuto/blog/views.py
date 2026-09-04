from rest_framework import generics

from .filters import UserPostFilter
from .models import Blog, Comment, UserPost
from .pagination import CustomPagination
from .serializer import BlogSerializer, CommentSerializer, UserPostSerializer


# Create your views here.
class Bloglist(generics.ListAPIView, generics.CreateAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer


class Bloginfo(generics.RetrieveUpdateDestroyAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    lookup_field = "pk"


class UserPostgenerics(generics.ListCreateAPIView):
    queryset = UserPost.objects.all()
    serializer_class = UserPostSerializer
    pagination_class = CustomPagination
    filterset_class = UserPostFilter


class UserPostviews(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserPost.objects.all()
    serializer_class = UserPostSerializer
    lookup_field = "pk"


class Commentgenerics(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    lookup_field = "pk"
