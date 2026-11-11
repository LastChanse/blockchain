from django.db import models


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    node_id = models.CharField(max_length=64, unique=True)
    internal_url = models.URLField(help_text="URL внутри сети compose, например http://node0:8000")
    public_url = models.URLField(help_text="URL для браузера, например http://localhost:8081")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name