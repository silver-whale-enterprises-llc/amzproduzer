import keepa
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from products.models import AmazonCategorySalesRank, AmazonCategory

ROOT_CATEGORY_NAMES = [
    ('Appliances', 500),
    ('Arts, Crafts & Sewing', 20000),
    ('Automotive', 35000),
    ('Baby', 18000),
    ('Beauty & Personal Care', 55000),
    ('Books', 90000),
    ('Camera & Photo', 2750),
    ('Cell Phones & Accessories', 50000),
    ('Clothing, Shoes & Jewelry', 85000),
    ('Computers & Accessories', 3750),
    ('Electronics', 17500),
    ('Grocery & Gourmet Food', 40000),
    ('Health & Household', 65000),
    ('Home and Garden', 8000),
    ('Home & Kitchen', 110000),
    ('Industrial & Scientific', 12000),
    ('Jewelry', 80000),
    ('Kindle Store', 90000),
    ('Kitchen & Dining', 45000),
    ('Musical Instruments', 7500),
    ('Office Products', 30000),
    ('Patio, Lawn & Garden', 27500),
    ('Pet Supplies', 28000),
    ('Shoes', 60000),
    ('Software', 600),
    ('Sports & Outdoors', 450000),
    ('Tools & Home Improvement', 50000),
    ('Toys & Games', 45000),
    ('Watches', 105000),
    ('Video Games', 4400),
]


class Command(BaseCommand):
    help = 'Gets the main root category ids from amazon'

    def handle(self, *args, **options):
        keepa_api = keepa.Keepa(settings.KEEPA_ACCESS_KEY)

        with transaction.atomic():
            for cat_name, preferred_sr in ROOT_CATEGORY_NAMES:
                category_data = keepa_api.search_for_categories(cat_name)
                category_sales_rank, _ = AmazonCategorySalesRank.objects.update_or_create(name=cat_name,
                                                                                          defaults={
                                                                                              'preferred': preferred_sr
                                                                                          })
                for cat_id in category_data:
                    category = category_data[cat_id]
                    if category['name'] != cat_name:
                        continue
                    defaults = {
                        'products_count': category['productCount'] or 0,
                        'highest_rank': category['highestRank'] or 0
                    }
                    amazon_category, _ = AmazonCategory.objects \
                        .update_or_create(category_id=int(cat_id), name=cat_name, sales_rank=category_sales_rank,
                                          defaults=defaults)
