from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


class BaseInfoTests(APITestCase):

    def setUp(self):
        self.url = '/api/base-info/'

        self.business = User.objects.create_user(username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business_user')

        self.customer = User.objects.create_user(username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')

        Offer.objects.create(user=self.business, title='Logo Design', description='Nice logos')
        Review.objects.create(business_user=self.business, reviewer=self.customer, rating=4)

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
