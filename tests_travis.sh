#! /bin/bash

cd lsql

coverage erase
coverage run manage.py test
coverage report -m
