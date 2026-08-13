from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


def build_details():
    """Three valid packages as the offer endpoint expects them."""
    return [
        {
            'title': f'{offer_type} package',
            'revisions': 1,
            'delivery_time_in_days': 5,
            'price': price,
            'features': ['something'],
            'offer_type': offer_type,
        }
        for offer_type, price in [('basic', 100), ('standard', 200), ('premium', 300)]
    ]


class OfferTests(APITestCase):

    def setUp(self):
        self.business = User.objects.create_user(username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business')
        self.business_token = Token.objects.create(user=self.business)

        self.customer = User.objects.create_user(username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')
        self.customer_token = Token.objects.create(user=self.customer)

        self.offer = Offer.objects.create(user=self.business, title='Logo Design', description='Nice logos')
        for detail in build_details():
            OfferDetail.objects.create(offer=self.offer, **detail)

        self.url = '/api/offers/'

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_list_is_public_and_shows_the_annotated_minimums(self):
        response = self.client.get(self.url)
        offer = response.data['results'][0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(offer['min_price'], 100)
        self.assertEqual(offer['min_delivery_time'], 5)

    def test_business_user_can_create_an_offer_with_three_details(self):
        self.authenticate(self.business_token)
        response = self.client.post(
            self.url,
            {'title': 'New offer', 'description': 'Text', 'details': build_details()},
            format='json',
        )
        created = Offer.objects.get(title='New offer')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.details.count(), 3)
        self.assertEqual(created.user, self.business)

    def test_customer_may_not_create_an_offer(self):
        self.authenticate(self.customer_token)
        response = self.client.post(
            self.url,
            {'title': 'New offer', 'description': 'Text', 'details': build_details()},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_the_creator_may_change_an_offer(self):
        self.authenticate(self.customer_token)
        response = self.client.patch(f'/api/offers/{self.offer.pk}/', {'title': 'Hijacked'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, 'Logo Design')

    def test_unsupported_methods_do_not_crash(self):
        self.authenticate(self.business_token)

        options = self.client.options(f'/api/offers/{self.offer.pk}/')
        put = self.client.put(f'/api/offers/{self.offer.pk}/', {'title': 'x'}, format='json')

        self.assertEqual(options.status_code, status.HTTP_200_OK)
        self.assertEqual(put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
