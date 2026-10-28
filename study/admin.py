from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin as BaseUserAdmin,
)

from .models import (
    CalendarConnection,
    FolderReference,
    ResearchDeadline,
    ResearchFolder,
    ResearchImage,
    ResearchNote,
    SavedReference,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)

    list_display = (
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "email",
        "full_name",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal information",
            {
                "fields": (
                    "full_name",
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "StudySource access",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "role",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


@admin.register(ResearchFolder)
class ResearchFolderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "description",
        "owner__email",
        "owner__full_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "owner",
    )


@admin.register(SavedReference)
class SavedReferenceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "provider",
        "reference_type",
        "publication_year",
        "created_at",
    )

    list_filter = (
        "provider",
        "reference_type",
        "publication_year",
        "created_at",
    )

    search_fields = (
        "title",
        "doi",
        "external_id",
        "source_name",
        "owner__email",
        "owner__full_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "owner",
    )

    filter_horizontal = ()


@admin.register(FolderReference)
class FolderReferenceAdmin(admin.ModelAdmin):
    list_display = (
        "saved_reference",
        "folder",
        "folder_owner",
        "date_added",
    )

    list_filter = (
        "date_added",
    )

    search_fields = (
        "saved_reference__title",
        "saved_reference__doi",
        "folder__name",
        "folder__owner__email",
    )

    readonly_fields = (
        "date_added",
    )

    autocomplete_fields = (
        "folder",
        "saved_reference",
    )

    @admin.display(
        description="Owner",
        ordering="folder__owner__email",
    )
    def folder_owner(self, obj):
        return obj.folder.owner.email


@admin.register(ResearchNote)
class ResearchNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "folder", "updated_at")
    search_fields = ("title", "content", "owner__email", "folder__name")
    list_filter = ("created_at", "updated_at")
    autocomplete_fields = ("owner", "folder", "saved_reference")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ResearchDeadline)
class ResearchDeadlineAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "folder", "due_date", "completed")
    search_fields = ("title", "description", "owner__email", "folder__name")
    list_filter = ("completed", "due_date")
    autocomplete_fields = ("owner", "folder")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ResearchImage)
class ResearchImageAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "folder", "created_at")
    search_fields = ("title", "public_id", "owner__email", "folder__name")
    autocomplete_fields = ("owner", "folder")
    readonly_fields = ("image_url", "public_id", "created_at")


@admin.register(CalendarConnection)
class CalendarConnectionAdmin(admin.ModelAdmin):
    list_display = ("owner", "token_expires_at", "updated_at")
    search_fields = ("owner__email", "owner__full_name")
    readonly_fields = (
        "access_token",
        "refresh_token",
        "token_expires_at",
        "created_at",
        "updated_at",
    )
