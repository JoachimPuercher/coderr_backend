from offers_app.models import Offer
from django_filters import FilterSet, NumberFilter

class OfferFilter(FilterSet):

    creator_id = NumberFilter(field_name="user")
    min_price = NumberFilter(field_name="min_price", lookup_expr="gte")
    max_delivery_time = NumberFilter(field_name="min_delivery_time", lookup_expr="lte")

    class Meta:

        model = Offer
        fields = ['creator_id']
