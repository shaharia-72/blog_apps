"""
apps/users/admin.py
====================
Register User in Django admin panel.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Extends the default UserAdmin to show our custom fields.
    """

    list_display = ["username", "email", "full_name", "is_staff", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name"]

    # Add our custom fields into the existing fieldsets
    fieldsets = UserAdmin.fieldsets + (
        (
            "Profile",
            {
                "fields": [
                    "bio",
                    "avatar",
                    "website",
                    "twitter_username",
                    "linkedin_username",
                    "github_username",
                    "skills",
                ]
            },
        ),
    )
