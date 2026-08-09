from django.db.models.aggregates import Avg
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from reviews_app.models import Review
from auth_app.models import UserProfile
from offers_app.models import Offer

class RetrieveBaseInfos(APIView):

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        reviews_count = Review.objects.count()
        average_rating = Review.objects.aggregate(Avg("rating", default=0))
        profile_count = UserProfile.objects.filter(type="business_user").count()
        offer_count = Offer.objects.count()

        data = {
            "review_count" : reviews_count,
            "average_rating" : round(average_rating["rating__avg"], 1),
            "business_profile_count" : profile_count,
            "offer_count" : offer_count
        }

        return Response(data, status.HTTP_200_OK)