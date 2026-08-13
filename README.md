# Coderr Backend

REST API for the Coderr platform, built with Django and Django REST Framework.
Business users publish offers, customers order them and rate the provider afterwards.

## Stack

| | |
|---|---|
| Python | 3.13 |
| Django | 6.0 |
| Django REST Framework | 3.17, token authentication |
| django-filter | query parameter filtering |
| django-cors-headers | browser access from the frontend |
| Database | SQLite (development) |

The frontend expects the API under `http://127.0.0.1:8000/api/`.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env      # then fill in SECRET_KEY, see below

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The database is a local SQLite file and is **not** part of the repository — `migrate`
creates it on first run, empty.

### First data

The API distinguishes two roles, and most endpoints need one of them. Register one
account of each type over the API itself, that also creates the matching profile:

```
POST /api/registration/
{ "username": "biz", "email": "biz@mail.de", "password": "…", "repeated_password": "…", "type": "business_user" }
{ "username": "cust", "email": "cust@mail.de", "password": "…", "repeated_password": "…", "type": "customer" }
```

The response contains the token for the `Authorization` header. A superuser created with
`createsuperuser` has **no** profile — it can reach the admin and delete orders, but not
create offers or reviews.

### Media files

Offer images land in `media/` and are served by the development server only. The folder
is gitignored; in production a web server delivers it.

### Configuration

Settings that differ per machine live in `.env`, which is gitignored. `.env.example`
lists the expected keys:

| Key | Meaning |
|---|---|
| `SECRET_KEY` | Django's signing key. No default — a missing value stops the server. |
| `DEBUG` | `True` while developing, `False` everywhere else. |
| `ALLOWED_HOSTS` | Comma separated list of domains the app answers for. |
| `CORS_ALLOWED_ORIGINS` | Where the frontend runs, with scheme and port. |

Generate a key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The key signs sessions, CSRF tokens and password reset links. It never reaches the
frontend and must not be committed — the per user API tokens are a separate thing.

`CORS_ALLOWED_ORIGINS` decides which pages a browser lets talk to this API. The origin
must match exactly: `http://127.0.0.1:5500` and `http://localhost:5500` count as two
different ones, and a trailing slash breaks the match. If a request works in Postman but
not in the browser, this is the first place to look.

### Dependencies

All packages are pinned in `requirements.txt`. After installing or upgrading something,
write the file back with UTF-8 encoding:

```powershell
pip freeze | Out-File -Encoding utf8 requirements.txt
```

A plain `>` redirect produces UTF-16 on Windows, which `pip install -r` cannot read.


## Project layout

```
core/                 settings, root urls
auth_app/             registration, login, UserProfile model
profile_app/          profile detail and the two profile lists
offers_app/           offers with their three packages
orders_app/           orders and the order counters
reviews_app/          ratings of business users
base_info_app/        platform statistics for the landing page
```


## Tests

```powershell
python manage.py test                                   # everything
python manage.py test orders_app                        # one app
python manage.py test orders_app.tests.test_orders      # one file
python manage.py test orders_app.tests.test_orders.OrderTests.test_customer_can_order_an_offer_detail
```

Add `-v 2` for single test names and `--failfast` to stop at the first error.


## Debugging

Run the debugger through `manage.py`, never on a single file — otherwise
`DJANGO_SETTINGS_MODULE` is missing.


## About

Apprenticeship project for the Developer Akademie. The frontend is a separate
repository and consumes this API.
