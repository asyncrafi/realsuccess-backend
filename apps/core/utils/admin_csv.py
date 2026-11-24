import csv
from datetime import datetime
from django.http import HttpResponse

try:
    from import_export import resources
    from import_export.admin import ExportMixin
    HAS_IMPORT_EXPORT = True
except ImportError:
    HAS_IMPORT_EXPORT = False
    class ExportMixin:
        pass


if HAS_IMPORT_EXPORT:
    class SmartModelResource(resources.ModelResource):
        """
        Intelligent ModelResource that automatically expands:
        - ForeignKeys -> human-readable string
        - ManyToMany -> comma-separated list of items
        """
        def export_field(self, field, instance, **kwargs):
            val = super().export_field(field, instance, **kwargs)
            attr_name = getattr(field, 'attribute', None) or getattr(field, 'column_name', None)
            if attr_name:
                clean_name = attr_name[:-3] if attr_name.endswith('_id') else attr_name
                try:
                    f_obj = instance._meta.get_field(clean_name)
                    if f_obj.is_relation and f_obj.many_to_one:
                        rel_obj = getattr(instance, clean_name, None)
                        if rel_obj is not None:
                            return str(rel_obj)
                    elif f_obj.is_relation and f_obj.many_to_many:
                        m2m = getattr(instance, clean_name, None)
                        if m2m is not None:
                            return ', '.join(str(x) for x in m2m.all())
                except Exception:
                    pass
            return val


def export_as_csv_action(description="📥 Export selected to CSV", fields=None, exclude=None):
    """
    Returns an admin action that exports selected queryset objects to a CSV file.
    """
    def export_as_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta
        field_names = fields or [field.name for field in opts.fields]
        if exclude:
            field_names = [f for f in field_names if f not in exclude]

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{opts.model_name}_export_{timestamp}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        response.write('\ufeff')
        writer = csv.writer(response)

        headers = []
        for f in field_names:
            try:
                field_obj = opts.get_field(f)
                headers.append(getattr(field_obj, 'verbose_name', f).title())
            except Exception:
                headers.append(f.replace('_', ' ').title())
        writer.writerow(headers)

        for obj in queryset:
            row = []
            for field in field_names:
                try:
                    val = getattr(obj, field, '')
                    if callable(val):
                        try:
                            val = val()
                        except Exception:
                            val = ''
                    if val is None:
                        val = ''
                    elif hasattr(val, 'all'):
                        val = ', '.join(str(x) for x in val.all())
                    elif hasattr(val, 'strftime'):
                        val = val.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(val, bool):
                        val = 'Yes' if val else 'No'
                    elif isinstance(val, (list, tuple)):
                        val = ', '.join(str(x) for x in val)
                    else:
                        val = str(val)
                except Exception:
                    val = ''
                row.append(val)
            writer.writerow(row)

        return response

    export_as_csv.short_description = description
    return export_as_csv


class ExportCsvMixin(ExportMixin):
    """
    Universal Export Mixin for ModelAdmins.
    """
    if HAS_IMPORT_EXPORT:
        def get_resource_classes(self, request=None):
            if hasattr(self, 'resource_classes') and self.resource_classes:
                return self.resource_classes
            if hasattr(self, 'resource_class') and self.resource_class:
                return [self.resource_class]

            class ModelSmartResource(SmartModelResource):
                class Meta:
                    model = self.model
            return [ModelSmartResource]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'export_as_csv' not in actions:
            action = export_as_csv_action()
            actions['export_as_csv'] = (action, 'export_as_csv', action.short_description)
        return actions
