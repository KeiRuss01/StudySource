from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    """Create users who log in using an email address."""

    use_in_migrations = True

    def create_user(
        self,
        email,
        password=None,
        **extra_fields,
    ):
        if not email:
            raise ValueError(
                "An email address is required."
            )

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault(
            "role",
            User.Role.ADMIN,
        )

        extra_fields.setdefault(
            "is_staff",
            True,
        )

        extra_fields.setdefault(
            "is_superuser",
            True,
        )

        extra_fields.setdefault(
            "is_active",
            True,
        )

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "A superuser must have is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "A superuser must have is_superuser=True."
            )

        return self.create_user(
            email,
            password,
            **extra_fields,
        )


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        ADMIN = "admin", "Admin"

    username = None

    email = models.EmailField(
        unique=True,
    )

    full_name = models.CharField(
        max_length=150,
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class ResearchFolder(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="research_folders",
    )

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-updated_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_folder_name_per_owner",
            )
        ]

    def __str__(self):
        return self.name


class SavedReference(models.Model):
    class Provider(models.TextChoices):
        OPENALEX = "openalex", "OpenAlex"
        CROSSREF = "crossref", "Crossref"
        GOOGLE_BOOKS = "google_books", "Google Books"
        MANUAL = "manual", "Manual Entry"

    class ReferenceType(models.TextChoices):
        PAPER = "paper", "Paper"
        BOOK = "book", "Book"
        OTHER = "other", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_references",
    )

    provider = models.CharField(
        max_length=30,
        choices=Provider.choices,
    )

    external_id = models.CharField(
        max_length=255,
        blank=True,
    )

    reference_type = models.CharField(
        max_length=20,
        choices=ReferenceType.choices,
        default=ReferenceType.PAPER,
    )

    title = models.CharField(
        max_length=500,
    )

    authors = models.JSONField(
        default=list,
        blank=True,
    )

    publication_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    doi = models.CharField(
        max_length=255,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    source_name = models.CharField(
        max_length=255,
        blank=True,
    )

    source_url = models.URLField(
        max_length=1000,
        blank=True,
    )

    access_url = models.URLField(
        max_length=1000,
        blank=True,
    )

    folders = models.ManyToManyField(
        ResearchFolder,
        through="FolderReference",
        related_name="saved_references",
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "owner",
                    "provider",
                    "external_id",
                ],
                condition=~models.Q(external_id=""),
                name="unique_provider_reference_per_owner",
            ),
            models.UniqueConstraint(
                Lower("doi"),
                "owner",
                condition=~models.Q(doi=""),
                name="unique_reference_doi_per_owner",
            ),
        ]

    @property
    def authors_display(self):
        if not self.authors:
            return "Not available"

        return ", ".join(self.authors)

    def __str__(self):
        return self.title


class FolderReference(models.Model):
    folder = models.ForeignKey(
        ResearchFolder,
        on_delete=models.CASCADE,
        related_name="folder_references",
    )

    saved_reference = models.ForeignKey(
        SavedReference,
        on_delete=models.CASCADE,
        related_name="folder_links",
    )

    date_added = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-date_added"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "folder",
                    "saved_reference",
                ],
                name="unique_reference_in_folder",
            )
        ]

    def __str__(self):
        return (
            f"{self.folder.name}: "
            f"{self.saved_reference.title}"
        )