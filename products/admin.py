import csv
import re
from decimal import Decimal

from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

from products.tasks import process_inventory_upload
from products.utils import find_price_col_index, save_status, find_identifier_col_index, create_or_update_product
from .models import Supplier, Product, InventoryUpload


class InventoryUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'supplier', 'total_products', 'status', 'failed_analysis_reason')
    fieldsets = [
        (None, {'fields': ['supplier', 'file']}),
        ('File Info', {'fields': ['price_col', 'identifier_col', 'identifier_type']}),
    ]

    def save_model(self, request: HttpRequest, obj: InventoryUpload, form: ModelForm, change: bool):
        super().save_model(request, obj, form, change)

        if change:
            return

        try:
            with open(obj.file.name, "r") as read_file:
                reader = csv.reader(read_file, delimiter=',')
                header = next(reader)
                price_col = find_price_col_index(obj, header)
                if price_col < 0 or price_col >= len(header):
                    save_status(obj, InventoryUpload.FAILED,
                                f'Price column value "{obj.price_col}" not found in file!')
                    return
                identifier_col = find_identifier_col_index(obj, header)
                if identifier_col < 0 or identifier_col >= len(header):
                    save_status(obj, InventoryUpload.FAILED,
                                f'Identifier column value "{obj.identifier_col}" not found in file!')
                    return

                for line_no, line in enumerate(list(reader)):
                    if line_no == 0:
                        pass  # skip header

                    create_or_update_product(obj, line, price_col, identifier_col)

                obj.total_products = obj.products.all().count()
                if obj.total_products <= 1:
                    save_status(obj, InventoryUpload.FAILED, 'File is empty. No products found!')
                else:
                    obj.save()

        except Exception as e:
            save_status(obj, InventoryUpload.FAILED, str(e))

        process_inventory_upload(obj.id)


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'supplier',
        'asin',
        'upc',
        'ein',
        'sku',
        'name',
        'wholesale_units',
        'wholesale_price',
        'fees',
        'total_cost',
        'profit',
        'roi',
        'buy_box',
        'buy_box_avg90',
        'buy_box_min',
        'buy_box_max',
        'buy_box_min_date',
        'buy_box_max_date',
        'review_count',
        'review_count_last30',
        'review_count_avg90',
        'sales_rank',
        'sales_rank_avg90',
        'fba_sellers_count',
        'root_category',
        'sales_estimate',
        'three_month_supply_cost',
        'three_month_supply_amount',
        'sold_by_amazon',
        'status',
        'failed_analysis_reason',
    )
    list_filter = ('supplier__name', 'files', 'roi', 'sales_rank', 'profit', 'sold_by_amazon')


admin.site.register(Supplier)
admin.site.register(Product, ProductAdmin)
admin.site.register(InventoryUpload, InventoryUploadAdmin)
