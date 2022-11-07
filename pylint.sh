#! /bin/bash

cd lsql 

# Workaround for django-pylint issue with  pylint >= 2.15
# https://github.com/PyCQA/pylint-django/issues/370
# https://github.com/PyCQA/pylint-django/issues/325
export PYTHONPATH=$PWD

pylint --ignore=apps.py,migrations judge/
