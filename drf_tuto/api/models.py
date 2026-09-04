from django.db import models


# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=50)
    age = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class AuthorProfile(models.Model):
    author = models.OneToOneField(Author, on_delete=models.CASCADE)
    bio = models.TextField()
    website = models.URLField()

    def __str__(self):
        return f"profile of : {self.author.name}"


class Genre(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    genre = models.ManyToManyField(Genre)
    price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.title} genre {self.genre.name} written by {self.author.name}"
