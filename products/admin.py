from django.contrib import admin
from .models import Supplier, Product, InventoryUpload


class InventoryUploadAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['supplier', 'file']}),
        ('File Info', {'fields': ['price_col', 'identifier_col', 'identifier_type']}),
    ]

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        super().save_model(request, obj, form, change)


class ProductAdmin(admin.ModelAdmin):
    list_filter = ('supplier__name', 'files', 'roi', 'sales_rank', 'profit', 'sold_by_amazon')


admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(InventoryUpload, InventoryUploadAdmin)
