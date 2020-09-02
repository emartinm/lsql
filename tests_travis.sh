#! /bin/bash

cd lsql

python manage.py migrate
python manage.py collectstatic

coverage erase
coverage run manage.py test
coverage report -m
