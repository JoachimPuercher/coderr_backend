"""Fill an empty database with the demo accounts, offers, orders and reviews
from initial_seed/data.json, including the pictures in initial_seed/images/.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from auth_app.models import UserProfile, UserTypeChoices
from offers_app.models import Offer, OfferDetail, OfferTypeChoices
from orders_app.models import Order
from reviews_app.models import Review

SEED_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = SEED_DIR / 'data.json'
IMAGE_DIR = SEED_DIR / 'images'
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
REQUIRED_TYPES = {choice.value for choice in OfferTypeChoices}


def load_data():
    """Read data.json next to the app; a broken file should stop the run."""
    try:
        with DATA_FILE.open(encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError) as err:
        raise CommandError(f'Cannot read {DATA_FILE}: {err}')


def find_image(folder, username):
    """The first file named after the username with a known extension."""
    for extension in IMAGE_EXTENSIONS:
        path = IMAGE_DIR / folder / f'{username}{extension}'
        if path.exists():
            return path
    return None


class Command(BaseCommand):
    help = 'Seed demo businesses, customers, offers, orders and reviews.'

    def handle(self, *args, **options):
        data = load_data()
        password = data['password']
        self.missing_images = []
        self.counts = {
            'users': 0, 'offers': 0, 'details': 0,
            'orders': 0, 'reviews': 0, 'skipped': 0,
        }

        # one transaction so a broken entry leaves no half-seeded database
        with transaction.atomic():
            for entry in data['businesses']:
                user = self.create_account(
                    entry, UserTypeChoices.BUSINESS, password)
                if user is not None:
                    self.create_offer(user, entry['offer'])
            for entry in data['customers']:
                self.create_account(
                    entry, UserTypeChoices.CUSTOMER, password)
            for entry in data['orders']:
                self.create_order(entry)
            for entry in data['reviews']:
                self.create_review(entry)

        self.print_summary(password)

    def create_account(self, entry, user_type, password):
        """User plus profile plus picture; None when the username exists."""
        username = entry['username']
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'übersprungen: {username} existiert bereits')
            self.counts['skipped'] += 1
            return None

        user = User.objects.create_user(
            username=username,
            email=entry['email'].lower(),
            password=password,
            first_name=entry.get('first_name', ''),
            last_name=entry.get('last_name', ''),
        )
        profile = UserProfile(
            user=user,
            type=user_type,
            location=entry.get('location', ''),
            tel=entry.get('tel', ''),
            description=entry.get('description', ''),
            working_hours=entry.get('working_hours', ''),
        )
        if self.attach_image(profile.file, 'profiles', username):
            profile.uploaded_at = timezone.now()
        profile.save()
        self.counts['users'] += 1
        return user

    def create_offer(self, user, entry):
        """One offer with exactly one basic, standard and premium detail."""
        types = [detail['offer_type'] for detail in entry['details']]
        if len(types) != 3 or set(types) != REQUIRED_TYPES:
            raise CommandError(
                f'{user.username}: an offer needs exactly one basic, '
                f'standard and premium detail, got {types}')

        offer = Offer(
            user=user,
            title=entry['title'],
            description=entry['description'],
        )
        self.attach_image(offer.image, 'offers', user.username)
        offer.save()
        for detail in entry['details']:
            OfferDetail.objects.create(
                offer=offer,
                title=detail['title'],
                revisions=detail['revisions'],
                delivery_time_in_days=detail['delivery_time_in_days'],
                price=Decimal(str(detail['price'])),
                features=detail.get('features', []),
                offer_type=detail['offer_type'],
            )
        self.counts['offers'] += 1
        self.counts['details'] += 3

    def create_order(self, entry):
        """Copy the detail's conditions into an order, like the API does."""
        customer = User.objects.filter(username=entry['customer']).first()
        detail = OfferDetail.objects.filter(
            offer__user__username=entry['business'],
            offer_type=entry['offer_type'],
        ).select_related('offer').first()
        if customer is None or detail is None:
            self.stdout.write(
                f'übersprungen: Order {entry["customer"]} -> '
                f'{entry["business"]} ({entry["offer_type"]}), '
                'Account oder Angebot fehlt')
            return
        exists = Order.objects.filter(
            customer_user=customer,
            business_user=detail.offer.user,
            offer_type=detail.offer_type,
        ).exists()
        if exists:
            return

        Order.objects.create(
            customer_user=customer,
            business_user=detail.offer.user,
            title=detail.title,
            revisions=detail.revisions,
            delivery_time_in_days=detail.delivery_time_in_days,
            price=detail.price,
            features=detail.features,
            offer_type=detail.offer_type,
            status=entry['status'],
        )
        self.counts['orders'] += 1

    def create_review(self, entry):
        """A customer's review of a business; one per pair."""
        reviewer = User.objects.filter(username=entry['reviewer']).first()
        business = User.objects.filter(
            username=entry['business'],
            userprofile__type=UserTypeChoices.BUSINESS,
        ).first()
        if reviewer is None or business is None:
            self.stdout.write(
                f'übersprungen: Review {entry["reviewer"]} -> '
                f'{entry["business"]}, Account fehlt oder kein Business')
            return
        exists = Review.objects.filter(
            business_user=business, reviewer=reviewer).exists()
        if exists:
            return

        Review.objects.create(
            business_user=business,
            reviewer=reviewer,
            rating=entry['rating'],
            description=entry.get('description', ''),
        )
        self.counts['reviews'] += 1

    def attach_image(self, field, folder, username):
        """Store the seed picture through the field so it
        lands under MEDIA_ROOT; True when a file was found.
        """
        path = find_image(folder, username)
        if path is None:
            self.missing_images.append(f'{folder}/{username}')
            return False
        with path.open('rb') as fh:
            field.save(path.name, File(fh), save=False)
        return True

    def print_summary(self, password):
        counts = self.counts
        self.stdout.write(self.style.SUCCESS(
            f'angelegt: {counts["users"]} Accounts, {counts["offers"]} '
            f'Angebote, {counts["details"]} Details, {counts["orders"]} '
            f'Orders, {counts["reviews"]} Reviews '
            f'({counts["skipped"]} Accounts übersprungen)'))
        if self.missing_images:
            self.stdout.write(self.style.WARNING(
                'ohne Bild (Datei fehlt in initial_seed/images/): '
                + ', '.join(self.missing_images)))
        if counts['users']:
            self.stdout.write(
                f'Passwort für alle Seed-Accounts: {password}')
