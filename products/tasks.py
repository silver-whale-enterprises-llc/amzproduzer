from __future__ import absolute_import, unicode_literals
import datetime
import random
import re
import urllib
import keepa
import requests
from celery import shared_task
from decimal import Decimal, getcontext
from time import sleep
from urllib.parse import quote
from products.models import InventoryUpload, Product, AmazonCategory, AmazonProductListing
from django.conf import settings


# ===========================================================
# Data gathering
# ===========================================================

def get_root_category(listing_data: dict):
    root_category_id = listing_data.get('rootCategory')
    if root_category_id == 0:
        return None  # no category known

    max_64bit_int_value = 9223372036854775807  # 2^(64 - 1) -1
    if root_category_id == max_64bit_int_value:
        return None  # blank category with the name "?". Product is listed in no or non-existent categories

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
    if buy_box <= 0:
        buy_box = 0
    return Decimal(buy_box / 100)  # /100 = convert from cents to dollars


def get_fees(listing_data: dict):
    # TODO: get from amazon
    fees_data = listing_data.get('fbaFees', {})
    if not fees_data:
        return 0
    fba_fees = Decimal(sum([Decimal(fee) for fee in fees_data.values() if fee > 0]) / 100)
    buy_box = get_buy_box(listing_data)
    referral_estimate = buy_box * Decimal(0.15)
    return fba_fees + referral_estimate


def get_sales_rank_avg90(listing_data):
    sr_history = listing_data.get('data', {}).get('SALES', [])
    sr_history_date = listing_data.get('data', {}).get('SALES_time', [])
    data_points = len(sr_history)

    if not data_points:
        return 0

    start_date = datetime.datetime.now() + datetime.timedelta(-90)
    start_index = 0
    while start_index < data_points and sr_history_date[start_index] < start_date:
        start_index += 1

    if start_index == data_points:
        return 0

    last_90_days = sr_history[start_index:]
    sum_sr = sum(last_90_days)
    if sum_sr == -1:
        return 0

    return int(round(sum_sr / len(last_90_days)))


def get_sales_rank(listing_data: dict):
    sr = listing_data.get('data', {}).get('SALES', [0])[-1]
    return sr if sr > 0 else 0


def get_review_count(listing_data: dict):
    revs = listing_data.get('data', {}).get('COUNT_REVIEWS', [0])[-1]
    return revs if revs > 0 else 0


def get_rating(listing_data: dict):
    rat = listing_data.get('data', {}).get('RATING', [0])[-1]
    return rat if rat > 0 else 0


def get_number_of_items(listing_data: dict):
    # packageQuantity
    # Quantity of items in a package. 0 or -1 if not available.
    # Example: 9

    # numberOfItems
    # The number of items of this product. -1 if not available.
    # Example: 1
    number_of_items = listing_data.get('numberOfItems', 1)
    if number_of_items < 1:
        number_of_items = 1

    return number_of_items


def get_pack_count(listing_data: dict):
    # if this a "Pack of x units" try and find x from the name
    name = get_name(listing_data)

    regex = r'(?:pk|pack)\s?(?:of\s?)(\d+)|(\d+)\s?(?:pk|pack)'
    matches = re.finditer(regex, name, re.IGNORECASE)
    first_match = next(matches, None)
    if not first_match:
        return 1
    return int(first_match.group(2))


def get_total_cost(listing_data: dict, unit_price: Decimal):
    fees = get_fees(listing_data)
    pack_units = get_pack_count(listing_data)
    pack_price = pack_units * unit_price

    return fees + pack_price


SLEEP_TIME = [val / 100.0 for val in range(1, 200)]


