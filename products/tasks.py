from products.models import InventoryUpload, Product
from django.conf import settings
import keepa


def process_inventory_upload(upload_id: int):
    upload = InventoryUpload.objects.get(id=upload_id)
    upload.status = InventoryUpload.PROCESSING
    upload.save()

    keepa_api = keepa.Keepa(settings.KEEPA_ACCESS_KEY)

    for product in upload.products.filter(status=Product.PENDING):
        identifier = product.asin or product.upc or product.ein
        identifier_is_asin = upload.identifier_type == InventoryUpload.ASIN

        # request keepa data
        keepa_api.wait_for_tokens()
        while keepa_api.user.tokens_left <= 0:
            keepa_api.wait_for_tokens()
        try:
            # product_data_sample.txt = keepa_api.query(identifier, offers=30, stats=365, product_code_is_asin=identifier_is_asin)
            product_data = keepa_api.query(identifier, offers=20, stats=365, product_code_is_asin=identifier_is_asin)
        except Exception as e:
            product.status = Product.FAILED
            product.failed_analysis_reason = str(e)
            product.save()
            continue

        # request amz scout sales estimate

        # update product
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
