from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    expiry_date = models.DateField()

    def is_active(self):
        return self.expiry_date >= timezone.now().date()

    def __str__(self):
        return f"Συνδρομή για {self.user.username} έως {self.expiry_date}"
