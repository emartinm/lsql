"""
Unit tests for the management commands (judge/management/commands)
"""

import io
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

HEADER = "FOTOGRAFÍA,NOMBRE COMPLETO,DOCUMENTO,ASIGNATURA,CORREO\n"
ROWS = '"","García Pérez, Ana",12345678A,BD,anagar@ucm.es\n"","López, Bea",87654321B,BD,BEALOP@UCM.ES\n'


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CreateUsersTest(TestCase):
    """Tests for create_users (students from the UCM class list CSV)"""

    def run_command(self, content, *args):
        """Writes content in a temporary CSV file and runs create_users on it"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "estudiantes.csv"
            path.write_text(content, encoding="utf-8-sig")
            out = io.StringIO()
            call_command("create_users", str(path), "Grupo A", *args, stdout=out)
            return out.getvalue()

    def test_dry_run_stores_nothing(self):
        """Without --save nothing is stored"""
        output = self.run_command(HEADER + ROWS)
        self.assertIn("DRY RUN", output)
        self.assertIn("Created user anagar", output)
        self.assertFalse(get_user_model().objects.exists())
        self.assertFalse(Group.objects.exists())

    def test_save(self):
        """With --save the users and the group are created; existing users only join the group"""
        self.run_command(HEADER + ROWS, "--save")
        ana = get_user_model().objects.get(username="anagar")
        self.assertEqual((ana.first_name, ana.last_name, ana.email), ("Ana", "García Pérez", "anagar@ucm.es"))
        self.assertTrue(ana.check_password("12345678A"))
        self.assertEqual(list(ana.groups.values_list("name", flat=True)), ["Grupo A"])
        self.assertTrue(get_user_model().objects.filter(username="bealop").exists())
        # Second time: existing users keep their password and are added to the group
        ana.set_password("new-password")
        ana.save()
        output = self.run_command(HEADER + ROWS, "--save")
        self.assertIn("Existing user anagar", output)
        self.assertIn("Existing group", output)
        ana.refresh_from_db()
        self.assertTrue(ana.check_password("new-password"))

    def test_errors(self):
        """Non-UCM e-mails, missing columns and unreadable files stop the import without changes"""
        with self.assertRaisesMessage(CommandError, "invalid UCM e-mail"):
            self.run_command(HEADER + '"","X, Y",1,BD,someone@gmail.com\n', "--save")
        with self.assertRaisesMessage(CommandError, "Missing columns"):
            self.run_command("NOMBRE,CORREO\nx,y@ucm.es\n")
        with self.assertRaisesMessage(CommandError, "Cannot read"):
            call_command("create_users", "/nonexistent.csv", "Grupo A")
        self.assertFalse(get_user_model().objects.exists())
