from django.contrib.auth.models import User
from django.db import models


class OfferTypeChoices(models.TextChoices):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class Offer(models.Model):
    """A service a business user offers, split into three packages."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers")
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="offer_images/", blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OfferDetail(models.Model):
    """One package of an offer with its own price and scope."""

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
    title = models.CharField(max_length=255)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(max_length=20, choices=OfferTypeChoices.choices)

    class Meta:
        constraints = [
            # every type may exist only once per offer
            models.UniqueConstraint(
                fields=["offer", "offer_type"],
                name="unique_offer_type_per_offer",
            )
        ]
