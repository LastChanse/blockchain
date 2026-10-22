from django.conf import settings
from django.db import models


class ChainBlock(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chain_blocks",
        null=True,
        blank=True
    )
    index = models.PositiveIntegerField(unique=True) 
    timestamp = models.CharField(max_length=64)
    prev_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)
    type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)

    class Meta:
        ordering = ("index",)


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )
    patients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="assigned_doctors",
    )