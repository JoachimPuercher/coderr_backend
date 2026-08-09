from django.db import models
from django.contrib.auth.models import User
from offers_app.models import OfferTypeChoices


class OrderTypeChoices(models.TextChoices):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(models.Model):
    """A booked offer package.

    The conditions are copied from the OfferDetail instead of being linked, so a later
    change to the offer does not rewrite orders that were already placed.
    """

    # SET_NULL keeps the order as a record even after one of the users is gone
    customer_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="customer_user_order")
    business_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="business_user_order")
    title = models.CharField(default="")
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(choices=OfferTypeChoices.choices)
    status = models.CharField(choices=OrderTypeChoices.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
