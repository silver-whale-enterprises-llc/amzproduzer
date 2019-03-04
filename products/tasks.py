from products.models import InventoryUpload


def process_inventory_upload(upload_id: int):
    upload = InventoryUpload.objects.get(upload_id)
    upload.status = InventoryUpload.PROCESSING
    upload.save()

    for product in upload.products.all():
        # request keepa data
        # update product
        # analyse product
        # update upload status
        pass

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
