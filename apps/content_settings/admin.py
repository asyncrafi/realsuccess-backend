from django.contrib import admin
from .models import LegalDocument, FAQ


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "updated_at"]


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ["question", "category", "order", "is_active", "updated_at"]
    list_filter = ["category", "is_active"]
    search_fields = ["question", "answer"]
    list_editable = ["order", "is_active"]
