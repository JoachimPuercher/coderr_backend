from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from reviews_app.models import Review


class ReviewTests(APITestCase):
    """Writing, filtering and editing reviews, one review per business."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.customer = User.objects.create_user(
            username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')
        self.customer_token = Token.objects.create(user=self.customer)

        self.other_customer = User.objects.create_user(
            username='cust2', password='SicheresPW123')
        UserProfile.objects.create(user=self.other_customer, type='customer')
        self.other_customer_token = Token.objects.create(
            user=self.other_customer)

        self.business = User.objects.create_user(
            username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business')

        self.url = '/api/reviews/'
        self.payload = {
            'business_user': self.business.pk,
            'rating': 4,
            'description': 'Solid work.'}

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_can_write_a_review_and_becomes_its_author(self):
        self.authenticate(self.customer_token)
        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.get().reviewer, self.customer)

    def test_second_review_for_the_same_business_is_rejected(self):
        self.authenticate(self.customer_token)
        self.client.post(self.url, self.payload, format='json')
        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_list_can_be_filtered_by_business_user(self):
        Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=4)
        self.authenticate(self.customer_token)

        hit = self.client.get(
            f'{self.url}?business_user_id={self.business.pk}')
        miss = self.client.get(
            f'{self.url}?business_user_id={self.customer.pk}')

        self.assertEqual(hit.status_code, status.HTTP_200_OK)
        self.assertEqual(len(hit.data), 1)
        self.assertEqual(len(miss.data), 0)

    def test_author_can_change_the_rating(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=4)
        self.authenticate(self.customer_token)
        response = self.client.patch(
            f'{self.url}{review.pk}/', {'rating': 5}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)

    def test_foreign_user_may_not_change_or_delete_the_review(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=4)
        self.authenticate(self.other_customer_token)

        patch_response = self.client.patch(
            f'{self.url}{review.pk}/', {'rating': 1}, format='json')
        delete_response = self.client.delete(f'{self.url}{review.pk}/')

        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_403_FORBIDDEN)
        self.assertEqual(Review.objects.count(), 1)

    def test_business_user_may_not_write_a_review(self):
        other_business = User.objects.create_user(
            username='biz2', password='SicheresPW123')
        UserProfile.objects.create(user=other_business, type='business')
        self.authenticate(Token.objects.create(user=other_business))
        response = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Review.objects.exists())

    def test_rating_has_to_be_between_one_and_five(self):
        self.authenticate(self.customer_token)
        too_low = self.client.post(
            self.url, {**self.payload, 'rating': 0}, format='json')
        too_high = self.client.post(
            self.url, {**self.payload, 'rating': 6}, format='json')

        self.assertEqual(too_low.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(too_high.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_only_business_users_can_be_reviewed(self):
        self.authenticate(self.customer_token)
        response = self.client.post(
            self.url,
            {**self.payload, 'business_user': self.other_customer.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('business_user', response.data)

    def test_business_user_of_a_review_cannot_be_changed(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=4)
        self.authenticate(self.customer_token)
        response = self.client.patch(
            f'{self.url}{review.pk}/',
            {'business_user': self.other_customer.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        review.refresh_from_db()
        self.assertEqual(review.business_user, self.business)

    def test_author_can_delete_the_review(self):
        review = Review.objects.create(
            business_user=self.business,
            reviewer=self.customer,
            rating=4)
        self.authenticate(self.customer_token)
        response = self.client.delete(f'{self.url}{review.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.exists())

    def test_unknown_review_returns_404(self):
        self.authenticate(self.customer_token)
        response = self.client.patch(
            f'{self.url}9999/', {'rating': 5}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_can_be_filtered_by_reviewer_and_ordered_by_rating(self):
        Review.objects.create(
            business_user=self.business, reviewer=self.customer, rating=2)
        Review.objects.create(
            business_user=self.business,
            reviewer=self.other_customer,
            rating=5)
        self.authenticate(self.customer_token)

        own = self.client.get(f'{self.url}?reviewer_id={self.customer.pk}')
        ordered = self.client.get(f'{self.url}?ordering=-rating')

        self.assertEqual([r['rating'] for r in own.data], [2])
        self.assertEqual([r['rating'] for r in ordered.data], [5, 2])
