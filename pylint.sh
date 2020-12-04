#! /bin/bash

cd lsql 

pylint --ignore=apps.py,migrations judge/
