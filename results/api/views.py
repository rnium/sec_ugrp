from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializer import (SessionSerializer)
from .permission import IsCampusAdmin
from results.models import Session

class ConstaintFailureException(APIException):
    status_code = 400
    default_detail = 'Constraint failure.'

class SessionCreate(CreateAPIView):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Session.objects.all()
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise ConstaintFailureException(str(e))