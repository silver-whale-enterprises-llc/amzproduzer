# Generated by Django 2.1.7 on 2019-03-16 14:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AmazonCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(default='', max_length=255)),
                ('category_id', models.BigIntegerField()),
                ('products_count', models.IntegerField(default=0)),
                ('highest_rank', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AmazonProductListing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('asin', models.CharField(max_length=15, verbose_name='ASIN')),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('fees', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('total_cost', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('profit', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('profit_median', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('profit_avg', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('roi', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=3, verbose_name='ROI')),
                ('buy_box', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('buy_box_median', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('buy_box_std_dev', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('buy_box_variance', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('buy_box_avg90', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11, verbose_name='Buy Box - 90 Days AVG')),
                ('buy_box_min', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('buy_box_max', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('buy_box_min_date', models.DateField(blank=True, null=True)),
                ('buy_box_max_date', models.DateField(blank=True, null=True)),
                ('review_count', models.IntegerField(blank=True, default=0, verbose_name='Reviews')),
                ('review_count_last30', models.IntegerField(blank=True, default=0, verbose_name='Reviews - Last 30 Days')),
                ('review_count_avg90', models.IntegerField(blank=True, default=0, verbose_name='Reviews - 90 Days AVG')),
                ('sales_rank', models.IntegerField(blank=True, default=0)),
                ('sales_rank_median', models.IntegerField(blank=True, default=0)),
                ('sales_rank_avg90', models.IntegerField(blank=True, default=0, verbose_name='Sales Rank - 90 Days AVG')),
                ('sales_rank_std_dev', models.IntegerField(blank=True, default=0)),
                ('sales_rank_std_variance', models.IntegerField(blank=True, default=0)),
                ('fba_sellers_count', models.IntegerField(blank=True, default=0)),
                ('sales_estimate_current', models.IntegerField(blank=True, default=0, verbose_name='Sales /mo.')),
                ('sales_estimate_avg', models.IntegerField(blank=True, default=0)),
                ('three_month_supply_cost', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('three_month_supply_amount', models.IntegerField(blank=True, default=0)),
                ('sold_by_amazon', models.BooleanField(default=False)),
                ('isAddOn', models.BooleanField(default=False)),
                ('rating_current', models.IntegerField(blank=True, default=0)),
                ('pack_units', models.IntegerField(blank=True, default=1)),
                ('status', models.IntegerField(choices=[(0, 'Thumbs Down :('), (1, 'Highlighted'), (2, 'Recommended'), (3, 'Thumbs Up :)')], default=1)),
                ('discard_reason', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InventoryUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(upload_to='uploads/inventory/%Y/%m/%d')),
                ('price_col', models.CharField(default='Price', max_length=255, verbose_name='Price Column')),
                ('identifier_col', models.CharField(default='UPC', max_length=255, verbose_name='Identifier Column')),
                ('identifier_type', models.IntegerField(choices=[(0, 'ASIN'), (1, 'UPC'), (2, 'EIN')], default=1)),
                ('status', models.IntegerField(choices=[(0, 'Analysis Pending'), (1, 'Analysis in Process'), (2, 'Analysis Finished'), (3, 'Analysis Finished With Some Failures'), (4, 'Analysis Failed')], default=0)),
                ('failed_analysis_reason', models.CharField(blank=True, default='', max_length=255)),
                ('total_products', models.IntegerField(blank=True, default=0)),
                ('processed_products', models.IntegerField(blank=True, default=0)),
                ('analysed_products', models.IntegerField(blank=True, default=0)),
                ('failed_products', models.IntegerField(blank=True, default=0)),
                ('email_on_completion', models.BooleanField(blank=True, default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('asin', models.CharField(max_length=15, verbose_name='ASIN')),
                ('upc', models.CharField(blank=True, default='', max_length=15, verbose_name='UPC')),
                ('ein', models.CharField(blank=True, default='', max_length=15, verbose_name='EIN')),
                ('sku', models.CharField(blank=True, default='', max_length=15, verbose_name='SKU')),
                ('name', models.CharField(blank=True, default='', max_length=255)),
                ('unit_price', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('set_price', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=11)),
                ('status', models.IntegerField(choices=[(0, 'Pending Analysis'), (1, 'Analysis Successful'), (2, 'Analysis Failed')], default=0)),
                ('failed_analysis_reason', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('website', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.Supplier'),
        ),
        migrations.AddField(
            model_name='inventoryupload',
            name='products',
            field=models.ManyToManyField(related_name='files', to='products.Product'),
        ),
        migrations.AddField(
            model_name='inventoryupload',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to='products.Supplier'),
        ),
        migrations.AddField(
            model_name='amazonproductlisting',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amazon_listings', to='products.Product'),
        ),
        migrations.AddField(
            model_name='amazonproductlisting',
            name='root_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='listings', to='products.AmazonCategory'),
        ),
    ]
