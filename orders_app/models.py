from django.db import models
from django.contrib.auth.models import User
from offers_app.models import OfferTypeChoices

# Create your models here.

class OrderTypeChoices(models.TextChoices):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Orders(models.Model):
    customer_user = models.OneToOneField(User, on_delete=models.SET_NULL)
    business_user = models.OneToOneField(User, on_delete=models.SET_NULL)
    title = models.CharField(default="")
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(choices=OfferTypeChoices.choices)
    status = models.CharField(choices=OrderTypeChoices.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)