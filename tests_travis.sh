#! /bin/bash

# Applies migrations, run tests and uploads reports to codecov

cd lsql

python manage.py migrate
python manage.py collectstatic

# Run tests and show a report with lines not covered in stdout
coverage erase
coverage run manage.py test
coverage report -m

# Generates XML report for codecov,failing if coverage is less than 100%
coverage xml --fail-under 100
bash <(curl -s https://codecov.io/bash) 
