from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from results.models import Department, Session, SemesterEnroll, CourseResult



class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        fourth_batch = Session.objects.filter(dept__name="eee", from_year=2018).first()
        if not fourth_batch:
            self.stdout.write(self.style.ERROR(f"fourth batch not found"))
        for semester in fourth_batch.semester_set.all():
            enrolls = semester.semesterenroll_set.all()
            course_res_count = CourseResult.objects.filter(course__semester=semester).count()
            update_count = 0
            for e in enrolls:
                for course in e.courses.all():
                    course_res = course.courseresult_set.filter(student=e.student).first()
                    if course_res:
                        course_res.save()
                        update_count += 1
            self.stdout.write(self.style.SUCCESS(f"{semester} --> Updated {update_count} / {course_res_count} course results"))
                        
        # Export fixtures from the main database
        self.stdout.write(self.style.WARNING(f"Dumping to fixtures"))
        call_command('dumpdata', '--exclude', 'auth.permission', '--exclude', 'contenttypes', '--exclude', 'admin.LogEntry', '--output', 'fixtures.json')
        self.stdout.write(self.style.SUCCESS(f"completed"))