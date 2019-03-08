import requests

from products.models import InventoryUpload, Product, AmazonCategorySalesRank, AmazonCategory, AmazonProductListing
from django.conf import settings
import keepa


def get_amzscout_sales_estimate(listing_data: dict):
    root_category_id = listing_data.get('rootCategory')
    category = AmazonCategory.objects.filter(category_id=root_category_id)
    if not category.exists():
        return 0

    # request amz scout sales estimate
    bsr = listing_data['stats']['SALES'][-1]
    cat_name = category.values_list('name', flat=True).first()

    params = {'domain': 'COM', 'category': cat_name, 'rank': bsr}
    response = requests.api.get(settings.AMZ_SCOUT_ESTIMATOR_ENDPOINT, params)
    response.raise_for_status()
    return response.json()['sales']


def get_asin(listing_data: dict):
    return listing_data.get('asin')


def get_name(listing_data: dict):
    return listing_data.get('title')


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
            listings_data = keepa_api.query(identifier, offers=20, stats=365, rating=True,
                                            product_code_is_asin=identifier_is_asin)
        except Exception as e:
            product.status = Product.FAILED
            product.failed_analysis_reason = str(e)
            product.save()
            continue

        for listing in listings_data:
            try:
                amzscout_sales_estimate = get_amzscout_sales_estimate(listings_data)
            except Exception as e:
                product.status = Product.FAILED
                product.failed_analysis_reason = str(e)
                product.save()
                continue

            sales_per_review_multiplier = 25  # TODO: put this on a config table
            latest_review_count = listing['data'].get('COUNT_REVIEWS', [0])[-1]
            review_count_sales_estimate = latest_review_count * sales_per_review_multiplier

            sales_estimate = amzscout_sales_estimate or review_count_sales_estimate or 0

            # update product
            amazon_listing = AmazonProductListing.objects.create(
                product=product,
                asin=get_asin(listing),
                name=get_name(listing),
                # fees
                # total_cost
                # profit
                # profit_median
                # profit_avg
                # roi
                # buy_box
                # buy_box_median
                # buy_box_std_dev
                # buy_box_variance
                # buy_box_avg90
                # buy_box_min
                # buy_box_max
                # buy_box_min_date
                # buy_box_max_date
                # review_count
                # review_count_last30
                # review_count_avg90
                # sales_rank
                # sales_rank_median
                # sales_rank_avg90
                # sales_rank_std_dev
                # sales_rank_std_variance
                # fba_sellers_count
                # root_category
                # sales_estimate_current
                # sales_estimate_avg
                # three_month_supply_cost
                # three_month_supply_amount
                # sold_by_amazon
                # isAddOn
            )

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
