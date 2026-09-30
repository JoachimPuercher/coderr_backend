# initial_seed

Demo data for the acceptance review. Everything lives in this folder; the
only line outside it is `'initial_seed'` in `INSTALLED_APPS`. Delete the
folder and that line to remove it again.

- `data.json` – 15 business accounts (each with one offer and its basic,
  standard and premium package), 10 customer accounts, orders and reviews.
  All names, addresses and texts are fictional. Each entry carries an
  `image_prompt` used by the picture generator.
- `images/profiles/<username>.jpg` and `images/offers/<username>.jpg` –
  the pictures, see `images/README.md`.
- `management/commands/generate_seed_images.py` – creates the pictures with
  OpenAI's image model. Runs locally only.
- `management/commands/seed_demo.py` – writes the data and pictures into the
  database. Safe to run twice: existing usernames are skipped.

## Pictures (local, once)

Put the key into `.env` (it is ignored by git and docker):

```
OPENAI_API_KEY=sk-...
OPENAI_IMAGE_MODEL=gpt-image-2   # optional, this is the default
```

Then:

```
python manage.py generate_seed_images              # all missing pictures
python manage.py generate_seed_images --only offers
python manage.py generate_seed_images --force --quality low   # cheaper, coarser
```

Existing files are skipped, so a rerun only fills gaps. Commit the pictures.

## Seeding

```
python manage.py seed_demo                              # local
docker compose exec web python manage.py seed_demo      # on the server
```

The command prints what it created, which pictures were missing and the
shared password of all seed accounts. Pictures are stored under the active
`MEDIA_ROOT` (`/app/data/media` in docker), so the web server has to serve
`/media/` from there.
