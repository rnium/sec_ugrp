from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('login/', views.login_page, name="user_login_get"),
    path('api/login', views.api_login, name="user_login_api"),
    path('logout/', views.LogoutView.as_view(), name="user_logout"),
    path('createstudentaccount/', views.StudentAccountCreate.as_view(), name="create_student_account"),
    path('createstudentaccount/excel/session<int:pk>', views.create_student_via_excel, name="create_student_via_excel"),
    path('setstudentavatar/', views.set_student_avatar, name="set_student_avatar"),
    path('student/<int:registration>/', views.StudentProfileView.as_view(), name="view_student_profile"),
    path('sendstaffsignuptoken', views.send_signup_token, name="send_staff_signup_token"),
    path('admin/signup/', views.signup_admin, name="signupadmin"),
    path('admin/signup/createaccount/<str:tokenId>', views.create_admin_account, name="create_admin_account"),
    path('setadminavatar/', views.set_admin_avatar, name="set_admin_avatar"),
]
   