from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, FileResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializer import (SessionSerializer, SemesterSerializer,
                         CourseSerializer, CourseResultSerializer, StudentStatsSerializer)
from .permission import IsCampusAdmin
from results.models import (Department, Session, Semester, ExamCommittee)
from account.models import StudentAccount, AdminAccount
from results.tasks import restore_dept_data_task, restore_session_data_task
from results.decorators_and_mixins import superadmin_required, superadmin_or_deptadmin_required
from results.api.permission import IsSuperAdmin
from django.conf import settings

disallowed_committee_admin_types = ['sust', 'academic']


@api_view()
def committee_radios(request): # Searching for an admin for the semester committee selection
    admin_name = request.GET.get('name')
    # admins_qs = AdminAccount.objects
    admins_qs = AdminAccount.objects.all().exclude(type__in=disallowed_committee_admin_types)
    admins_qs_firstname = admins_qs.filter(user__first_name__startswith=admin_name)
    admins_qs_email = admins_qs.filter(user__email__startswith=admin_name)
    admins_qs_final = admins_qs_firstname | admins_qs_email
    html_content = render_to_string('results/components/admin_radios.html', context={'admin_qs': admins_qs_final[:5]})
    return Response(data={'html': html_content})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def add_committee_member(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    committee, created = ExamCommittee.objects.get_or_create(semester=semester)
    user = get_object_or_404(AdminAccount, id=request.data.get('user_pk'))
    member_type = request.data.get('member_type')
    if member_type == 'chair':
        committee.chairman = user
    elif member_type == 'member':
        committee.members.add(user)
    elif member_type == 'tabulator':
        committee.tabulators.add(user)
    else:
        return Response(data={'detail': "Undefined member type"}, status=status.HTTP_400_BAD_REQUEST)
    committee.save()
    html_content = render_to_string('results/components/committee_members.html', context={'semester': semester, 'request': request})
    return Response(data={'info': 'updated', 'html': html_content})

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def remove_committee_member(request, semester_pk, admin_pk, member_type):
    semester = get_object_or_404(Semester, pk=semester_pk)
    committee, created = ExamCommittee.objects.get_or_create(semester=semester)
    admin = get_object_or_404(AdminAccount, id=admin_pk)
    if member_type == 'chair' and committee.chairman == admin:
        committee.chairman = None
    elif member_type == 'c-member' and admin in committee.members.all():
        committee.members.remove(admin)
    elif member_type == 'tabulator' and admin in committee.tabulators.all():
        committee.tabulators.remove(admin)
        print('tabulator go', flush=1)
    else:
        Response(data={"detail": "Specified member type mismatch for the user"})
    committee.save()
    html_content = render_to_string('results/components/committee_members.html', context={'semester': semester, 'request': request})
    return Response(data={'info': 'Member removed', 'html': html_content})