from decimal import Decimal

import requests

from products.models import InventoryUpload, Product, AmazonCategorySalesRank, AmazonCategory, AmazonProductListing
from django.conf import settings
import keepa


def get_root_category(listing_data: dict):
    root_category_id = listing_data.get('rootCategory')
    category = AmazonCategory.objects.filter(category_id=root_category_id)
    if not category.exists():
        return None
    return category.first()


def get_asin(listing_data: dict):
    return listing_data.get('asin')


def get_name(listing_data: dict):
    return listing_data.get('title')


def get_buy_box(listing_data: dict):
    buy_box = listing_data.get('stats', {}).get('buyBoxPrice', 0)
    if buy_box < 0:
        buy_box = 0
    return buy_box


def get_fees(listing_data: dict):
    fbafees = sum([round(fee / 100, 2) for fee in listing_data.get('fbaFees', {}).values()])
    buy_box = get_buy_box(listing_data)
    referral_estimate = buy_box * 0.15
    return round(fbafees + referral_estimate, 2)


def get_sales_rank(listing_data: dict):
    return listing_data.get('data', {}).get('SALES', [0])[-1]


def get_review_count(listing_data: dict):
    return listing_data.get('data', {}).get('COUNT_REVIEWS', [0])[-1]


def get_rating(listing_data: dict):
    return listing_data.get('data', {}).get('COUNT_REVIEWS', [0])[-1]


def get_total_cost(listing_data: dict, unit_price):
    fbafees = get_fees(listing_data)
    listing_units = listing_data.get('numberOfItems', 1)
    if listing_units < 1:
        listing_units = 1
    return round(fbafees + listing_units * unit_price, 2)


def get_amzscout_sales_estimate(listing_data: dict):
    category = get_root_category(listing_data)
    if not category:
        return 0

    # request amz scout sales estimate
    bsr = get_sales_rank(listing_data)
    cat_name = category.values_list('name', flat=True).first()

    params = {'domain': 'COM', 'category': cat_name, 'rank': bsr}
    response = requests.api.get(settings.AMZ_SCOUT_ESTIMATOR_ENDPOINT, params)
    response.raise_for_status()
    return response.json()['sales']


def get_sales_estimate(listing_data):
    amzscout_sales_estimate = get_amzscout_sales_estimate(listing_data)

    sales_per_review_multiplier = 25  # TODO: put this on a config table
    latest_review_count = get_review_count(listing_data)
    review_count_sales_estimate = latest_review_count * sales_per_review_multiplier

    return amzscout_sales_estimate or review_count_sales_estimate or 0


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
                sales_estimate = get_sales_estimate(listing)
            except Exception as e:
                product.status = Product.FAILED
                product.failed_analysis_reason = str(e)
                product.save()
                continue

            # update product
            amazon_listing = AmazonProductListing.objects.create(
                product=product,
                asin=get_asin(listing),
                name=get_name(listing),
                fees=get_fees(listing),
                total_cost=get_total_cost(listing, product.unit_price),
                buy_box=get_buy_box(listing),
                # profit
                # roi
                # sold_by_amazon
                sales_rank=get_sales_rank(listing),
                root_category=get_root_category(listing),
                review_count=get_review_count(listing),
                rating_current=get_rating(listing),
                sales_estimate_current=sales_estimate,
                # three_month_supply_cost
                # three_month_supply_amount

                # profit_median
                # profit_avg
                # buy_box_median
                # buy_box_std_dev
                # buy_box_variance
                # buy_box_avg90
                # buy_box_min
                # buy_box_max
                # buy_box_min_date
                # buy_box_max_date
                # review_count_last30
                # review_count_avg90
                # sales_rank_median
                # sales_rank_avg90
                # sales_rank_std_dev
                # sales_rank_std_variance
                # fba_sellers_count
                # sales_estimate_avg
                # isAddOn

                # TODO: include these fields
                # hazardousMaterialType
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
