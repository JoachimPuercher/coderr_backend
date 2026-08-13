from django.db.models import Avg
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


class RetrieveBaseInfos(APIView):
    """Platform figures for the landing page.

    No serializer here: the answer is an evaluation, not a resource, so the dict is
    assembled by hand.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        reviews_count = Review.objects.count()
        # default=0 keeps the average a number while there are no reviews yet
        average_rating = Review.objects.aggregate(Avg("rating", default=0))
        profile_count = UserProfile.objects.filter(type="business").count()
        offer_count = Offer.objects.count()

        data = {
            "review_count": reviews_count,
            "average_rating": round(average_rating["rating__avg"], 1),
            "business_profile_count": profile_count,
            "offer_count": offer_count,
        }

        return Response(data, status.HTTP_200_OK)
