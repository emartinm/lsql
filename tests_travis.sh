#! /bin/bash

# Prints environment
# echo "Environment"
# env
# echo "-----------"

# Applies migrations, run tests and uploads reports to codecov
cd lsql

python manage.py migrate
python manage.py collectstatic

# Run tests and show a report with lines not covered in stdout
coverage erase
coverage run manage.py test
coverage report -m

# Generates XML report for codecov, failing if coverage is less than 100%
coverage xml --fail-under 100

# Submits coverage report, checking the checksum of the uploader
curl -s https://raw.githubusercontent.com/codecov/codecov-bash/master/SHA1SUM | grep codecov > SHA1SUM
curl -s https://codecov.io/bash > codecov
sha1sum -c SHA1SUM
if [ $? -eq 0 ]; then
    bash codecov
else
    echo "'codecov' uploader does not match expected checksum!"
    echo "*IGNORING codecov EXECUTION*"
    echo
fi
# Unsafe version that executes without checking
# bash <(curl -s https://codecov.io/bash)
