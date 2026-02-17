from django.db import models

# Create your models here.
from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel

class Region(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    def __str__(self): return self.name

class Department(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=140)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    class Meta:
        unique_together = ("name", "parent")
    def __str__(self): return self.name

class Position(UUIDModel, TimeStampedModel):
    title = models.CharField(max_length=140, db_index=True)
    def __str__(self): return self.title

class Grade(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    rank_order = models.PositiveIntegerField(db_index=True)
