from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandError
from results.models import Course



class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        for course in Course.objects.all():
            course.save()
        self.stdout.write(self.style.SUCCESS(f"completed"))