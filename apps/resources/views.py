from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from .models import Resource, UserResourceDownload
from .serializers import ResourceSerializer, UserResourceDownloadSerializer


class ResourceListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["event", "type", "category", "status", "is_featured"]
    search_fields = ["title", "description", "category"]
    ordering_fields = ["created_at", "download_count", "title"]
    ordering = ["-is_featured", "-created_at"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        res = serializer.save()
        return self.created_response(data=self.get_serializer(res).data, message="Resource created successfully")


class ResourceDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self.updated_response(data=serializer.data, message="Resource updated successfully")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.deleted_response(message="Resource deleted successfully")


class ResourceDownloadRecordView(BaseResponseMixin, generics.GenericAPIView):
    """
    Records a download event for this resource.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        user = request.user if request.user.is_authenticated else None
        resource.record_download(user=user)
        return self.success_response(
            data={"download_count": resource.download_count},
            message="Download recorded"
        )


class FeaturedResourceView(BaseResponseMixin, generics.GenericAPIView):
    """
    Mobile screen Featured Resource
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        resource = Resource.objects.filter(is_featured=True, status="Published").first()
        if not resource:
            resource = Resource.objects.filter(status="Published").first()
        if not resource:
            return self.not_found_response(message="No resource found")

        serializer = ResourceSerializer(resource)
        return self.success_response(data=serializer.data)


class RecentDownloadsView(BaseResponseMixin, generics.ListAPIView):
    """
    Mobile screen Recent Downloads
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserResourceDownloadSerializer

    def list(self, request, *args, **kwargs):
        downloads = UserResourceDownload.objects.filter(user=request.user)[:5]
        serializer = self.get_serializer(downloads, many=True)
        return self.success_response(data=serializer.data)
