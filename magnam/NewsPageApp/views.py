from .models import News
from rest_framework import generics, status
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from utils.permission import PermissionCheck
from .globals import *


class NewsView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = News.objects.all()
    serializer_class = ReturnNewsSerializer


class CreateNewsView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    serializer_class = CreateEditNewsSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        news = serializer.save()
        return Response({"data": {"id": news.id}}, status=status.HTTP_201_CREATED)


class GetNewsView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnNewsSerializer

    def get(self, request, news_id, format=None):
        news = get_object_or_404(News, id=news_id)
        data = self.serializer_class(news, context={"request": request}).data
        return Response({"data": data}, status=status.HTTP_200_OK)


class EditNewsView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    serializer_class = CreateEditNewsSerializer

    def patch(self, request, news_id, format=None):
        news = get_object_or_404(News, id=news_id)
        serializer = self.serializer_class(
            instance=news, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        news = serializer.save()
        return Response(status=status.HTTP_200_OK)


class DeleteNewsView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"

    def delete(self, request, news_id, format=None):
        news = get_object_or_404(News, id=news_id)
        news.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NewsCarouselView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    queryset = News.objects.all()
    serializer_class = ReturnNewsSerializer
