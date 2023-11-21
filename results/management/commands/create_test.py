from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from results.models import Department



class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        # Export fixtures from the main database
        call_command('dumpdata', '--exclude', 'auth.permission', '--exclude', 'contenttypes', '--exclude', 'admin.LogEntry', '--output', 'fixtures.json')
        # Load fixtures into the test database
        call_command('test')