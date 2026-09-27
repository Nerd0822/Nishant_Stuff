from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile


class ProfileRegistrationForm(UserCreationForm):
    bio = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Tell us about your travel style..."}
        ),
        required=False,
    )
    preferred_travel_style = forms.ChoiceField(
        choices=Profile.TRAVEL_STYLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    class Meta(UserCreationForm.Meta):
        model = Profile
        fields = (
            "username",
            "email",
            "password1",
            "password2",
            "bio",
            "preferred_travel_style",
        )

class ProfileLoginForm(AuthenticationForm):
    pass
