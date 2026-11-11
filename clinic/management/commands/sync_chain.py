from django.conf import settings
from django.core.management.base import BaseCommand
import requests

from clinic import services


class Command(BaseCommand):
    help = "Синхронизировать цепочку с пирами"

    def handle(self, *args, **options):
        token = settings.INTERNAL_SYNC_TOKEN
        headers = {"X-Internal-Token": token}
        local_height = services.local_height()
        self.stdout.write(f"local height: {local_height}")

        for peer in settings.PEERS:
            try:
                r = requests.get(f"{peer}/clinic/network/height", headers=headers, timeout=5)
                r.raise_for_status()
                remote = r.json()
            except requests.RequestException as e:
                self.stderr.write(f"{peer}: {e}")
                continue

            if remote["height"] <= local_height:
                self.stdout.write(f"{peer}: up to date (remote={remote['height']})")
                continue

            r = requests.get(
                f"{peer}/clinic/network/blocks",
                params={"from": local_height + 1},
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()
            blocks = r.json()["blocks"]

            for block in blocks:
                ok, err = services.validate_incoming_block(block)
                if not ok:
                    self.stderr.write(f"{peer}: reject block {block.get('index')}: {err}")
                    break
                services.add_block_from_dict(block)
                local_height = int(block["index"])
                self.stdout.write(f"{peer}: accepted block {block['index']}")