#! /bin/bash

# Applies migrations, run tests and uploads reports to codecov
cd lsql

python manage.py migrate
python manage.py collectstatic

# Run tests and show a report with lines not covered in stdout
coverage erase
coverage run manage.py test || exit 255  # Exits promptly if fails
coverage report -m

# Generates XML report for codecov, failing if coverage is less than 100%
coverage xml --fail-under 100 || exit 255  # Exits promptly if fails

# Upload coverage using bash uploader (obsolescent)
# curl -fLso codecov https://codecov.io/bash
# VERSION=$(grep -o 'VERSION=\"[0-9\.]*\"' codecov | cut -d'"' -f2);
# wget "https://raw.githubusercontent.com/codecov/codecov-bash/${VERSION}/SHA256SUM"
# shasum -a 256 -c SHA256SUM --ignore-missing
# SUM_OK=$?

# if [ $SUM_OK -eq 0 ]; then
#   bash codecov
# else
#    echo "'codecov' uploader does not match expected checksum!"
#    echo "*IGNORING codecov EXECUTION*"
#    echo
# fi

# New uploader, currently beta (does not work with lsql yet)
# Submits coverage report to Codecov, checking first the checksum of the uploader
# curl https://keybase.io/codecovsecurity/pgp_keys.asc | gpg --import
# curl -Os https://uploader.codecov.io/latest/codecov-linux
# curl -Os https://uploader.codecov.io/latest/codecov-linux.SHA256SUM
# curl -Os https://uploader.codecov.io/latest/codecov-linux.SHA256SUM.sig

# gpg --verify codecov-linux.SHA256SUM.sig codecov-linux.SHA256SUM
# GPG_OK=$?
# shasum -a 256 -c codecov-linux.SHA256SUM
# SUM_OK=$?

# if [ $GPG_OK -eq 0 ] && [ $SUM_OK -eq 0 ]; then
#   chmod +x codecov-linux
#   ./codecov-linux -v
# else
#    echo "'codecov' uploader does not match expected checksum!"
#    echo "*IGNORING codecov EXECUTION*"
#    echo
# fi
