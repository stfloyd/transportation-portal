#!/bin/bash

if [ "$DB_NAME" = "transportation" ]
then
  echo "Waiting for PostgreSQL:transportation..."

  while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
  done

  echo "PostgreSQL:transportation started."
fi

PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 | psql -h $DB_HOST -U $DB_USER -c "CREATE DATABASE $DB_NAME"


python manage.py migrate
python manage.py loaddata initial
python manage.py createsuperuser --no-input
python manage.py collectstatic --no-input --clear

exec "$@"
