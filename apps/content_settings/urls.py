from django.urls import path
from .views import (
    LegalDocumentView,
    PrivacyPolicyAPIView,
    TermsConditionsAPIView,
    FAQListView,
    FAQDetailView,
)

app_name = "content_settings"

urlpatterns = [
    path("legal/", LegalDocumentView.as_view(), name="legal-documents"),
    path("privacy/", PrivacyPolicyAPIView.as_view(), name="privacy-policy"),
    path("terms/", TermsConditionsAPIView.as_view(), name="terms-conditions"),
    path("faq/", FAQListView.as_view(), name="faq-list"),
    path("faq/<int:pk>/", FAQDetailView.as_view(), name="faq-detail"),
]
