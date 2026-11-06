"""Creation of students from the class list CSV exported by the UCM.

    python manage.py create_users estudiantes.csv "Grupo A"          # dry run: only shows what it would do
    python manage.py create_users estudiantes.csv "Grupo A" --save   # creates the users

The CSV has (at least) the columns NOMBRE COMPLETO ("Surnames, Name"), DOCUMENTO and
CORREO. The username is the part of the e-mail before @ucm.es and the initial password
is the identity document. Existing users are only added to the group.
"""

import csv

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

UCM_DOMAIN = "ucm.es"


class Command(BaseCommand):
    help = "Creates students from the UCM class list CSV and adds them to a group."

    def add_arguments(self, parser):
        parser.add_argument("csv_file")
        parser.add_argument("group")
        parser.add_argument("--save", action="store_true", help="Store the changes (by default it is a dry run).")

    def handle(self, csv_file, group, save, **options):
        try:
            with open(csv_file, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
        except OSError as e:
            raise CommandError(f"Cannot read {csv_file}: {e}") from e
        missing = {"NOMBRE COMPLETO", "DOCUMENTO", "CORREO"} - set(rows[0] if rows else {})
        if missing:
            raise CommandError(f"Missing columns in the CSV: {', '.join(sorted(missing))}")
        if not save:
            self.stdout.write("DRY RUN: nothing will be stored (use --save)")
        with transaction.atomic():
            self._create(rows, group)
            if not save:
                transaction.set_rollback(True)

    def _create(self, rows, group_name):
        users = get_user_model().objects
        group, created = Group.objects.get_or_create(name=group_name)
        self.stdout.write(f"{'Created' if created else 'Existing'} group {group_name}")
        for line, row in enumerate(rows, start=2):
            email = row["CORREO"].strip().lower()
            username, _, domain = email.partition("@")
            if not username or domain != UCM_DOMAIN:
                raise CommandError(f"Line {line}: invalid UCM e-mail '{email}'")
            surnames, _, name = row["NOMBRE COMPLETO"].partition(",")
            user = users.filter(username=username).first()
            if user is None:
                user = users.create_user(
                    username=username,
                    email=email,
                    password=row["DOCUMENTO"].strip(),
                    first_name=name.strip(),
                    last_name=surnames.strip(),
                )
                self.stdout.write(f"Created user {username}")
            else:
                self.stdout.write(f"Existing user {username}")
            user.groups.add(group)
