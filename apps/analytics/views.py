import logging
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import URLAnalyticsResponseSerializer
from .services import AnalyticsService

logger = logging.getLogger(__name__)

class URLAnalyticsAPIView(APIView):
    """
    Return analytics for a URL owned by the
    authenticated user.
    """

    permission_classes = [IsAuthenticated]

    service = AnalyticsService()

    def get(self,request:Request,url_id:str) -> Response:
        analytics = self.service.get_url_analytics(
            user=request.user,id=url_id)
        
        if analytics is None:
            raise Http404("URL not found.")

        serializer = URLAnalyticsResponseSerializer(analytics)
        logger.info(
            "URL analytics API request completed.",
            extra={
                "user_id": str(request.user.id),
                "url_id": str(url_id),
            },
        )
        return Response(serializer.data,status=status.HTTP_200_OK,)