def get_amzscout_sales_estimate(listing_data: dict):
    category = get_root_category(listing_data)
    if not category:
        return 0

    # request amz scout sales estimate
    bsr = get_sales_rank_avg90(listing_data)
    cat_name = category.name

    if not bsr:
        return 0

    sleep(random.choice(SLEEP_TIME))

    params = {'domain': 'COM', 'category': cat_name, 'rank': bsr}
    query = urllib.parse.urlencode(params, safe='/', quote_via=urllib.parse.quote)
    url = f'{settings.AMZ_SCOUT_ESTIMATOR_ENDPOINT}?{query}'
    cookies = dict(__zlcmid='rKi5WodP36jCpG')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
        'Host': 'amzscout.net',
        'Referer': 'https://amzscout.net/sales-estimator'
    }
    response = requests.api.get(settings.AMZ_SCOUT_ESTIMATOR_ENDPOINT, params=params, headers=headers, cookies=cookies)
    response.raise_for_status()
    response_json = response.json()
    return response_json.get('sales')


def get_sales_estimate(listing_data):
    amzscout_sales_estimate = get_amzscout_sales_estimate(listing_data)

    sales_per_review_multiplier = 25  # TODO: put this on a config table
    latest_review_count = get_review_count(listing_data)
    review_count_sales_estimate = latest_review_count * sales_per_review_multiplier

    return amzscout_sales_estimate or review_count_sales_estimate or 0


def get_fba_sellers_count(listing_data):
    # offerCountFBA: Count of retrieved live new FBA offers, if existent. Otherwise -2.
    count = listing_data.get('stats', {}).get('offerCountFBA', 0)
    if count < 0:
        count = 0

    return count


def get_sold_by_amazon(listing_data):
    # Availability of the Amazon offer. Possible values:
    #
    # -1: no Amazon offer exists
    # 0: Amazon offer is in stock and shippable
    # 1: Amazon offer is currently not in stock, but will be in the future (back-ordered, pre-order)
    # 2: Amazon offer availability is “unknown”
    # 3: Unrecognized Amazon availability status
    status = listing_data.get('availabilityAmazon', -1)
    if status in (0, 1, 2):
        return True
    return False


# ===========================================================
# Analysis
# ===========================================================

def discard(listing: AmazonProductListing, reason=''):
    listing.status = AmazonProductListing.DISCARDED
    listing.discard_reason += reason
    listing.save()


def roi_rule(listing: AmazonProductListing):
    # TODO: put this values in config table
    roi_lower_end = Decimal(0.10)  # percent
    roi_upper_end = Decimal(3.00)  # percent
    if listing.roi < roi_lower_end:
        discard(listing, reason=f'ROI below {round(roi_lower_end * 100)}%, ')
        return False
    if listing.roi > roi_upper_end:
        discard(listing, reason=f'ROI over {round(roi_upper_end * 100)}%, ')
        return False
    return True


def profit_rule(listing: AmazonProductListing):
    # TODO: put this values in config table
    profit_min = Decimal(3.00)  # currency

    if listing.profit < profit_min:
        discard(listing, reason=f'Profit less than ${profit_min}, ')
        return False
    return True


def sold_by_amazon_rule(listing: AmazonProductListing):
    # TODO: put this values in config table
    include_sold_by_amazon = False

    if not include_sold_by_amazon and listing.sold_by_amazon:
        discard(listing, reason=f'Sold by Amazon, ')
        return False
    return True


def sales_rank_rule(listing: AmazonProductListing):
    if listing.root_category:
        if listing.sales_rank_avg90 > listing.root_category.sales_rank.max_allowed:
            discard(listing, reason=f'BSR greater than max allowed {listing.root_category.sales_rank.max_allowed}, ')
            return False
        elif listing.sales_rank_avg90 <= listing.root_category.sales_rank.preferred \
                and listing.status != AmazonProductListing.DISCARDED:
            listing.status = AmazonProductListing.RECOMMENDED
            listing.save()

    return True


def rating_rule(listing: AmazonProductListing):
    # TODO: put this values in config table
    min_rating = 30
    if listing.rating_current < min_rating:
        discard(listing, reason=f'Rating less than {min_rating}, ')
        return False
    return True


