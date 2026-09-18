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
{ "username": "biz", "email": "biz@mail.de", "password": "…", "repeated_password": "…", "type": "business" }
{ "username": "cust", "email": "cust@mail.de", "password": "…", "repeated_password": "…", "type": "customer" }
```

Passwords go through Django's validators: at least 8 characters, not only digits,
not a common password and not too close to the username or the email.

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


## API

Authentication is token based. Send the token from registration or login as
`Authorization: Token <key>`.

| Method | Endpoint | Who |
|---|---|---|
| POST | `/api/registration/` | everyone |
| POST | `/api/login/` | everyone |
| GET, PATCH | `/api/profile/<user_id>/` | read: logged in, write: owner |
| GET | `/api/profiles/business/` | logged in |
| GET | `/api/profiles/customer/` | logged in |
| GET | `/api/offers/` | everyone |
| POST | `/api/offers/` | business users |
| GET, PATCH, DELETE | `/api/offers/<id>/` | read: logged in, write: creator |
| GET | `/api/offerdetails/<id>/` | logged in |
| GET | `/api/orders/` | logged in, own orders only |
| POST | `/api/orders/` | customers |
| PATCH | `/api/orders/<id>/` | the provider of that order |
| DELETE | `/api/orders/<id>/` | admins |
| GET | `/api/order-count/<business_user_id>/` | logged in |
| GET | `/api/completed-order-count/<business_user_id>/` | logged in |
| GET | `/api/reviews/` | logged in |
| POST | `/api/reviews/` | customers, once per business user |
| PATCH, DELETE | `/api/reviews/<id>/` | author |
| GET | `/api/base-info/` | everyone |

The url of a profile carries the **user** id, not the id of the profile row.

Query parameters:

- offers: `?creator_id=`, `?min_price=`, `?max_delivery_time=`, `?search=`, `?ordering=`, `?page_size=`
- reviews: `?business_user_id=`, `?reviewer_id=`, `?ordering=`

The offer list is paginated, so it answers with `count`, `next`, `previous` and `results`.
A page holds 20 offers, `?page_size=` raises that up to 50. All other lists return a
plain array.

### Rules

- An offer is created with exactly three details, one each of `basic`, `standard` and
  `premium`. A PATCH may send single details; they are matched by their `offer_type`.
- Offer images may be at most 5 MB.
- An order copies the conditions of the chosen offer detail, so a later price change
  leaves it untouched. The client only sends `offer_detail_id`.
- The status of an order is `in_progress`, `completed` or `cancelled`. It is the only
  field a PATCH may change; unknown keys are answered with a 400.
- Only business users can be reviewed, with a rating from 1 to 5. A PATCH may change
  `rating` and `description`, nothing else.
- An email address belongs to one account only, at registration and in the profile.
  It is stored lower cased.

### Rate limits

Every endpoint is throttled. Anonymous callers are counted per IP address, logged in
ones per user. Above the limit the API answers with `429 Too Many Requests` and a
`Retry-After` header.

| Scope | Limit |
|---|---|
| all requests, anonymous | 60 / minute |
| all requests, logged in | 240 / minute |
| registration | 5 / hour |
| login | 5 / minute |
| profile update | 30 / hour |
| offer create | 10 / hour |
| offer update and delete | 60 / hour |
| order create | 30 / hour |
| order update and delete | 60 / hour |
| review create | 10 / hour |
| review update and delete | 30 / hour |
| base info | 30 / minute |

The rates live in `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']` in `core/settings.py`, the
scopes in `<app>/api/throttles.py`.


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

Apprenticeship project for the Back-End program of the Developer Akademie. The task was
to implement a given API specification for the Coderr frontend, which is a separate
repository and consumes this API.

### What this project covers

Technologies: Python, Django, Django REST Framework, Django ORM with SQLite,
django-filter, django-cors-headers, DRF token authentication, Pillow, python-dotenv,
the Django test framework and Git.

Concepts:

- REST API design against a specification: HTTP methods, status codes, response shapes
- Token authentication with registration and login
- Role based access (business / customer) and object level permissions (owner, provider, staff)
- ModelSerializer and nested serializers with nested create and update
- Custom validation in serializers and protection against mass assignment
- Generic views and mixins, querysets restricted to the requesting user
- Query annotation and aggregation (Min, Avg, Count)
- Filtering, searching, ordering and pagination
- Data modelling with foreign keys, choices, unique constraints and migrations
- Password hashing and validation, configuration through environment variables, CORS
- Rate limiting with throttle scopes per endpoint
- Media uploads
- API integration tests for the happy path and the 400/401/403/404 cases
- Conventional Commits
