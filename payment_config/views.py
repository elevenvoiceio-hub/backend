from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PaymentConfig
from rest_framework import serializers
import uuid
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from VoiceAsService.utils import mask_secret


class PaymentConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentConfig
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        secret = data.get("secret_key")
        if secret:
            data["secret_key"] = mask_secret(secret)
        return data


class PaymentConfigListCreateAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve all payment configurations.",
        responses={200: PaymentConfigSerializer(many=True)},
    )
    def get(self, request):
        configs = PaymentConfig.objects.all()
        serializer = PaymentConfigSerializer(configs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new payment configuration.",
        request_body=PaymentConfigSerializer,
        responses={201: PaymentConfigSerializer},
    )
    def post(self, request):
        serializer = PaymentConfigSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentConfigDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return PaymentConfig.objects.get(pk=pk)
        except PaymentConfig.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_description="Retrieve a payment configuration by ID.",
        responses={200: PaymentConfigSerializer, 404: "Not found"},
    )
    def get(self, request, pk):
        config = self.get_object(pk)
        if not config:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentConfigSerializer(config)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a payment configuration by ID.",
        request_body=PaymentConfigSerializer,
        responses={200: PaymentConfigSerializer, 404: "Not found"},
    )
    def put(self, request, pk):
        config = self.get_object(pk)
        if not config:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a payment configuration by ID.",
        responses={204: "No Content", 404: "Not found"},
    )
    def delete(self, request, pk):
        config = self.get_object(pk)
        if not config:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentConfigGetOneAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Get the first payment configuration and generate an order ID.",
        responses={
            200: openapi.Response(
                description="Payment config and order ID",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "config": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "order_id": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            404: "No payment config found",
        },
    )
    def get(self, request):
        config = PaymentConfig.objects.first()
        if not config:
            return Response(
                {"error": "No payment config found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = PaymentConfigSerializer(config)
        order_id = str(uuid.uuid4())
        return Response(
            {"config": serializer.data, "order_id": order_id}, status=status.HTTP_200_OK
        )
