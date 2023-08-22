from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('login/', views.login_page, name="user_login_get"),
    path('api/login', views.api_login, name="user_login_api"),
    path('logout/', views.LogoutView.as_view(), name="user_logout"),
    path('createstudentaccount/', views.StudentAccountCreate.as_view(), name="create_student_account"),
    path('setstudentavatar/', views.set_student_avatar, name="set_student_avatar"),
    path('student/<int:registration>/', views.StudentProfileView.as_view(), name="view_student_profile"),
    path('sendstaffsignuptoken', views.send_signup_token, name="send_staff_signup_token"),
    path('admin/signup/', views.signup_admin, name="signupadmin"),
    path('admin/signup/createaccount/<str:tokenId>', views.create_admin_account, name="create_admin_account"),
    # path('profile/', views.ProfileView.as_view(), name="user_profile"),
    # path('signup/', SignupView.as_view(), name="user_signup_get"),
    # path('api/verify/sendmail', send_verification_email_api, name="send_verification_email_api"),
    # path('verify/<uidb64>/<token>', verify_user, name="verify_user"),
    # path('recovery', forgot_password_get, name="forgot_password_get"),
    # path('api/recovery/sendmail', send_recovery_email_api, name="send_recovery_email_api"),
    # path('recovery/<uidb64>/<token>', reset_password_get, name="reset_password_get"),
    # path('api/recovery/setpassword/<uidb64>/<emailb64>', reset_password_api, name="reset_password_api"),
    # path('profile/<int:pk>', view_profile, name="view_profile"),
    # path('profile/update', update_profile, name="update_profile_api"),
    # path('profile/update/password', update_password_get, name="update_password_get"),
    # path('profile/api/update/password', update_password_api, name="update_password_api"),
    # path('profile/edit', edit_profile, name="edit_profile"),
    # path('api/signup', api_signup, name="user_signup_post"),
    # path('profile/avatar/set', set_avatar, name="set_avatar"),
]
   