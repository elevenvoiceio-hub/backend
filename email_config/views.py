from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from permissions import IsAdmin
from .models import EmailConfig
from .serializer import EmailConfigSerializer  # Adjust import as needed
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class EmailConfigListCreateAPIView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description="Retrieve all email configurations.",
        responses={200: EmailConfigSerializer(many=True)},
    )
    def get(self, request):
        """
        Get all email configurations.

        Returns a list of all email configuration objects.
        """
        configs = EmailConfig.objects.all()
        serializer = EmailConfigSerializer(configs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new email configuration.",
        request_body=EmailConfigSerializer,
        responses={201: EmailConfigSerializer(), 400: "Validation Error"},
    )
    def post(self, request):
        """
        Create a new email configuration.

        Accepts email configuration data and creates a new record.
        """
        data = request.data.copy()
        data["created_by"] = request.user.id
        serializer = EmailConfigSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailConfigDetailAPIView(APIView):
    permission_classes = [IsAdmin]

    def get_object(self, pk):
        try:
            return EmailConfig.objects.get(pk=pk)
        except EmailConfig.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_description="Retrieve a specific email configuration by ID.",
        responses={200: EmailConfigSerializer(), 404: openapi.Response("Not found")},
    )
    def get(self, request, pk):
        """
        Get a specific email configuration by ID.

        Returns the email configuration object if found.
        """
        config = self.get_object(pk)
        if not config:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmailConfigSerializer(config)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a specific email configuration by ID.",
        request_body=EmailConfigSerializer,
        responses={
            200: EmailConfigSerializer(),
            400: "Validation Error",
            404: openapi.Response("Not found"),
        },
    )
    def put(self, request, pk):
        """
        Update a specific email configuration by ID.

        Accepts updated data for the email configuration.
        """
        config = self.get_object(pk)
        if not config:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data["created_by"] = config.created_by.id  # Preserve original creator
        serializer = EmailConfigSerializer(config, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetDefaultEmailConfigAPIView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(
        operation_description="Retrieve the default email configuration.",
        responses={200: EmailConfigSerializer(), 404: "Not found"},
    )
    def get(self, request):
        """
        Get the default email configuration.

        Returns the active and default email configuration object.
        """
        config = EmailConfig.objects.filter(is_active=True, is_default=True).first()
        if not config:
            return Response(
                {"error": "No default email configuration found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EmailConfigSerializer(config)
        return Response(serializer.data)
