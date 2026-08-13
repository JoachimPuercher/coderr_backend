from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from auth_app.models import UserProfile


class RegistrationTests(APITestCase):

    def setUp(self):
        self.url = reverse('registration')
        self.data = {
            'username': 'testuser',
            'email': 'test@mail.de',
            'password': 'SicheresPW123',
            'repeated_password': 'SicheresPW123',
            'type': 'customer',
        }

    def test_registration_creates_user(self):
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'test@mail.de')

    def test_registration_returns_token_and_user_data(self):
        response = self.client.post(self.url, self.data, format='json')
        user = User.objects.get(username='testuser')

        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@mail.de')
        self.assertEqual(response.data['user_id'], user.pk)
        self.assertEqual(response.data['token'], Token.objects.get(user=user).key)

    def test_registration_creates_profile_with_type(self):
        self.client.post(self.url, self.data, format='json')

        profile = UserProfile.objects.get(user__username='testuser')
        self.assertEqual(profile.type, 'customer')

    def test_password_is_hashed_and_not_returned(self):
        response = self.client.post(self.url, self.data, format='json')
        user = User.objects.get(username='testuser')

        self.assertNotEqual(user.password, self.data['password'])
        self.assertTrue(user.check_password(self.data['password']))
        self.assertNotIn('password', response.data)

    def test_passwords_do_not_match(self):
        data = {**self.data, 'repeated_password': 'AnderesPW123'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_username_already_taken(self):
        User.objects.create_user(username='testuser', password='irgendwas')
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_email_already_taken(self):
        User.objects.create_user(username='andereruser', email='test@mail.de', password='irgendwas')
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_email_comparison_ignores_case(self):
        User.objects.create_user(username='andereruser', email='test@mail.de', password='irgendwas')
        data = {**self.data, 'email': 'TEST@MAIL.DE'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_user_type(self):
        data = {**self.data, 'type': 'admin'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class LoginTests(APITestCase):

    def setUp(self):
        self.url = reverse('login')
        self.password = 'SicheresPW123'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@mail.de',
            password=self.password,
        )
        self.data = {
            'username': 'testuser',
            'password': self.password,
        }

    def test_login_returns_token_and_user_data(self):
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@mail.de')
        self.assertEqual(response.data['user_id'], self.user.pk)
        self.assertEqual(response.data['token'], Token.objects.get(user=self.user).key)

    def test_login_reuses_existing_token(self):
        existing = Token.objects.create(user=self.user)
        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.data['token'], existing.key)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_login_twice_returns_same_token(self):
        first = self.client.post(self.url, self.data, format='json')
        second = self.client.post(self.url, self.data, format='json')

        self.assertEqual(first.data['token'], second.data['token'])

    def test_password_not_returned(self):
        response = self.client.post(self.url, self.data, format='json')

        self.assertNotIn('password', response.data)

    def test_login_with_wrong_password(self):
        data = {**self.data, 'password': 'FalschesPW123'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_login_with_unknown_username(self):
        data = {**self.data, 'username': 'gibtesnicht'}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_error_message_does_not_reveal_which_field_was_wrong(self):
        wrong_password = self.client.post(
            self.url, {**self.data, 'password': 'FalschesPW123'}, format='json'
        )
        wrong_username = self.client.post(
            self.url, {**self.data, 'username': 'gibtesnicht'}, format='json'
        )

        self.assertEqual(wrong_password.data, wrong_username.data)

    def test_login_without_password(self):
        response = self.client.post(self.url, {'username': 'testuser'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_without_username(self):
        response = self.client.post(self.url, {'password': self.password}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class DocumentedUrlTests(APITestCase):
    """The paths from the API documentation have to exist exactly as written."""

    def test_registration_and_login_answer_under_their_documented_path(self):
        registration = self.client.post('/api/registration/', {}, format='json')
        login = self.client.post('/api/login/', {}, format='json')

        # 400 because the body is empty; a 404 would mean the route does not exist
        self.assertEqual(registration.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(login.status_code, status.HTTP_400_BAD_REQUEST)
