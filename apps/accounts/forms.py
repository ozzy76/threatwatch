import datetime
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.accounts.models import User, ROLE_ANALYST, ROLE_ADMIN


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )


class UserCreateForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="First Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Last Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    role = forms.ChoiceField(
        choices=[(ROLE_ANALYST, "Analyst"), (ROLE_ADMIN, "Admin")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    password = forms.CharField(
        min_length=12,
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects(username=username).first():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects(email=email).first():
            raise forms.ValidationError("A user with that email address already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "Passwords do not match.")
        if pw:
            try:
                validate_password(pw)
            except DjangoValidationError as exc:
                self.add_error("password", exc)
        return cleaned
