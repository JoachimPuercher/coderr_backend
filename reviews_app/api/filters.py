from django_filters import FilterSet, NumberFilter

from reviews_app.models import Review


class ReviewFilter(FilterSet):
    """Lets the review list be narrowed down to one provider or one author."""

    # the query parameters carry the _id suffix, the model fields do not
    business_user_id = NumberFilter(field_name="business_user")
    reviewer_id = NumberFilter(field_name="reviewer")

    class Meta:
        model = Review
        # empty on purpose: no filters are generated automatically
        fields = []
