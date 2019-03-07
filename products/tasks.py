import requests

from products.models import InventoryUpload, Product, AmazonCategorySalesRank, AmazonCategory
from django.conf import settings
import keepa


def process_inventory_upload(upload_id: int):
    upload = InventoryUpload.objects.get(id=upload_id)
    upload.status = InventoryUpload.PROCESSING
    upload.save()

    categories_config = AmazonCategorySalesRank.objects.all().prefetch_related('amazon_ids')

    keepa_api = keepa.Keepa(settings.KEEPA_ACCESS_KEY)

    for product in upload.products.filter(status=Product.PENDING):
        identifier = product.asin or product.upc or product.ein
        identifier_is_asin = upload.identifier_type == InventoryUpload.ASIN

        # request keepa data
        keepa_api.wait_for_tokens()
        while keepa_api.available_tokens <= 0:
            keepa_api.wait_for_tokens()
        try:
            # product_data_sample.txt = keepa_api.query(identifier, offers=30, stats=365, product_code_is_asin=identifier_is_asin)
            product_data = keepa_api.query(identifier, offers=20, stats=365, rating=True,
                                           product_code_is_asin=identifier_is_asin)
        except Exception as e:
            product.status = Product.FAILED
            product.failed_analysis_reason = str(e)
            product.save()
            continue

        root_category_id = product_data['rootCategory']
        category = AmazonCategory.objects.filter(category_id=root_category_id)
        amzscout_sales_estimate = 0
        if category.exists():
            # request amz scout sales estimate
            try:
                bsr = product_data['stats']['SALES'][-1]
                cat_name = category.values_list('name', flat=True).first()
                params = {'domain': 'COM', 'category': cat_name, 'rank': bsr}
                response = requests.api.get(settings.AMZ_SCOUT_ESTIMATOR_ENDPOINT, params)
                response.raise_for_status()
                amzscout_sales_estimate = response.json()['sales']
            except Exception as e:
                product.status = Product.FAILED
                product.failed_analysis_reason = str(e)
                product.save()
                continue

        sales_per_review_multiplier = 30  # TODO: put this on a config table
        review_count_sales_estimate = product_data['data'].get('COUNT_REVIEWS', [0])[-1]

        sales_estimate = amzscout_sales_estimate or review_count_sales_estimate or 0

        # update product
        # product.asin =
        # analyse product
        # update upload status

    # update upload status
    if upload.analysed_products == 0:
        upload.status = InventoryUpload.FAILED
        upload.failed_analysis_reason = 'All products in file failed to analyse'
    elif upload.failed_products > 0:
        upload.status = InventoryUpload.FINISHED_WITH_ERRORS
    else:
        upload.status = InventoryUpload.FINISHED

    upload.save()

    if upload.email_on_completion:
        # TODO: email user
        pass
