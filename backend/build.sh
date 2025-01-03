# install Dependencies
poetry install

# run Migrations
python manage.py migrate

python manage.py collectstatic
