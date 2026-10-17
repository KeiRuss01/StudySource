from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin as BaseUserAdmin,
)

from .models import (
    FolderReference,
    ResearchFolder,
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