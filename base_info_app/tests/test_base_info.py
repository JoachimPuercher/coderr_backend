from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


class BaseInfoTests(APITestCase):
    """GET /api/base-info/: public figures that match the database."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.url = '/api/base-info/'

        self.business = User.objects.create_user(
            username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business')

        self.customer = User.objects.create_user(
            username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')

        Offer.objects.create(
            user=self.business,
            title='Logo Design',
            description='Nice logos')
        Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=4)

    def test_endpoint_is_public_and_counts_match_the_database(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['review_count'], 1)
        self.assertEqual(response.data['business_profile_count'], 1)
        self.assertEqual(response.data['offer_count'], 1)
        self.assertEqual(response.data['average_rating'], 4)

    def test_average_rating_without_reviews_is_zero(self):
        Review.objects.all().delete()
        response = self.client.get(self.url)

        self.assertEqual(response.data['review_count'], 0)
        self.assertEqual(response.data['average_rating'], 0)

    def test_average_rating_is_rounded_to_one_decimal(self):
        for name, rating in (('cust2', 4), ('cust3', 5)):
            reviewer = User.objects.create_user(
                username=name, password='SicheresPW123')
            Review.objects.create(
                business_user=self.business, reviewer=reviewer, rating=rating)
        response = self.client.get(self.url)

        # (4 + 4 + 5) / 3 = 4.333...
        self.assertEqual(response.data['average_rating'], 4.3)
