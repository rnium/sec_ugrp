from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from results.utils import render_error

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect("account:user_login_get")
        if hasattr(request.user, 'adminaccount'):
            return view_func(request, *args, **kwargs)
        else:
            return render_error(request, "Forbidden", "You're not an admin")
    return wrapper

def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect("account:user_login_get")
        if hasattr(request.user, 'adminaccount') and (request.user.adminaccount.is_super_admin):
            return view_func(request, *args, **kwargs)
        else:
            return render_error(request, "Forbidden", "You don't have superadmin privileges")
    return wrapper
        
def superadmin_or_deptadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect("account:user_login_get")
        if hasattr(request.user, 'adminaccount') and (request.user.adminaccount.dept is not None or (request.user.adminaccount.is_super_admin)):
            return view_func(request, *args, **kwargs)
        else:
            return render_error(request, "Forbidden", "You don't have superadmin or dept. admin privileges")
    return wrapper


class DeptAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'adminaccount'):
            dept = self.get_dept()
            if request.user.adminaccount.is_super_admin or request.user.adminaccount.dept == dept:
                return super().dispatch(request, *args, **kwargs)
            else:
                return render_error(request, "Forbidden")
        else:
            return HttpResponseForbidden("Forbidden: You must be a staff to access this page.")