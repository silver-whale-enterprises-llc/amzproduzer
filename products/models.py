from django.core.validators import validate_comma_separated_integer_list
from django.db import models


class TimeStamp(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Supplier(TimeStamp):
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return f'<Supplier: {self.id}, {self.name}>'


class Product(TimeStamp):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    asin = models.CharField(max_length=15, verbose_name='ASIN', default='', blank=True)
    upc = models.CharField(max_length=15, verbose_name='UPC', default='', blank=True)
    ein = models.CharField(max_length=15, verbose_name='EIN', default='', blank=True)
    sku = models.CharField(max_length=15, verbose_name='SKU', default='', blank=True)
    name = models.CharField(max_length=255, default='', blank=True)
    wholesale_units = models.IntegerField(default=0, blank=True)
    wholesale_price = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    fees = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    total_cost = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    profit = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    roi = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True, verbose_name='ROI')
    buy_box = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    buy_box_avg90 = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True, verbose_name='Buy Box - 90 Days AVG')
    buy_box_min = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    buy_box_max = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    buy_box_min_date = models.DateField(null=True, blank=True)
    buy_box_max_date = models.DateField(null=True, blank=True)
    review_count = models.IntegerField(default=0, blank=True, verbose_name='Reviews')
    review_count_last30 = models.IntegerField(default=0, blank=True, verbose_name='Reviews - Last 30 Days')
    review_count_avg90 = models.IntegerField(default=0, blank=True, verbose_name='Reviews - 90 Days AVG')
    sales_rank = models.IntegerField(default=0, blank=True)
    sales_rank_avg90 = models.IntegerField(default=0, blank=True, verbose_name='Sales Rank - 90 Days AVG')
    fba_sellers_count = models.IntegerField(default=0, blank=True)
    root_category = models.CharField(max_length=255, default='', blank=True)
    sales_estimate = models.IntegerField(default=0, blank=True)
    three_month_supply_cost = models.DecimalField(max_digits=11, decimal_places=2, default=0, blank=True)
    three_month_supply_amount = models.IntegerField(default=0, blank=True)
    sold_by_amazon = models.BooleanField(default=False)

    PENDING, DISCARDED, HIGHLIGHTED, LIKED, FAILED = range(5)
    STATUS_CHOICES = (
        (PENDING, 'Pending Analysis'),  # New product on catalog, pending user review or system analysis
        (DISCARDED, 'Thumbs Down :('),  # Product doesn't sell well or user won't sell it for some reason
        (HIGHLIGHTED, 'Highlighted'),  # good preliminary review but saved for later in-depth analysis
        (LIKED, 'Thumbs Up :)'),  # good prospect
        (FAILED, 'Analysis Failed'),  # System failed to analyse this product
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)
    failed_analysis_reason = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return f'<Product: {self.id}, {self.asin or "NO_ASIN"}, {self.name}>'


class InventoryUpload(TimeStamp):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='uploads')
    products = models.ManyToManyField(Product, related_name='files')
    file = models.FileField(upload_to='uploads/inventory/%Y/%m/%d')
    price_col = models.CharField(max_length=255, default='Price', verbose_name='Price Column')
    identifier_col = models.CharField(max_length=255, default='UPC', verbose_name='Identifier Column')
    ASIN, UPC, EIN = range(3)
    IDENTIFIER_CHOICES = (
        (ASIN, 'ASIN'),
        (UPC, 'UPC'),
        (EIN, 'EIN'),
    )
    identifier_type = models.IntegerField(choices=IDENTIFIER_CHOICES, default=UPC)

    PENDING, PROCESSING, FINISHED, FINISHED_WITH_ERRORS, FAILED = range(5)
    STATUS_CHOICES = (
        (PENDING, 'Analysis Pending'),
        (PROCESSING, 'Analysis in Process'),
        (FINISHED, 'Analysis Finished'),
        (FINISHED_WITH_ERRORS, 'Analysis Finished With Some Failures'),
        (FAILED, 'Analysis Failed'),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)
    failed_analysis_reason = models.CharField(max_length=255, default='', blank=True)

    total_products = models.IntegerField(default=0, blank=True)
    processed_products = models.IntegerField(default=0, blank=True)
    analysed_products = models.IntegerField(default=0, blank=True)
    failed_products = models.IntegerField(default=0, blank=True)
    email_on_completion = models.BooleanField(default=True, blank=True)

    def identifier_field(self):
        if self.identifier_type == InventoryUpload.ASIN:
            return 'asin'

        elif self.identifier_type == InventoryUpload.UPC:
            return 'upc'

        elif self.identifier_type == InventoryUpload.EIN:
            return 'ein'

        return ''

    def __str__(self):
        return f'<InventoryUpload: {self.id}, {self.file.name}, {self.STATUS_CHOICES[self.status]}>'


class AmazonCategorySalesRank(models.Model):
    name = models.CharField(max_length=255, default='')
    max_allowed = models.IntegerField(null=False, blank=False, default=200000)
    preferred = models.IntegerField(null=False, blank=False, default=100000)

    def __str__(self):
        return f'<AmazonCategorySalesRank: {self.id}, {self.name}, {self.preferred}>'


class AmazonCategory(TimeStamp):
    sales_rank = models.ForeignKey(AmazonCategorySalesRank, on_delete=models.CASCADE,
                                   null=False, blank=False, related_name='amazon_ids')
    name = models.CharField(max_length=255, default='')
    category_id = models.BigIntegerField(null=False, blank=False)
    products_count = models.IntegerField(default=0)
    highest_rank = models.IntegerField(default=0)

    def __str__(self):
        return f'<AmazonCategory: {self.id}, {self.name}, {self.products_count}>'


