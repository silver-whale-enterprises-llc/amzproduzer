from django.db import models


class TimeStamp(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Supplier(TimeStamp):
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255)


class Product(TimeStamp):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    asin = models.CharField(max_length=15, verbose_name='ASIN')
    upc = models.CharField(max_length=15, verbose_name='UPC')
    ein = models.CharField(max_length=15, verbose_name='EIN')
    sku = models.CharField(max_length=15, verbose_name='SKU')
    wholesale_units = models.IntegerField(default=0)
    wholesale_price = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    fees = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    roi = models.DecimalField(max_digits=11, decimal_places=2, default=0, verbose_name='ROI')
    buy_box = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    buy_box_avg90 = models.DecimalField(max_digits=11, decimal_places=2, default=0, verbose_name='Buy Box - 90 Days AVG')
    buy_box_min = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    buy_box_max = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    buy_box_min_date = models.DateField()
    buy_box_max_date = models.DateField()
    review_count = models.IntegerField(default=0, verbose_name='Reviews')
    review_count_last30 = models.IntegerField(default=0, verbose_name='Reviews - Last 30 Days')
    review_count_avg90 = models.IntegerField(default=0, verbose_name='Reviews - 90 Days AVG')
    sales_rank = models.IntegerField(default=0)
    sales_rank_avg90 = models.IntegerField(default=0, verbose_name='Sales Rank - 90 Days AVG')
    fba_sellers_count = models.IntegerField(default=0)
    root_category = models.CharField(max_length=255)
    sales_estimate = models.IntegerField(default=0)
    three_month_supply_cost = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    three_month_supply_amount = models.IntegerField(default=0)

    PENDING, DISCARDED, HIGHLIGHTED, LIKED = range(4)
    STATUS_CHOICES = (
        (PENDING, 'Pending'),  # New product on catalog, pending user review
        (DISCARDED, 'Discarded'),  # Product doesn't sell well or user won't sell it for some reason
        (HIGHLIGHTED, 'Highlighted'),  # good preliminary review but saved for later in-depth analysis
        (LIKED, 'Approved'),  # good prospect
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)


class InventoryUpload(TimeStamp):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='uploads')
    products = models.ManyToManyField(Product, related_name='files')
    file = models.FileField(upload_to='uploads/inventory/%Y/%m/%d')


