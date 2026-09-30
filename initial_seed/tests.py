import base64
import io
import json
import os
import shutil
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from auth_app.models import UserProfile
from initial_seed.management.commands import generate_seed_images, seed_demo
from offers_app.models import Offer, OfferDetail
from orders_app.models import Order
from reviews_app.models import Review


def load_seed_data():
    with seed_demo.DATA_FILE.open(encoding='utf-8') as fh:
        return json.load(fh)


class SeedDemoTests(TestCase):
    """The seed command fills an empty database exactly once."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # pictures must not land in the real media folder
        cls.media_dir = tempfile.mkdtemp()
        # a fast hasher: 25 accounts per test would otherwise
        # spend most of the time in PBKDF2
        cls.settings_override = override_settings(
            MEDIA_ROOT=cls.media_dir,
            PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        )
        cls.settings_override.enable()
        cls.data = load_seed_data()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        shutil.rmtree(cls.media_dir, ignore_errors=True)
        super().tearDownClass()

    def run_seed(self):
        out = io.StringIO()
        call_command('seed_demo', stdout=out)
        return out.getvalue()

    def test_seed_creates_all_accounts_offers_orders_and_reviews(self):
        self.run_seed()

        self.assertEqual(
            UserProfile.objects.filter(type='business').count(),
            len(self.data['businesses']))
        self.assertEqual(
            UserProfile.objects.filter(type='customer').count(),
            len(self.data['customers']))
        self.assertEqual(Offer.objects.count(), len(self.data['businesses']))
        self.assertEqual(
            OfferDetail.objects.count(), 3 * len(self.data['businesses']))
        self.assertEqual(Order.objects.count(), len(self.data['orders']))
        self.assertEqual(Review.objects.count(), len(self.data['reviews']))

    def test_every_offer_has_the_three_package_types(self):
        self.run_seed()

        for offer in Offer.objects.all():
            types = set(offer.details.values_list('offer_type', flat=True))
            self.assertEqual(types, {'basic', 'standard', 'premium'})

    def test_second_run_adds_nothing(self):
        self.run_seed()
        before = (
            User.objects.count(), Offer.objects.count(),
            OfferDetail.objects.count(), Order.objects.count(),
            Review.objects.count())

        output = self.run_seed()

        after = (
            User.objects.count(), Offer.objects.count(),
            OfferDetail.objects.count(), Order.objects.count(),
            Review.objects.count())
        self.assertEqual(before, after)
        self.assertIn('übersprungen', output)

    def test_emails_are_lowercase_and_unique(self):
        self.run_seed()

        emails = list(User.objects.values_list('email', flat=True))
        self.assertEqual(emails, [email.lower() for email in emails])
        self.assertEqual(len(emails), len(set(emails)))

    def test_seed_accounts_can_log_in_with_the_shared_password(self):
        self.run_seed()
        username = self.data['businesses'][0]['username']

        self.assertTrue(self.client.login(
            username=username, password=self.data['password']))

    def test_orders_copy_the_detail_values(self):
        self.run_seed()
        entry = self.data['orders'][0]
        detail = OfferDetail.objects.get(
            offer__user__username=entry['business'],
            offer_type=entry['offer_type'])

        order = Order.objects.get(
            customer_user__username=entry['customer'],
            business_user__username=entry['business'])

        self.assertEqual(order.title, detail.title)
        self.assertEqual(order.price, detail.price)
        self.assertEqual(order.features, detail.features)
        self.assertEqual(order.status, entry['status'])

    def test_profile_picture_is_stored_when_a_file_exists(self):
        username = self.data['businesses'][0]['username']
        if seed_demo.find_image('profiles', username) is None:
            self.skipTest('no seed picture present for the first business')

        self.run_seed()

        profile = UserProfile.objects.get(user__username=username)
        self.assertTrue(profile.file.name.startswith('image_uploads/'))
        self.assertIsNotNone(profile.uploaded_at)
        self.assertTrue(Path(self.media_dir, profile.file.name).exists())


class GenerateSeedImagesTests(SimpleTestCase):
    """The image command talks to OpenAI only through urlopen, so
    a mocked answer is enough to check the file handling.
    """

    def setUp(self):
        self.image_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.image_dir, ignore_errors=True)
        patcher = patch.object(
            generate_seed_images, 'IMAGE_DIR', self.image_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def fake_response(*args, **kwargs):
        payload = {
            'data': [{'b64_json': base64.b64encode(b'JPEGDATA').decode()}]}
        return io.BytesIO(json.dumps(payload).encode())

    def test_missing_api_key_is_a_command_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(CommandError):
                call_command('generate_seed_images', stdout=io.StringIO())

    def test_pictures_are_written_and_existing_ones_skipped(self):
        data = load_seed_data()
        expected = len(data['businesses']) * 2 + len(data['customers'])

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch.object(
                    generate_seed_images.urllib.request, 'urlopen',
                    side_effect=self.fake_response) as urlopen:
                call_command('generate_seed_images', stdout=io.StringIO())
                first_calls = urlopen.call_count
                call_command('generate_seed_images', stdout=io.StringIO())
                second_calls = urlopen.call_count

        written = list(self.image_dir.rglob('*.jpg'))
        self.assertEqual(len(written), expected)
        self.assertEqual(first_calls, expected)
        self.assertEqual(second_calls, expected)
        self.assertEqual(written[0].read_bytes(), b'JPEGDATA')

    def test_only_offers_limits_the_run(self):
        data = load_seed_data()

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch.object(
                    generate_seed_images.urllib.request, 'urlopen',
                    side_effect=self.fake_response):
                call_command(
                    'generate_seed_images', only='offers',
                    stdout=io.StringIO())

        self.assertEqual(
            len(list((self.image_dir / 'offers').glob('*.jpg'))),
            len(data['businesses']))
        self.assertFalse((self.image_dir / 'profiles').exists())

    def test_timeout_is_retried_and_then_succeeds(self):
        data = load_seed_data()
        calls = []

        def flaky(*args, **kwargs):
            # the very first request times out, every later one succeeds
            calls.append(1)
            if len(calls) == 1:
                raise TimeoutError('read timed out')
            return self.fake_response()

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch.object(
                    generate_seed_images.urllib.request, 'urlopen',
                    side_effect=flaky):
                call_command(
                    'generate_seed_images', only='offers',
                    stdout=io.StringIO())

        self.assertEqual(len(calls), len(data['businesses']) + 1)
        self.assertEqual(
            len(list((self.image_dir / 'offers').glob('*.jpg'))),
            len(data['businesses']))

    def test_http_error_becomes_a_command_error(self):
        error = urllib.error.HTTPError(
            generate_seed_images.API_URL, 401, 'Unauthorized', {},
            io.BytesIO(b'{"error": "bad key"}'))

        with patch.dict(os.environ, {'OPENAI_API_KEY': 'wrong'}):
            with patch.object(
                    generate_seed_images.urllib.request, 'urlopen',
                    side_effect=error):
                with self.assertRaisesMessage(CommandError, '401'):
                    call_command(
                        'generate_seed_images', stdout=io.StringIO())
