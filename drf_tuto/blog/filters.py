import django_filters

from .models import UserPost


class UserPostFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="iexact")

    class Meta:
        model = UserPost
        fields = "__all__"
