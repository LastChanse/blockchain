from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from clinic import services


class Command(BaseCommand):
    help = "Создать тестовый medical_record от имени врача"

    def add_arguments(self, parser):
        parser.add_argument("--doctor", required=True)
        parser.add_argument("--patient", required=True)
        parser.add_argument("--diagnosis", default="test diagnosis")

    def handle(self, *args, **options):
        try:
            doctor = User.objects.get(username=options["doctor"])
            patient = User.objects.get(username=options["patient"])
        except User.DoesNotExist as e:
            raise CommandError(str(e))

        services.add_block(patient, "medical_record", {
            "patient_name": patient.username,
            "diagnosis": options["diagnosis"],
        })
        self.stdout.write(f"height: {services.local_height()}")