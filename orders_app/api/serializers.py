from rest_framework import serializers
from orders_app.models import Order, OrderTypeChoices
from offers_app.models import OfferDetail
from django.shortcuts import get_object_or_404

class OrderSerializer(serializers.ModelSerializer):
    """Read side of an order. Everything is read-only, the children open up single fields."""

    price = serializers.DecimalField(decimal_places=2, coerce_to_string=False, max_digits=10, read_only=True)

    class Meta:

        model = Order

        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at"
            ]

        read_only_fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "created_at",
            "updated_at"
        ]

    def create(self, validated_data):
        """Build the order from the chosen offer detail; the client only sends its id."""
        new_offer_id = validated_data["offer_detail_id"]
        new_offer_user_id = self.context["request"].user.id
        offer = get_object_or_404(OfferDetail, pk=new_offer_id)
        # the conditions are copied, not linked, so a later price change leaves the order untouched
        order = Order.objects.create(
            customer_user_id = new_offer_user_id,
            business_user_id = offer.offer.user_id,
            title = offer.title,
            revisions = offer.revisions,
            delivery_time_in_days = offer.delivery_time_in_days,
            price = offer.price,
            features = offer.features,
            offer_type = offer.offer_type,
            status = "in_progress"
            )

        return order


class OrderRetrieveWriteSerializer(OrderSerializer):
    """POST side: the offer detail id is the only thing the client may send."""

    offer_detail_id = serializers.IntegerField(write_only=True)

    class Meta(OrderSerializer.Meta):

        fields = OrderSerializer.Meta.fields + ["offer_detail_id"]


class OrderUpdateSerializer(OrderSerializer):
    """PATCH side: status is the only writable field."""

    # declared explicitly to take it out of the inherited read_only_fields
    status = serializers.ChoiceField(choices=OrderTypeChoices.choices)

    class Meta(OrderSerializer.Meta):

        fields = OrderSerializer.Meta.fields

    def validate(self, attrs):
        """Answer unknown keys with a 400 instead of dropping them silently."""
        # DRF only walks its own fields, so extra keys are invisible after this point
        sent = set(self.initial_data)
        allowed = set(attrs)
        too_much = sent - allowed

        if too_much:
            raise serializers.ValidationError(f"Not allowed. {", ".join(too_much)}")
        else:
            return attrs
