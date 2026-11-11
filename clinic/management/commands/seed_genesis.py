from django.core.management.base import BaseCommand
from clinic import services


class Command(BaseCommand):
    help = "Создать genesis-блок, если цепочка пуста"

    def handle(self, *args, **options):
        services._ensure_genesis()
        self.stdout.write(f"height: {services.local_height()}")