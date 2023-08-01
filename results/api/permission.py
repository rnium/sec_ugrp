from rest_framework.permissions import BasePermission

class IsCampusAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.adminaccount.is_super_admin:
            return True
        else:
            return (request.user.adminaccount.dept.name == obj.dept.name)