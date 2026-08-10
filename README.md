# Coderr Backend

REST API for the Coderr platform, built with Django and Django REST Framework.
Business users publish offers, customers order them and rate the provider afterwards.

## Requirements

- Python 3.13
- The frontend expects the API under `http://127.0.0.1:8000/api/`

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The database is a local SQLite file and is **not** part of the repository — `migrate`
creates it on first run.

### Dependencies

All packages are pinned in `requirements.txt`. After installing or upgrading something,
write the file back with UTF-8 encoding:

```powershell
pip freeze | Out-File -Encoding utf8 requirements.txt
```

A plain `>` redirect produces UTF-16 on Windows, which `pip install -r` cannot read.

## Before going public

`core/settings.py` still holds development defaults. Move them into environment
variables (`python-dotenv` is already installed) before deploying:

- `SECRET_KEY` — currently hard coded in the file
- `DEBUG` — must be `False`
- `ALLOWED_HOSTS` — must list the real domain

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
