import io
import os
import shutil
import tempfile
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from PIL import Image
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
        for offer_type, price in [
            ('basic', 100), ('standard', 200), ('premium', 300),
        ]
    ]


class OfferTests(APITestCase):
    """Offer list, creation and editing, including the role checks."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.business = User.objects.create_user(
            username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business')
        self.business_token = Token.objects.create(user=self.business)

        self.customer = User.objects.create_user(
            username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')
        self.customer_token = Token.objects.create(user=self.customer)

        self.offer = Offer.objects.create(
            user=self.business,
            title='Logo Design',
            description='Nice logos')
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
            {
                'title': 'New offer',
                'description': 'Text',
                'details': build_details(),
            },
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
            {
                'title': 'New offer',
                'description': 'Text',
                'details': build_details(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_the_creator_may_change_an_offer(self):
        self.authenticate(self.customer_token)
        response = self.client.patch(
            f'/api/offers/{self.offer.pk}/',
            {'title': 'Hijacked'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, 'Logo Design')

    def test_unsupported_methods_do_not_crash(self):
        self.authenticate(self.business_token)

        options = self.client.options(f'/api/offers/{self.offer.pk}/')
        put = self.client.put(
            f'/api/offers/{self.offer.pk}/', {'title': 'x'}, format='json')

        self.assertEqual(options.status_code, status.HTTP_200_OK)
        self.assertEqual(put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def create_offer(self, details):
        self.authenticate(self.business_token)
        return self.client.post(
            self.url,
            {'title': 'New offer', 'description': 'Text', 'details': details},
            format='json',
        )

    def test_offer_needs_exactly_three_details(self):
        too_few = self.create_offer(build_details()[:2])
        too_many = self.create_offer(build_details() + build_details()[:1])

        self.assertEqual(too_few.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(too_many.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Offer.objects.count(), 1)

    def test_the_three_details_need_different_types(self):
        details = build_details()
        for detail in details:
            detail['offer_type'] = 'basic'
        response = self.create_offer(details)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Offer.objects.count(), 1)

    def test_creator_can_update_the_title_and_a_single_detail(self):
        basic = self.offer.details.get(offer_type='basic')
        self.authenticate(self.business_token)
        response = self.client.patch(
            f'/api/offers/{self.offer.pk}/',
            {
                'title': 'Updated',
                'details': [{'offer_type': 'basic', 'price': 150}],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['details']), 3)
        self.offer.refresh_from_db()
        basic.refresh_from_db()
        self.assertEqual(self.offer.title, 'Updated')
        self.assertEqual(basic.price, 150)
        # the other packages and the id of the changed one stay as they were
        self.assertEqual(
            self.offer.details.get(offer_type='standard').price, 200)
        self.assertEqual(response.data['details'][0]['id'], basic.pk)

    def test_detail_without_offer_type_is_rejected(self):
        self.authenticate(self.business_token)
        response = self.client.patch(
            f'/api/offers/{self.offer.pk}/',
            {'details': [{'price': 150}]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creator_can_delete_an_offer_with_its_details(self):
        self.authenticate(self.business_token)
        response = self.client.delete(f'/api/offers/{self.offer.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())

    def test_foreign_user_may_not_delete_an_offer(self):
        self.authenticate(self.customer_token)
        response = self.client.delete(f'/api/offers/{self.offer.pk}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Offer.objects.exists())

    def test_single_offer_shows_its_details_as_links(self):
        self.authenticate(self.customer_token)
        response = self.client.get(f'/api/offers/{self.offer.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['details']), 3)
        self.assertIn('url', response.data['details'][0])
        self.assertEqual(response.data['min_price'], 100)

    def test_single_offer_needs_authentication(self):
        response = self.client.get(f'/api/offers/{self.offer.pk}/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_offer_returns_404(self):
        self.authenticate(self.customer_token)
        response = self.client.get('/api/offers/9999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_offer_detail_endpoint_returns_the_package(self):
        detail = self.offer.details.get(offer_type='basic')
        self.authenticate(self.customer_token)
        response = self.client.get(f'/api/offerdetails/{detail.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['offer_type'], 'basic')
        # a JSON number, the string "100.00" would not be equal
        self.assertEqual(response.data['price'], 100)

    def test_offer_detail_endpoint_needs_authentication_and_an_id(self):
        anonymous = self.client.get('/api/offerdetails/1/')
        self.authenticate(self.customer_token)
        unknown = self.client.get('/api/offerdetails/9999/')

        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unknown.status_code, status.HTTP_404_NOT_FOUND)


class OfferFilterTests(APITestCase):
    """Query parameters and paging of the public offer list."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.logo_owner = User.objects.create_user(
            username='biz', password='SicheresPW123')
        self.web_owner = User.objects.create_user(
            username='biz2', password='SicheresPW123')
        self.make_offer(self.logo_owner, 'Logo Design', 100, 5)
        self.make_offer(self.web_owner, 'Website Build', 500, 10)
        self.url = '/api/offers/'

    def make_offer(self, user, title, price, days):
        offer = Offer.objects.create(
            user=user, title=title, description=f'{title} text')
        OfferDetail.objects.create(
            offer=offer,
            title='basic package',
            revisions=1,
            delivery_time_in_days=days,
            price=price,
            features=[],
            offer_type='basic',
        )

    def titles(self, query):
        response = self.client.get(f'{self.url}?{query}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [offer['title'] for offer in response.data['results']]

    def test_filter_by_creator(self):
        self.assertEqual(
            self.titles(f'creator_id={self.logo_owner.pk}'), ['Logo Design'])

    def test_filter_by_min_price(self):
        self.assertEqual(self.titles('min_price=300'), ['Website Build'])

    def test_filter_by_max_delivery_time(self):
        self.assertEqual(self.titles('max_delivery_time=7'), ['Logo Design'])

    def test_search_in_title_and_description(self):
        self.assertEqual(self.titles('search=website'), ['Website Build'])

    def test_ordering_by_min_price(self):
        self.assertEqual(
            self.titles('ordering=-min_price'),
            ['Website Build', 'Logo Design'])

    def test_page_size_limits_the_results(self):
        response = self.client.get(f'{self.url}?page_size=1')

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['next'])

    def test_invalid_filter_value_is_rejected(self):
        response = self.client.get(f'{self.url}?min_price=abc')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


def make_image():
    """A small valid PNG; random pixels stop it from shrinking to nothing."""
    buffer = io.BytesIO()
    Image.frombytes('RGB', (20, 20), os.urandom(20 * 20 * 3)).save(
        buffer, 'PNG')
    return SimpleUploadedFile(
        'offer.png', buffer.getvalue(), content_type='image/png')


class OfferImageTests(APITestCase):
    """Image upload on an offer, including the size limit."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.business = User.objects.create_user(
            username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business')
        token = Token.objects.create(user=self.business)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.offer = Offer.objects.create(
            user=self.business, title='Logo Design', description='Nice logos')
        self.url = f'/api/offers/{self.offer.pk}/'

    def test_image_within_the_limit_is_stored(self):
        media = tempfile.mkdtemp()
        # the upload goes to a throwaway folder instead of the real media/
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        with self.settings(MEDIA_ROOT=media):
            response = self.client.patch(
                self.url, {'image': make_image()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.image)

    def test_image_above_the_limit_is_rejected(self):
        # a lower limit spares the test a file of several megabytes
        with patch('offers_app.api.serializers.MAX_IMAGE_SIZE', 100):
            response = self.client.patch(
                self.url, {'image': make_image()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.offer.refresh_from_db()
        self.assertFalse(self.offer.image)
