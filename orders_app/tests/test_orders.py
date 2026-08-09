from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail
from orders_app.models import Order


class OrderTests(APITestCase):

    def setUp(self):
        self.customer = User.objects.create_user(username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')
        self.customer_token = Token.objects.create(user=self.customer)

        self.business = User.objects.create_user(username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business_user')
        self.business_token = Token.objects.create(user=self.business)

        self.offer = Offer.objects.create(user=self.business, title='Logo Design', description='Nice logos')
        self.detail = OfferDetail.objects.create(
            offer=self.offer,
            title='basic package',
            revisions=2,
            delivery_time_in_days=5,
            price=100,
            features=['Logo'],
            offer_type='basic',
        )
        self.url = '/api/orders/'

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def make_order(self, state='in_progress'):
        return Order.objects.create(
            customer_user=self.customer,
            business_user=self.business,
            title='basic package',
            revisions=2,
            delivery_time_in_days=5,
            price=100,
            features=['Logo'],
            offer_type='basic',
            status=state,
        )

    def test_customer_can_order_an_offer_detail(self):
        self.authenticate(self.customer_token)
        response = self.client.post(self.url, {'offer_detail_id': self.detail.pk}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

    def test_order_copies_the_conditions_of_the_detail(self):
        self.authenticate(self.customer_token)
        response = self.client.post(self.url, {'offer_detail_id': self.detail.pk}, format='json')

        self.assertEqual(response.data['title'], 'basic package')
        self.assertEqual(response.data['price'], 100)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_order_connects_customer_and_provider(self):
        self.authenticate(self.customer_token)
        self.client.post(self.url, {'offer_detail_id': self.detail.pk}, format='json')
        order = Order.objects.get()

        self.assertEqual(order.customer_user, self.customer)
        self.assertEqual(order.business_user, self.business)

    def test_business_user_may_not_order(self):
        self.authenticate(self.business_token)
        response = self.client.post(self.url, {'offer_detail_id': self.detail.pk}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 0)

    def test_list_shows_the_orders_of_both_sides(self):
        self.make_order()
        self.authenticate(self.business_token)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_provider_can_change_the_status(self):
        order = self.make_order()
        self.authenticate(self.business_token)
        response = self.client.patch(f'/api/orders/{order.pk}/', {'status': 'completed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')

    def test_additional_fields_are_rejected(self):
        order = self.make_order()
        self.authenticate(self.business_token)
        response = self.client.patch(
            f'/api/orders/{order.pk}/',
            {'status': 'completed', 'price': 1},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_an_admin_may_delete(self):
        order = self.make_order()
        self.authenticate(self.business_token)
        response = self.client.delete(f'/api/orders/{order.pk}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 1)

    def test_running_and_completed_orders_are_counted(self):
        self.make_order('in_progress')
        self.make_order('completed')
        self.authenticate(self.customer_token)

        running = self.client.get(f'/api/order-count/{self.business.pk}/')
        done = self.client.get(f'/api/completed-order-count/{self.business.pk}/')

        self.assertEqual(running.data['order_count'], 1)
        self.assertEqual(done.data['completed_order_count'], 1)

    def test_count_for_an_unknown_user_returns_404(self):
        self.authenticate(self.customer_token)
        response = self.client.get('/api/order-count/9999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
