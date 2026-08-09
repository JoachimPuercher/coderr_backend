from django_filters import FilterSet, NumberFilter

from offers_app.models import Offer


class OfferFilter(FilterSet):
    """Maps the query parameters of the offer list onto model and annotated fields."""

    # the parameter names differ from the field names, hence the explicit filters
    creator_id = NumberFilter(field_name="user")
    min_price = NumberFilter(field_name="min_price", lookup_expr="gte")
    max_delivery_time = NumberFilter(field_name="min_delivery_time", lookup_expr="lte")

    class Meta:
        model = Offer
        fields = ['creator_id']
