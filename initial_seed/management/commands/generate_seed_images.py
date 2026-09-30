"""Create the pictures for initial_seed/images/ with OpenAI's image model.

Runs on the developer machine only; the finished files are committed, so
the server never needs the API key.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

SEED_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = SEED_DIR / 'data.json'
IMAGE_DIR = SEED_DIR / 'images'
API_URL = 'https://api.openai.com/v1/images/generations'
DEFAULT_MODEL = 'gpt-image-2'
ATTEMPTS = 3
TIMEOUT_SECONDS = 300


def generate_image(prompt, target_path, api_key, model, quality):
    """One request to the images endpoint; the JPEG is written to target_path.

    A slow answer is retried a few times: a single image can take well
    over a minute and the connection occasionally drops mid-response.
    """
    body = json.dumps({
        'model': model,
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'quality': quality,
        'output_format': 'jpeg',
    }).encode('utf-8')
    request = urllib.request.Request(
        API_URL,
        data=body,
        method='POST',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(
                    request, timeout=TIMEOUT_SECONDS) as response:
                payload = json.load(response)
            break
        except urllib.error.HTTPError as err:
            detail = err.read().decode('utf-8', errors='replace')
            raise CommandError(f'OpenAI answered {err.code}: {detail}')
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            if attempt == ATTEMPTS:
                raise CommandError(
                    f'Could not reach OpenAI after {ATTEMPTS} attempts: {err}')
            print(f'    Versuch {attempt} fehlgeschlagen ({err}), '
                  'neuer Versuch ...')

    try:
        image_bytes = base64.b64decode(payload['data'][0]['b64_json'])
    except (KeyError, IndexError, TypeError, ValueError):
        raise CommandError(f'Unexpected answer from OpenAI: {payload}')
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(image_bytes)


class Command(BaseCommand):
    help = 'Generate the seed profile and offer pictures with gpt-image-2.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only', choices=['profiles', 'offers'],
            help='generate only this folder')
        parser.add_argument(
            '--force', action='store_true',
            help='overwrite pictures that already exist')
        parser.add_argument(
            '--quality', choices=['low', 'medium', 'high'], default='medium',
            help='image quality sent to OpenAI (default: medium)')

    def handle(self, *args, **options):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise CommandError(
                'OPENAI_API_KEY fehlt. Trage den Key in die .env ein, '
                'z. B. OPENAI_API_KEY=sk-...')
        model = os.getenv('OPENAI_IMAGE_MODEL', DEFAULT_MODEL)

        with DATA_FILE.open(encoding='utf-8') as fh:
            data = json.load(fh)

        jobs = []
        if options['only'] != 'offers':
            for entry in data['businesses'] + data['customers']:
                jobs.append(('profiles', entry['username'],
                             entry.get('image_prompt')
                             or self.profile_prompt(entry)))
        if options['only'] != 'profiles':
            for entry in data['businesses']:
                offer = entry['offer']
                jobs.append(('offers', entry['username'],
                             offer.get('image_prompt')
                             or self.offer_prompt(offer)))

        done = skipped = 0
        for index, (folder, username, prompt) in enumerate(jobs, start=1):
            target = IMAGE_DIR / folder / f'{username}.jpg'
            label = f'[{index}/{len(jobs)}] {folder}/{target.name}'
            if target.exists() and not options['force']:
                self.stdout.write(f'{label} übersprungen, existiert')
                skipped += 1
                continue
            self.stdout.write(f'{label} wird erzeugt ...')
            generate_image(
                prompt, target, api_key, model, options['quality'])
            done += 1

        self.stdout.write(self.style.SUCCESS(
            f'{done} Bilder erzeugt, {skipped} übersprungen '
            f'(Modell {model}, Qualität {options["quality"]})'))

    @staticmethod
    def profile_prompt(entry):
        name = f'{entry.get("first_name", "")} {entry.get("last_name", "")}'
        return (
            f'Professional portrait photo of {name.strip()}, '
            f'{entry.get("description", "")}, neutral background, '
            'soft light, photorealistic, square crop')

    @staticmethod
    def offer_prompt(offer):
        return (
            f'Flat modern vector illustration representing: {offer["title"]}. '
            'Muted colors, no text, clean composition')
