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


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        # 1. Assign a placeholder email to any rows that currently have NULL email
        #    (only relevant if dev DB already has data).
        migrations.RunSQL(
            sql="""
                UPDATE users
                SET email = 'legacy_' || gen_random_uuid()::text || '@placeholder.invalid'
                WHERE email IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
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
