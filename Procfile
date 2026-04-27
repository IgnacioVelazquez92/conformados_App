web: python manage.py migrate && python manage.py collectstatic --noinput && python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
