from typing import Any, Dict
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.generics import CreateAPIView
from . import utils
from .models import StudentAccount
from .serializer import StudentAccountSerializer

    

def login_page(request):
    if request.user.is_authenticated:
            return redirect("results:dashboard")
    else:
        return render(request=request, template_name='account/login_page.html')
    
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return redirect("account:user_login_get")
    

class StudentProfileView(LoginRequiredMixin, DetailView):
    template_name = "account/view_student_profile.html"
    
    def get_object(self):
        student = get_object_or_404(
            StudentAccount, 
            registration = self.kwargs.get("registration", "")
        )
        return student
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['student'] = context['studentaccount'] # Alias
        context['gradesheet_years'] = context['student'].gradesheet_years
        context['request'] = self.request
        return context




# REST API SECTION BELOW

class UnauthorizedException(APIException):
    status_code = 403
    default_detail = 'Unauthorized'
    
class BadrequestException(APIException):
    status_code = 400
    default_detail = 'Bad Request'
    
@api_view(['POST'])
def api_login(request):
    user = authenticate(username=request.data['email'], password=request.data['password'])
    if user:
        login(request, user)
        success_url = reverse("results:dashboard")
        return Response({'status':'logged in', 'succes_url': success_url}, status=HTTP_200_OK)
    else:
        return Response({'status':'Invalid Credentials'}, status=HTTP_401_UNAUTHORIZED)


class StudentAccountCreate(CreateAPIView):
    # To be used by admin user
    serializer_class = StudentAccountSerializer
    permission_classes = [IsAuthenticated]
    queryset = StudentAccount.objects.all()
    
    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'adminaccount'):
            raise UnauthorizedException("User not authorized")
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))


@csrf_exempt
def set_student_avatar(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse(data={'details': 'Unauthorized'}, status=403)
        # get student account
        try:
            registration = request.POST.get('registration')
            print(registration)
            account = StudentAccount.objects.get(registration=registration)
        except StudentAccount.DoesNotExist:
            return JsonResponse(data={'details': "Account not found"}, status=400)
        # check if user has permission
        if not hasattr(request.user, 'adminaccount'):
            if not (hasattr(request.user, 'studentaccount') and (request.user.studentaccount == account)):
                return JsonResponse(data={'details': 'Unauthorized'}, status=403)
        # Saving file
        if len(request.FILES) > 0:
            try:
                image_file = request.FILES.get('dp')
                compressed_image = utils.compress_image(image_file)
            except ValidationError as e:
                return JsonResponse(data={'details': e.message}, status=400)
            if account.profile_picture is not None:
                account.profile_picture.delete(save=True)
            try:
                account.profile_picture = compressed_image
                account.save()
            except Exception as e:
                return JsonResponse(data={'details': 'Cannot save image'}, status=400)

            return JsonResponse({'status':'profile picture set'})
        else:
            return JsonResponse(data={'details': 'No image uploaded'}, status=400)
    else:
        return JsonResponse(data={'details': 'Method not allowed'}, status=400)