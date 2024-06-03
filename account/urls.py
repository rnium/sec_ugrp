from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('login/', views.login_page, name="user_login_get"),
    path('api/login', views.api_login, name="user_login_api"),
    path('logout/', views.LogoutView.as_view(), name="user_logout"),
    path('admin/editprofile', views.view_admin_profile_edit, name="view_admin_profile_edit"),
    path('createstudentaccount/', views.StudentAccountCreate.as_view(), name="create_student_account"),
    path('createstudentaccount/excel/session<int:pk>', views.create_student_via_excel, name="create_student_via_excel"),
    path('setstudentavatar/', views.set_student_avatar, name="set_student_avatar"),
    path('student/<int:registration>/', views.StudentProfileView.as_view(), name="view_student_profile"),
    path('student/<int:registration>/migratesession', views.migrate_sesion_of_student, name="migrate_sesion_of_student"),
    path('student/<int:registration>/delete', views.delete_student, name="delete_student"),
    path('student/<int:pk>/updateinfo/', views.StudentInfoUpdate.as_view(), name="update_student_info"),
    path('sendstaffsignuptoken', views.send_signup_token, name="send_staff_signup_token"),
    path('admin/signup/', views.signup_admin, name="signupadmin"),
    path('admin/update/', views.update_admin_account, name="update_admin_account"),
    path('admin/signup/createaccount/<str:tokenId>', views.create_admin_account, name="create_admin_account"),
    path('setadminavatar/', views.set_admin_avatar, name="set_admin_avatar"),
    path('recovery/', views.forgot_password_get, name="forgot_password_get"),
    path('api/recovery/sendmail', views.send_recovery_email_api, name="send_recovery_email_api"),
    path('recovery/<uidb64>/<token>', views.reset_password_get, name="reset_password_get"),
    path('api/recovery/setpassword/<uidb64>/<emailb64>', views.reset_password_api, name="reset_password_api"),
    path('get-userinfo/', views.get_admin_user_info, name="get_admin_user_info"),
    path('api/deleteaccount/', views.delete_admin_account, name="delete_admin_account"),
]
   