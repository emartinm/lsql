#! /bin/bash

# Applies migrations, run tests and uploads reports to codecov
cd lsql

python manage.py migrate
python manage.py collectstatic

# Run tests and show a report with lines not covered in stdout
coverage erase
coverage run manage.py test judge.tests.test_tags || exit -1  # Exits promptly if fails
coverage report -m

# Generates XML report for codecov, failing if coverage is less than 100%
coverage xml --fail-under 10 || exit -2  # Exits promptly if fails

# Submits coverage report to Codecov, checking first the checksum of the uploader
curl https://keybase.io/codecovsecurity/pgp_keys.asc | gpg --import
curl -Os https://uploader.codecov.io/latest/codecov-linux
curl -Os https://uploader.codecov.io/latest/codecov-linux.SHA256SUM
curl -Os https://uploader.codecov.io/latest/codecov-linux.SHA256SUM.sig

gpg --verify codecov-linux.SHA256SUM.sig codecov-linux.SHA256SUM
GPG_OK=$?
shasum -a 256 -c codecov-linux.SHA256SUM
SUM_OK=$?

if [ $GPG_OK -eq 0 ] && [ $SUM_OK -eq 0 ]; then
  chmod +x codecov-linux
  ./codecov-linux
else
    echo "'codecov' uploader does not match expected checksum!"
    echo "*IGNORING codecov EXECUTION*"
    echo
fi
