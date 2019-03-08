import re
from decimal import Decimal

from products.models import InventoryUpload, Product


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
    fields['unit_price'] = Decimal(re.sub(r'\s\$', '', line[price_col]))
    if product.exists():
        product.update(**fields)
    else:
        product = Product.objects.create(**fields)
        obj.products.add(product)
        obj.save()
