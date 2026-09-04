from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Author, AuthorProfile, Book, Genre
from .serializer import (
    AuthorProfileSerializer,
    AuthorSerializer,
    BookSerializer,
    GenreSerializer,
)


# Create your views here
@api_view(["GET", "POST"])
def authorslist(request):
    if request.method == "GET":
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        serializer = AuthorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def authordetail(request, pk):
    try:
        author = Author.objects.get(pk=pk)
    except Author.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = AuthorSerializer(author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "PUT":
        serializer = AuthorSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == "DELETE":
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# APIVIEW
class AuthorInfo(APIView):
    def get_author(self, pk):
        try:
            return AuthorProfile.objects.get(pk=pk)
        except AuthorProfile.DoesNotExist:
            return None

    def get(self, request, pk):
        author = self.get_author(pk)
        if author is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AuthorProfileSerializer(author)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        author = self.get_author(pk)
        if author is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AuthorProfileSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        author = self.get_author(pk)
        if author is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = AuthorProfileSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        author = self.get_author(pk)
        if author is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# mixins
# first of all we inherit listmodel createmodel and generic api
# also we inherit all the feature from mixins
# list retrieve create update destroy
class Bookapi(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView,
):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get(self, request):
        return self.list(request)

    def post(self, request):
        return self.create(request)


class Bookinfoapi(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get(self, request, pk):
        return self.retrieve(request, pk)

    def put(self, request, pk):
        return self.update(request, pk)

    def delete(self, request, pk):
        return self.destroy(request, pk)


# generics
# listapiview, create, retrieve, update, destroy
# listcreateapiview, retrieveupdate, retrieve updatedestory
# listcreateapi view is for non pk other 3 for pk
class Genreapi(generics.ListAPIView, generics.CreateAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class Genreinfoapi(generics.RetrieveUpdateDestroyAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = "pk"


# viewsets
# make a router by assigning defaultrouter to a router object
# pass args ike path to router using router.register
# include router in path in urls


class Authorviewset(viewsets.ViewSet):
    def list(self, request):
        queryset = Author.objects.all()
        serializer = AuthorSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = AuthorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorSerializer(author)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        author.delete()
        return Response(status.HTTP_204_NO_CONTENT)


# modelviewset
# register in router also
class Authormodelviewset(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


# done
# serializer
# api_view decorator
# Apiview
# mixins
# genericviews
# viewset
# modelviewset
# router
# nestedserialization done in blogs app
# pagination set the fields or vars in settings.py for pagination
# global pagination
# custompagination using pagination.py
# filtering first declare app in intsalled apps and also install filter (django-filter)
# custom filters # why do i even need this.
