#! /bin/bash

set -e # The script fails if any command fails

cd lsql

coverage erase
coverage run manage.py test
coverage report -m
