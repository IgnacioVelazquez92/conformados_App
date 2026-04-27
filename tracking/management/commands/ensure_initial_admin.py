import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un superusuario inicial si no existe."

    def handle(self, *args, **options):
        username = os.getenv("INITIAL_ADMIN_USERNAME", "ivelazquez")
        password = os.getenv("INITIAL_ADMIN_PASSWORD", "12345678**")
        email = os.getenv("INITIAL_ADMIN_EMAIL", "")

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f"Admin inicial '{username}' ya existe."))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Admin inicial '{username}' creado."))
