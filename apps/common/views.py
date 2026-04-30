from django.db import connection
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


@extend_schema(
    summary="Health check.",
    description="Returns the health status of the API and its dependencies. Used by Docker and monitoring tools.",
    responses={
        200: inline_serializer(
            name="HealthCheckResponse",
            fields={
                "status": serializers.CharField(),
                "database": serializers.CharField(),
            }
        ),
        503: OpenApiResponse(description="Service unavailable. One or more dependencies are down."),
    },
    tags=["Health"],
)
class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # skip JWT parsing for this endpoint

    def get(self, request):
        health = {
            "status": "ok",
            "database": "ok",
        }
        http_status = status.HTTP_200_OK

        try:
            connection.ensure_connection()
        except OperationalError:
            health["status"] = "degraded"
            health["database"] = "unavailable"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(health, status=http_status)