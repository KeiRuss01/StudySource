from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from .models import ResearchFolder, User


class SignUpForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=150,
        label="Full name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter your full name",
                "autocomplete": "name",
            }
        ),
    )

    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Enter your email address",
                "autocomplete": "email",
            }
        ),
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Create a password",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter your password again",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User

        fields = (
            "full_name",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "An account with this email address "
                "already exists."
            )

        return email

    def save(self, commit=True):
        user = super().save(
            commit=False
        )

        user.email = self.cleaned_data[
            "email"
        ]

        user.full_name = (
            self.cleaned_data["full_name"]
            .strip()
        )

        user.role = User.Role.STUDENT

        if commit:
            user.save()

        return user


class EmailAuthenticationForm(
    AuthenticationForm
):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": (
                    "Enter your email address"
                ),
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter your password",
                "autocomplete": (
                    "current-password"
                ),
            }
        ),
    )


class ResearchFolderForm(forms.ModelForm):
    name = forms.CharField(
        max_length=150,
        label="Folder name",
        widget=forms.TextInput(
            attrs={
                "placeholder": (
                    "Example: Dengue Research"
                ),
                "autocomplete": "off",
            }
        ),
    )

    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(
            attrs={
                "placeholder": (
                    "Briefly describe the topic "
                    "or purpose of this research "
                    "folder."
                ),
                "rows": 5,
            }
        ),
    )

    class Meta:
        model = ResearchFolder

        fields = (
            "name",
            "description",
        )

    def __init__(
        self,
        *args,
        owner=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.owner = owner

    def clean_name(self):
        name = (
            self.cleaned_data["name"]
            .strip()
        )

        if not name:
            raise forms.ValidationError(
                "Please enter a folder name."
            )

        if self.owner:
            matching_folders = (
                ResearchFolder.objects.filter(
                    owner=self.owner,
                    name__iexact=name,
                )
            )

            if self.instance.pk:
                matching_folders = (
                    matching_folders.exclude(
                        pk=self.instance.pk
                    )
                )

            if matching_folders.exists():
                raise forms.ValidationError(
                    "You already have a folder "
                    "with this name."
                )

        return name


class SaveOpenAlexReferenceForm(forms.Form):
    external_id = forms.RegexField(
        regex=r"^W\d+$",
        widget=forms.HiddenInput(),
        error_messages={
            "invalid": (
                "The selected paper has an "
                "invalid OpenAlex ID."
            )
        },
    )

    folder = forms.ModelChoiceField(
        queryset=ResearchFolder.objects.none(),
        required=False,
        empty_label="Save without a folder",
        label="Research folder",
        widget=forms.Select(
            attrs={
                "class": "save-reference-select",
            }
        ),
    )

    def __init__(
        self,
        *args,
        owner=None,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        if owner:
            self.fields["folder"].queryset = (
                ResearchFolder.objects.filter(
                    owner=owner
                )
            )