def reviews_rule(listing: AmazonProductListing):
    # TODO: put this values in config table
    min_reviews = 10
    if listing.review_count < min_reviews:
        discard(listing, reason=f'Reviews less than {min_reviews}, ')
        return False
    return True


def moq_rule(listing: AmazonProductListing):
    # TODO: put this values in config table
    min_moq = Decimal(500)
    if listing.three_month_supply_cost < min_moq:
        discard(listing, reason=f'3 month supply less than min MOQ of {min_moq}, ')
        return False
    return True


RULES = [
    sales_rank_rule,
    sold_by_amazon_rule,
    profit_rule,
    roi_rule,
    rating_rule,
    reviews_rule,
    moq_rule
]


def analyze_listing(listing: AmazonProductListing):
    all_rules_pass = True
    for pass_rule in RULES:
        if not pass_rule(listing):
            all_rules_pass = False

    if all_rules_pass:
        listing.status = AmazonProductListing.HIGHLIGHTED
        listing.save()


def update_product_status(upload, product, status, reason=''):
    product.status = status
    product.failed_analysis_reason = reason
    product.save()

    if status == Product.FAILED:
        upload.failed_products += 1
    elif status == Product.ANALYSED:
        upload.analysed_products += 1
    upload.save()


def update_or_create_amz_listing(listing: dict, product, upload):
    sales_estimate = get_sales_estimate(listing)

    total_cost = get_total_cost(listing, product.unit_price)
    buy_box = get_buy_box(listing)
    profit = buy_box - total_cost
    roi = profit / total_cost
    fba_sellers_count = get_fba_sellers_count(listing)
    pack_price = get_pack_count(listing) * product.unit_price
    sales_per_month = round(sales_estimate / (fba_sellers_count + 1))

    three_month_supply_amount = sales_per_month * 3
    three_month_supply_cost = three_month_supply_amount * pack_price

    amazon_listing, created = AmazonProductListing.objects.update_or_create(
        product=product,
        asin=get_asin(listing),
        defaults={
            'name': get_name(listing),
            'fees': get_fees(listing),
            'total_cost': total_cost,
            'buy_box': buy_box,
            'profit': profit,
            'roi': roi,
            'sales_rank': get_sales_rank(listing),
            'sales_rank_avg90': get_sales_rank_avg90(listing),
            'sold_by_amazon': get_sold_by_amazon(listing),
            'review_count': get_review_count(listing),
            'rating_current': get_rating(listing),
            'sales_estimate_current': sales_estimate,
            'fba_sellers_count': fba_sellers_count,
            'three_month_supply_amount': three_month_supply_amount,
            'three_month_supply_cost': three_month_supply_cost,
            'root_category': get_root_category(listing),

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
            # sales_rank_std_dev
            # sales_rank_std_variance
            # sales_estimate_avg
            # isAddOn

            # TODO: include these fields
            # hazardousMaterialType
        }
    )

    return amazon_listing


@shared_task(ignore_result=True)
def process_inventory_upload(upload_id: int):
    getcontext().prec = 2  # sets Decimal precision

    upload = InventoryUpload.objects.get(id=upload_id)
    upload.status = InventoryUpload.PROCESSING
    upload.save()

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
            update_product_status(upload, product, Product.FAILED, reason=f'Error: {str(3)}')
            continue

        if not listings_data:
            update_product_status(upload, product, Product.FAILED, reason='No data found on keepa.')
            continue

        for listing in listings_data:
            try:
                # update product
                amazon_listing = update_or_create_amz_listing(listing, product, upload)

                # analyse listing
                analyze_listing(amazon_listing)
            except Exception as e:
                print(f'Error:: {str(e)}')
                update_product_status(upload, product, Product.FAILED, reason=f'Error:: {str(e)}')
                continue

        # update upload status
        if product.status != Product.FAILED:
            update_product_status(upload, product, Product.ANALYSED)

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
