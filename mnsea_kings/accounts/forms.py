from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Full name"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={"class": "form-control", "placeholder": "Email address"}))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "10-digit mobile number"}))

    class Meta:
        model = User
        fields = ["first_name", "email", "username", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Choose a username"})
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirm password"})

    def save(self, commit=True):
        from .models import Profile
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        if commit:
            user.save()
            Profile.objects.update_or_create(user=user, defaults={"phone": self.cleaned_data["phone"]})
        return user
