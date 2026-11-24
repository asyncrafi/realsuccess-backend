from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from apps.core.utils.mixins import BaseResponseMixin
from .models import LegalDocument, FAQ
from .serializers import LegalDocumentSerializer, FAQSerializer


class LegalDocumentView(BaseResponseMixin, APIView):
    """
    Get or update privacy policy and terms & conditions content.
    Public read access for mobile/web; staff access for update.
    """
    permission_classes = [AllowAny]

    def _get_document(self):
        doc = LegalDocument.objects.first()
        if not doc:
            doc = LegalDocument.objects.create()
        return doc

    def get(self, request):
        doc = self._get_document()
        serializer = LegalDocumentSerializer(doc)
        return self.success_response(
            data=serializer.data,
            message="Legal documents retrieved successfully"
        )

    def put(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.error_response(
                message="Admin permissions required to update legal documents",
                status_code=status.HTTP_403_FORBIDDEN
            )
        doc = self._get_document()
        privacy = request.data.get("privacy_policy_content") or request.data.get("privacyPolicyContent")
        terms = request.data.get("terms_conditions_content") or request.data.get("termsConditionsContent")
        if privacy is not None:
            doc.privacy_policy_content = privacy
        if terms is not None:
            doc.terms_conditions_content = terms
        doc.save()
        serializer = LegalDocumentSerializer(doc)
        return self.success_response(
            data=serializer.data,
            message="Legal documents updated successfully"
        )


class PrivacyPolicyAPIView(BaseResponseMixin, APIView):
    """
    Dedicated API endpoint for mobile/frontend apps to get Privacy Policy.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        doc = LegalDocument.objects.first()
        if not doc:
            doc = LegalDocument.objects.create()
        return self.success_response(
            data={
                "title": "Privacy Policy",
                "content": doc.privacy_policy_content,
                "updated_at": doc.updated_at,
            },
            message="Privacy policy retrieved successfully"
        )


class TermsConditionsAPIView(BaseResponseMixin, APIView):
    """
    Dedicated API endpoint for mobile/frontend apps to get Terms & Conditions.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        doc = LegalDocument.objects.first()
        if not doc:
            doc = LegalDocument.objects.create()
        return self.success_response(
            data={
                "title": "Terms & Conditions",
                "content": doc.terms_conditions_content,
                "updated_at": doc.updated_at,
            },
            message="Terms and conditions retrieved successfully"
        )


def privacy_policy_page(request):
    """Public HTML page for App Store and Google Play compliance."""
    from django.shortcuts import render
    doc = LegalDocument.objects.first()
    if not doc:
        doc = LegalDocument.objects.create()
    return render(request, "legal/privacy_policy.html", {
        "content": doc.privacy_policy_content,
        "updated_at": doc.updated_at,
    })


def terms_conditions_page(request):
    """Public HTML page for App Store and Google Play compliance."""
    from django.shortcuts import render
    doc = LegalDocument.objects.first()
    if not doc:
        doc = LegalDocument.objects.create()
    return render(request, "legal/terms_conditions.html", {
        "content": doc.terms_conditions_content,
        "updated_at": doc.updated_at,
    })


class FAQListView(BaseResponseMixin, APIView):
    """
    List active FAQs for mobile and admin dashboard.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        category = request.query_params.get("category")
        qs = FAQ.objects.filter(is_active=True)
        if category:
            qs = qs.filter(category=category)
        serializer = FAQSerializer(qs, many=True)
        return self.success_response(
            data=serializer.data,
            message="FAQs retrieved successfully"
        )

    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.error_response(
                message="Admin permissions required",
                status_code=status.HTTP_403_FORBIDDEN
            )
        serializer = FAQSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message="FAQ created successfully",
                status_code=status.HTTP_201_CREATED
            )
        return self.error_response(
            message="Invalid FAQ data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FAQDetailView(BaseResponseMixin, APIView):
    """
    Retrieve, update or delete a specific FAQ.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        faq = get_object_or_404(FAQ, pk=pk)
        return self.success_response(
            data=FAQSerializer(faq).data,
            message="FAQ retrieved successfully"
        )

    def put(self, request, pk):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.error_response(
                message="Admin permissions required",
                status_code=status.HTTP_403_FORBIDDEN
            )
        faq = get_object_or_404(FAQ, pk=pk)
        serializer = FAQSerializer(faq, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                data=serializer.data,
                message="FAQ updated successfully"
            )
        return self.error_response(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.error_response(
                message="Admin permissions required",
                status_code=status.HTTP_403_FORBIDDEN
            )
        faq = get_object_or_404(FAQ, pk=pk)
        faq.delete()
        return self.success_response(message="FAQ deleted successfully")
