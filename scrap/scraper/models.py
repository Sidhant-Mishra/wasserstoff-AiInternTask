from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from .manager import CustomUserManager
# Create your models here.

class User(AbstractUser):
    username = None
    id = models.UUIDField(default=uuid.uuid4,unique=True, primary_key=True)
    name = models.CharField(max_length=90)
    email = models.EmailField(unique=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    def __str__(self):
        return self.email
    

class Excel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='excel')
    updatedat = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.file} {str(self.updatedat)}"