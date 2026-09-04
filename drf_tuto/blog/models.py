from datetime import datetime

from django.db import models


# Create your models here.
class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_on = models.DateField(auto_now_add=datetime.utcnow)

    def __str__(self):
        return f"{self.title} posted on {self.posted_on}"


class UserPost(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    userpost = models.ForeignKey(
        UserPost, on_delete=models.CASCADE, related_name="comments"
    )
    reply = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )
    comment = models.TextField()

    def __str__(self):
        return self.comment
