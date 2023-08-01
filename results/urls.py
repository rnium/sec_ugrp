from django.urls import path
from results import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.DashboardView.as_view(), name="admin_dashboard"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)