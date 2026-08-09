from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Review(models.Model):
    """A customer's rating of a business user."""

    # two relations to the same model, so both need their own reverse name
    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_reviews",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="written_reviews",
    )
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    description = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # nobody may review the same business twice
            models.UniqueConstraint(
                fields=["business_user", "reviewer"],
                name="unique_business_user_and_reviewer",
            )
        ]
