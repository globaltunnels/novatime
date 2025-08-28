from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Test database connectivity'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully connected to database!')
                )
                self.stdout.write(
                    f'PostgreSQL version: {version[0]}'
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to connect to database: {e}')
            )