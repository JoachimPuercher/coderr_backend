from django.core.cache import cache
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import UserProfile


class ProfileDetailTests(APITestCase):
    """GET and PATCH on a single profile, including owner checks."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@mail.de',
            password='SicheresPW123',
            first_name='Max',
            last_name='Muster',
        )
        self.profile = UserProfile.objects.create(
            user=self.owner,
            type='business',
            location='Berlin',
            tel='0170123456',
        )
        self.owner_token = Token.objects.create(user=self.owner)

        self.other = User.objects.create_user(
            username='other', password='SicheresPW123')
        self.other_token = Token.objects.create(user=self.other)

        # the url carries the user id, which is not necessarily the profile id
        self.url = f'/api/profile/{self.owner.pk}/'

    def authenticate(self, token):
        """Send all following requests with the given token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_owner_can_retrieve_profile(self):
        self.authenticate(self.owner_token)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.owner.pk)
        self.assertEqual(response.data['username'], 'owner')
        self.assertEqual(response.data['location'], 'Berlin')

    def test_owner_can_update_profile_and_user_fields(self):
        self.authenticate(self.owner_token)
        response = self.client.patch(
            self.url,
            {
                'first_name': 'Erika',
                'email': 'erika@mail.de',
                'location': 'Hamburg',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.owner.first_name, 'Erika')
        self.assertEqual(self.owner.email, 'erika@mail.de')
        self.assertEqual(self.profile.location, 'Hamburg')

    def test_update_of_a_single_field_keeps_the_rest_untouched(self):
        self.authenticate(self.owner_token)
        response = self.client.patch(
            self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.owner.first_name, 'Max')
        self.assertEqual(self.profile.tel, '0170123456')

    def test_unauthenticated_request_is_rejected(self):
        get_response = self.client.get(self.url)
        patch_response = self.client.patch(
            self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(
            get_response.status_code,
            status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            patch_response.status_code,
            status.HTTP_401_UNAUTHORIZED)

    def test_foreign_user_may_read_but_not_change(self):
        self.authenticate(self.other_token)
        get_response = self.client.get(self.url)
        patch_response = self.client.patch(
            self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, 'Berlin')

    def test_unknown_profile_returns_404(self):
        self.authenticate(self.owner_token)
        response = self.client.get('/api/profile/9999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_email_of_another_user_is_rejected(self):
        self.other.email = 'taken@mail.de'
        self.other.save()
        self.authenticate(self.owner_token)
        response = self.client.patch(
            self.url, {'email': 'TAKEN@mail.de'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.email, 'owner@mail.de')

    def test_owner_may_send_the_own_email_again(self):
        self.authenticate(self.owner_token)
        response = self.client.patch(
            self.url, {'email': 'owner@mail.de'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_email_is_rejected(self):
        self.authenticate(self.owner_token)
        response = self.client.patch(
            self.url, {'email': 'keine-mail'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_type_cannot_be_changed(self):
        self.authenticate(self.owner_token)
        self.client.patch(self.url, {'type': 'customer'}, format='json')

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.type, 'business')

    def test_patch_on_an_unknown_profile_returns_404(self):
        self.authenticate(self.owner_token)
        response = self.client.patch(
            '/api/profile/9999/', {'location': 'Hamburg'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_is_not_allowed(self):
        self.authenticate(self.owner_token)
        response = self.client.put(
            self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_empty_fields_are_strings_not_null(self):
        UserProfile.objects.create(user=self.other, type='customer')
        self.authenticate(self.owner_token)
        response = self.client.get(f'/api/profile/{self.other.pk}/')

        for field in ('first_name', 'last_name', 'location', 'tel',
                      'description', 'working_hours'):
            self.assertEqual(response.data[field], '', field)


class ProfileLookupTests(APITestCase):
    """The url of a profile carries the user id, not the id of the profile row.
    """

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        # a user without a profile pushes the two id sequences apart
        User.objects.create_user(
            username='no_profile',
            password='SicheresPW123')

        self.user = User.objects.create_user(
            username='owner', password='SicheresPW123')
        self.profile = UserProfile.objects.create(
            user=self.user, type='business')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_ids_really_diverge(self):
        self.assertNotEqual(self.profile.pk, self.user.pk)

    def test_profile_is_found_by_the_user_id(self):
        response = self.client.get(f'/api/profile/{self.user.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.pk)
        self.assertEqual(response.data['username'], 'owner')

    def test_profile_id_is_not_accepted(self):
        response = self.client.get(f'/api/profile/{self.profile.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProfileListTests(APITestCase):
    """Both list endpoints live under the documented plural path."""

    def setUp(self):
        # throttle counters live in the cache and
        # would carry over from the previous test
        cache.clear()
        self.business = User.objects.create_user(
            username='biz', password='SicheresPW123')
        UserProfile.objects.create(user=self.business, type='business')

        self.customer = User.objects.create_user(
            username='cust', password='SicheresPW123')
        UserProfile.objects.create(user=self.customer, type='customer')

        token = Token.objects.create(user=self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_business_list_returns_only_business_profiles(self):
        response = self.client.get('/api/profiles/business/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'business')

    def test_customer_list_returns_only_customer_profiles(self):
        response = self.client.get('/api/profiles/customer/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'customer')

    def test_lists_need_authentication(self):
        self.client.credentials()
        response = self.client.get('/api/profiles/business/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_list_needs_authentication(self):
        self.client.credentials()
        response = self.client.get('/api/profiles/customer/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_entries_carry_the_documented_fields(self):
        business = self.client.get('/api/profiles/business/').data[0]
        customer = self.client.get('/api/profiles/customer/').data[0]

        self.assertIn('working_hours', business)
        self.assertNotIn('email', business)
        self.assertIn('uploaded_at', customer)
        self.assertNotIn('tel', customer)
