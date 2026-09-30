FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# requirements first so the pip layer is cached
# until requirements.txt itself changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# gunicorn needs the port only inside the docker network;
# what reaches the host is decided in docker-compose.yml
EXPOSE 8000

# migrate and collectstatic run on every start so a new image
# is always in sync with its database and static files
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile -"]
