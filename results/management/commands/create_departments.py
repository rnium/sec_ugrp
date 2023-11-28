from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandError
from results.models import Department



class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        data = {
            'cse': {
                'fullname': 'Computer Science Engineering',
                'dept_logo_name': "cse-logo.png"
            },
            'eee': {
                'fullname': 'Electrical and Electronic Engineering',
                'dept_logo_name': "eee-logo.png"
            },
            'ce': {
                'fullname': 'Civil Engineering',
                'dept_logo_name': "ce-logo.png"
            }
        }
        for name, props in data.items():
            dept_props = {'name': name, **props}
            Department.objects.create(**dept_props)
            
        self.stdout.write(self.style.SUCCESS(f"completed"))