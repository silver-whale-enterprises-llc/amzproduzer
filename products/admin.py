import csv
import re
from decimal import Decimal

from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

from .models import Supplier, Product, InventoryUpload


def find_price_col_index(obj: InventoryUpload, line: list) -> int:
    try:
        return int(obj.price_col)
    except ValueError:
        for index, value in enumerate(line):
            if obj.price_col.strip().lower() == value.strip().lower():
                return index

    return -1


def find_identifier_col_index(obj: InventoryUpload, line: list) -> int:
    try:
        return int(obj.identifier_col)
    except ValueError:
        for index, value in enumerate(line):
            if obj.identifier_col.strip().lower() == value.strip().lower():
                return index

    return -1


def save_status(obj: InventoryUpload, status: int, msg: str = ''):
    obj.status = status
    obj.failed_analysis_reason = msg
    obj.save()


def create_or_update_product(obj: InventoryUpload, line: list, price_col: int, identifier_col: int):
    fields = {'supplier': obj.supplier}

    identifier = str(line[identifier_col]).strip()
    if not identifier:
        return

    fields[obj.identifier_field()] = identifier

    product = Product.objects.filter(**fields)
    fields['wholesale_price'] = Decimal(re.sub(r'\s\$', '', line[price_col]))
    if product.exists():
        product.update(**fields)
    else:
        product = Product.objects.create(**fields)
        obj.products.add(product)
        obj.save()


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
