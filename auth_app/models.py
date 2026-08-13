from django.contrib.auth.models import User
from django.db import models


class UserTypeChoices(models.TextChoices):
    CUSTOMER = "customer"
    BUSINESS = "business"


class UserProfile(models.Model):
    """Coderr specific data next to Django's User, plus the role of the account.

    Both roles share one model; `type` decides which fields the frontend shows.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    type = models.CharField(choices=UserTypeChoices.choices, max_length=20)
    file = models.ImageField(upload_to='image_uploads/', blank=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=50, default="")
    tel = models.CharField(max_length=50, default="")
    description = models.TextField(default="")
    working_hours = models.CharField(max_length=50, default="")
    created_at = models.DateTimeField(auto_now_add=True)
