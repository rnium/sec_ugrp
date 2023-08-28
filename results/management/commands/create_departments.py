from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandError
from results.models import Department



class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        data = {
            'cse': {
                'fullname': 'Computer Science Engineering',
                'dept_logo': "departments/logo/seccse.png"
            },
            'eee': {
                'fullname': 'Electrical and Electronic Engineering',
                'dept_logo': "departments/logo/seceee.png"
            },
            'ce': {
                'fullname': 'Civil Engineering',
                'dept_logo': "departments/logo/seccivil.png"
            }
        }
        for name, props in data.items():
            dept_props = {'name': name, **props}
            Department.objects.create(**dept_props)
            
        self.stdout.write(self.style.SUCCESS(f"completed"))