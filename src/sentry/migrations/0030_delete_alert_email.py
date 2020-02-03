# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-23 19:07
from __future__ import unicode_literals

from django.db import migrations

from sentry.utils.query import RangeQuerySetWrapper


def delete_alert_email_user_options(apps, schema_editor):
    """
    Processes user reports that are missing event data, and adds the appropriate data
    if the event exists in Clickhouse.
    """
    UserOption = apps.get_model("sentry", "UserOption")

    UserOption.objects.filter(key="alert_email").delete()


class Migration(migrations.Migration):
    # This flag is used to mark that a migration shouldn't be automatically run in
    # production. We set this to True for operations that we think are risky and want
    # someone from ops to run manually and monitor.
    # General advice is that if in doubt, mark your migration as `is_dangerous`.
    # Some things you should always mark as dangerous:
    # - Adding indexes to large tables. These indexes should be created concurrently,
    #   unfortunately we can't run migrations outside of a transaction until Django
    #   1.10. So until then these should be run manually.
    # - Large data migrations. Typically we want these to be run manually by ops so that
    #   they can be monitored. Since data migrations will now hold a transaction open
    #   this is even more important.
    # - Adding columns to highly active tables, even ones that are NULL.
    is_dangerous = True

    dependencies = [
        ("sentry", "0028_user_reports"),
    ]

    operations = [
        migrations.RunPython(delete_alert_email_user_options, migrations.RunPython.noop),
    ]
