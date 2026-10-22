from django.core.management.base import BaseCommand
from clinic.models import ChainBlock

class Command(BaseCommand):
    help = 'Ломает цепочку для тестов (меняет payload указанного блока)'

    def add_arguments(self, parser):
        parser.add_argument(
            'index', 
            type=int, 
            nargs='?', 
            default=None, 
            help='Индекс блока для подделки (по умолчанию последний)'
        )

    def handle(self, *args, **options):
        target_index = options['index']
        
        qs = ChainBlock.objects.filter(type="medical_record").order_by("index")

        if target_index is not None:
            target = qs.filter(index=target_index).first()
            if not target:
                self.stdout.write(self.style.ERROR(f"Блок с индексом #{target_index} не найден."))
                return
        else:
            target = qs.last()
            if not target:
                self.stdout.write(self.style.ERROR("Медицинских записей нет. Сначала добавьте хотя бы одну."))
                return

        old_diagnosis = target.payload.get("diagnosis")
        
        target.payload["diagnosis"] = "ПОДДЕЛКА"
        target.save()

        self.stdout.write(self.style.SUCCESS(f"Цель: блок #{target.index}"))
        self.stdout.write(self.style.WARNING(f"Данные успешно подделаны!"))
        self.stdout.write(f"   Было: '{old_diagnosis}'")
        self.stdout.write(f"   Стало: '{target.payload['diagnosis']}'")