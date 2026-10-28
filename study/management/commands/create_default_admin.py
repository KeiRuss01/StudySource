from django.core.management.base import BaseCommand

from study.models import User


class Command(BaseCommand):
    help = "Create the local StudySource administrator account."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@gmail.com")
        parser.add_argument("--password", default="admin123")
        parser.add_argument("--name", default="StudySource Administrator")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]
        full_name = options["name"].strip()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "role": User.Role.ADMIN,
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Admin account created: {email}"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "This is a local default password. Change it before deployment."
                )
            )
            return

        changed_fields = []
        required_values = {
            "role": User.Role.ADMIN,
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        }

        for field, value in required_values.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if not user.full_name:
            user.full_name = full_name
            changed_fields.append("full_name")

        if changed_fields:
            changed_fields.append("updated_at")
            user.save(update_fields=changed_fields)

        self.stdout.write(
            self.style.WARNING(
                f"{email} already exists. Its existing password was preserved."
            )
        )
