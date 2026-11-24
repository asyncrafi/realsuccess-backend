from rest_framework import serializers
from .models import LegalDocument, FAQ


class LegalDocumentSerializer(serializers.ModelSerializer):
    privacyPolicyContent = serializers.CharField(source="privacy_policy_content", required=False)
    privacy_policy_content = serializers.CharField(required=False, write_only=True)
    termsConditionsContent = serializers.CharField(source="terms_conditions_content", required=False)
    terms_conditions_content = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = LegalDocument
        fields = [
            "id",
            "privacyPolicyContent",
            "privacy_policy_content",
            "termsConditionsContent",
            "terms_conditions_content",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def update(self, instance, validated_data):
        if "privacy_policy_content" in validated_data:
            instance.privacy_policy_content = validated_data["privacy_policy_content"]
        if "terms_conditions_content" in validated_data:
            instance.terms_conditions_content = validated_data["terms_conditions_content"]
        return super().update(instance, validated_data)


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer", "category", "order", "is_active"]
