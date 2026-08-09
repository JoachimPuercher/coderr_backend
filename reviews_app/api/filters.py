from reviews_app.models import Review
from django_filters import FilterSet, NumberFilter

class ReviewFilter(FilterSet):

    business_user_id = NumberFilter(field_name="business_user")
    reviewer_id = NumberFilter(field_name="reviewer")

    class Meta:

        model = Review
        fields = []
