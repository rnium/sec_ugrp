from typing import Any, Optional
from django.core.management.base import BaseCommand, CommandError
from results.models import Department, Course, CourseResult, Session
from account.models import StudentAccount



class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        success_count = 0
        fail_count = 0
        for session in Session.objects.all():
            for student in session.studentaccount_set.all():
                failed_courseress = student.courseresult_set.filter(grade_point=0, is_drop_course=False)
                for carry_result in failed_courseress:
                    retakes = CourseResult.objects.filter(retake_of=carry_result, is_drop_course=True, grade_point__gt=0)
                    if (retakes.count() == 0):
                        possible_retake = CourseResult.objects.filter(course__code=carry_result.course.code, student=student).exclude(id=carry_result.id)
                        if (possible_retake.count()):
                            possible_retake = possible_retake[0]
                            possible_retake.retake_of = carry_result
                            possible_retake.save()
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS(f"{possible_retake.course}.retake_of = ({carry_result.course}"))
                            # return
                        else:
                            fail_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"completed: {success_count}"))
        self.stdout.write(self.style.ERROR(f"failed: {fail_count}"))