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

## Before going public

- `DEBUG=False` in the `.env` of the server
- `ALLOWED_HOSTS` set to the real domain
- a **fresh** `SECRET_KEY`, never the one from a development machine
- `python manage.py check --deploy` for the remaining warnings

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

Every app follows the same structure:

```
<app>/models.py       the models
<app>/api/            serializers, views, urls, permissions, filters
<app>/tests/          tests as a package, never tests.py — it collides with the folder
```

## API

| Method | Endpoint | Who |
|---|---|---|
| POST | `/api/registration/`, `/api/login/` | everyone |
| GET, PATCH | `/api/profile/<pk>/` | read: logged in, write: owner |
| GET | `/api/profile/business/`, `/api/profile/customer/` | logged in |
| GET | `/api/offers/` | everyone |
| POST | `/api/offers/` | business users |
| GET, PATCH, DELETE | `/api/offers/<id>/` | write: creator |
| GET | `/api/offerdetails/<id>/` | logged in |
| GET | `/api/orders/` | own orders only |
| POST | `/api/orders/` | customers |
| PATCH | `/api/orders/<id>/` | business users |
| DELETE | `/api/orders/<id>/` | admins |
| GET | `/api/order-count/<business_user_id>/` | logged in |
| GET | `/api/completed-order-count/<business_user_id>/` | logged in |
| GET | `/api/reviews/` | logged in |
| POST | `/api/reviews/` | customers, once per business user |
| PATCH, DELETE | `/api/reviews/<id>/` | author |
| GET | `/api/base-info/` | everyone |

Authentication is token based. Send the token from registration or login as
`Authorization: Token <key>`.

Query parameters worth knowing:

- offers: `?creator_id=`, `?min_price=`, `?max_delivery_time=`, `?search=`, `?ordering=`, `?page_size=`
- reviews: `?business_user_id=`, `?reviewer_id=`, `?ordering=`

The offer list is paginated (20 per page, `?page_size=` up to 50), so its answer is an
object with `count`, `next`, `previous` and `results`. All other lists return a plain array.

### Status codes

| Code | When |
|---|---|
| 400 | payload fails validation, or carries a field the endpoint does not accept |
| 401 | no or unknown token |
| 403 | authenticated, but the wrong role or not the owner of the object |
| 404 | the id does not exist, or the object is outside the caller's queryset |
| 405 | the endpoint does not offer this method, e.g. PUT |

## Tests

```powershell
python manage.py test                                   # everything
python manage.py test orders_app                        # one app
python manage.py test orders_app.tests.test_orders      # one file
python manage.py test orders_app.tests.test_orders.OrderTests.test_customer_can_order_an_offer_detail
```

Add `-v 2` for single test names and `--failfast` to stop at the first error.

## Conventions

- **PEP 8** for formatting; imports grouped as third party, own apps, relative.
- **Docstrings** on every class and on methods whose purpose is not obvious. Inline
  comments explain *why*, not *what*.
- **Commits** follow Conventional Commits: `type(scope): subject`, imperative and lower
  case, always with a short body.
- **Where logic belongs:** which objects are visible → `get_queryset()`; who may act →
  permission classes; which fields go in and out → serializer; how a value is stored →
  `create()` / `perform_create()`. Values the server already knows, such as the logged in
  user, are never taken from the payload.

## Debugging

Run the debugger through `manage.py`, never on a single file — otherwise
`DJANGO_SETTINGS_MODULE` is missing.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `KeyError: 'SECRET_KEY'` on start | no `.env`, or the key is empty |
| Works in Postman, blocked in the browser | origin missing in `CORS_ALLOWED_ORIGINS`, or written with a trailing slash |
| `DisallowedHost` | the host is missing in `ALLOWED_HOSTS` |
| `pip install -r` cannot read the file | `requirements.txt` was written as UTF-16, see above |
| A filter is ignored instead of failing | unknown query parameters are dropped silently — check the spelling |
| `Enter a number` on a filter | the value is not numeric, e.g. a trailing `/` behind the number |
| Tests are not found | the app has both a `tests.py` and a `tests/` folder |

## About

Apprenticeship project for the Developer Akademie. The frontend is a separate
repository and consumes this API.
