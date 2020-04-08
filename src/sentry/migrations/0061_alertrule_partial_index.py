# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-04-08 01:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    # This flag is used to mark that a migration shouldn't be automatically run in
    # production. We set this to True for operations that we think are risky and want
    # someone from ops to run manually and monitor.
    # General advice is that if in doubt, mark your migration as `is_dangerous`.
    # Some things you should always mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that
    #   they can be monitored. Since data migrations will now hold a transaction open
    #   this is even more important.
    # - Adding columns to highly active tables, even ones that are NULL.
    is_dangerous = False

    # This flag is used to decide whether to run this migration in a transaction or not.
    # By default we prefer to run in a transaction, but for migrations where you want
    # to `CREATE INDEX CONCURRENTLY` this needs to be set to False. Typically you'll
    # want to create an index concurrently when adding one to an existing table.
    atomic = True


    dependencies = [
        ('sentry', '0060_add_file_eventattachment_index'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("""
                    ALTER TABLE sentry_alertrule DROP CONSTRAINT IF EXISTS sentry_alertrule_organization_id_name_12c48b37_uniq;
                    DROP INDEX IF EXISTS sentry_alertrule_organization_id_name_12c48b37_uniq;
                    CREATE UNIQUE INDEX CONCURRENTLY sentry_alertrule_status_active
                    ON sentry_alertrule USING btree (organization_id, name, status)
                    WHERE status = 0;
                    """,
                    reverse_sql="""
                    DROP INDEX IF EXISTS sentry_alertrule_status_active;
                    CREATE UNIQUE INDEX CONCURRENTLY sentry_alertrule_organization_id_name_12c48b37_uniq
                    ON sentry_alertrule USING btree (organization_id, name);
                    """,
                )
            ],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="alertrule", unique_together=set([("organization", "name", "status")])
                )
            ],
        ),
    ]
