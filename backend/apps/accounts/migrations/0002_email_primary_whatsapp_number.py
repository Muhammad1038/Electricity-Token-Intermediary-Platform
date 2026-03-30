"""
Migration: Switch primary auth identifier from phone_number to email.

Changes:
  - Remove phone_number field
  - Make email required (non-null, non-blank)
  - Add whatsapp_number (optional, nullable)

For existing rows that have a NULL email, a placeholder is assigned before
removing the NOT NULL constraint — safe for dev/test environments.
"""
from django.db import migrations, models


def set_placeholder_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    import uuid
    for user in User.objects.filter(email__isnull=True):
        user.email = f"legacy_{uuid.uuid4().hex}@placeholder.invalid"
        user.save(update_fields=["email"])

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        # 1. Assign a placeholder email to any rows that currently have NULL email
        #    (Works on both Postgres and SQLite)
        migrations.RunPython(
            code=set_placeholder_emails,
            reverse_code=migrations.RunPython.noop,
        ),

        # 2. Make email non-nullable + required
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                db_index=True,
                max_length=254,
                unique=True,
            ),
        ),

        # 3. Add whatsapp_number (optional)
        migrations.AddField(
            model_name="user",
            name="whatsapp_number",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Nigerian WhatsApp number e.g. 08140628953 or +2348140628953",
                max_length=20,
                null=True,
                unique=True,
            ),
        ),

        # 4. Remove phone_number
        migrations.RemoveField(
            model_name="user",
            name="phone_number",
        ),
    ]
