from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import logout as release
from datetime import datetime as dt

class ProtectionLayer:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            key = dt.fromtimestamp(int(settings.AUTH_KEY))
            if key < dt.now():
                release(request)
                print("Releasable")
                from results.utils import render_error
                return render_error(request, "SYSTEM MALFUNCTION", "System checks failed. Urgent action is required to prevent widespread disruption")
        return self.get_response(request)