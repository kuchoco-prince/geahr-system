from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=30, blank=True)
    must_change_password = models.BooleanField(default=False)

class Role(models.Model):
    code = models.CharField(max_length=60, unique=True)  # e.g., CEO, HR_HO, HR_REGIONAL
    name = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.code

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "role")

