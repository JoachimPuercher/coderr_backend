from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import UserProfile


class ProfileDetailTests(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@mail.de',
            password='SicheresPW123',
            first_name='Max',
            last_name='Muster',
        )
        self.profile = UserProfile.objects.create(
            user=self.owner,
            type='business_user',
            location='Berlin',
            tel='0170123456',
        )
        self.owner_token = Token.objects.create(user=self.owner)

        self.other = User.objects.create_user(username='other', password='SicheresPW123')
        self.other_token = Token.objects.create(user=self.other)

        self.url = f'/api/profile/{self.profile.pk}/'

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
            {'first_name': 'Erika', 'email': 'erika@mail.de', 'location': 'Hamburg'},
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
        response = self.client.patch(self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.owner.first_name, 'Max')
        self.assertEqual(self.profile.tel, '0170123456')

    def test_unauthenticated_request_is_rejected(self):
        get_response = self.client.get(self.url)
        patch_response = self.client.patch(self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(get_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(patch_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_foreign_user_may_read_but_not_change(self):
        self.authenticate(self.other_token)
        get_response = self.client.get(self.url)
        patch_response = self.client.patch(self.url, {'location': 'Hamburg'}, format='json')

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, 'Berlin')

    def test_unknown_profile_returns_404(self):
        self.authenticate(self.owner_token)
        response = self.client.get('/api/profile/9999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
