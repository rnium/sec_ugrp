from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout


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
